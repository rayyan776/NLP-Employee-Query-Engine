import os
import hashlib
from typing import Dict, Any, List

import orjson
from redis import Redis
from sqlalchemy import text
from sentence_transformers import SentenceTransformer

from models.db import engine as get_engine
from services.schema_discovery import SchemaDiscovery, SchemaCache
from services.document_processor import VectorStore
from services.query_parser import QueryParser
from services.sql_builder import SQLBuilder


class QueryHistory:
    _items: List[Dict[str, Any]] = []
    
    @classmethod
    def append(cls, query: str, metrics: Dict[str, Any]) -> None:
        cls._items.append({"query": query, "metrics": metrics})
    
    @classmethod
    def tail(cls, n: int = 50) -> List[Dict[str, Any]]:
        return cls._items[-n:]


class QueryEngine:
    def __init__(self):
        self.conn_str = os.getenv("DATABASE_URL")
        if not self.conn_str:
            raise RuntimeError("DATABASE_URL not set")

        self.redis = Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True,
        )
        self.cache_ttl = int(os.getenv("REDIS_TTL", "300"))

        self.embed_model_name = os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self._embedder: SentenceTransformer | None = None

        self.eng = get_engine()
        self.discovery = SchemaDiscovery()
        
        # Initialize semantic parser and SQL builder
        self.parser = QueryParser()
        self.sql_builder = SQLBuilder()
        
        if not SchemaCache.get():
            SchemaCache.set(self.discovery.analyze_database(self.conn_str))

    # Cache keys
    def _cache_version(self) -> str:
        try:
            return self.redis.get("cache_version") or "0"
        except Exception:
            return "0"

    def _cache_key(self, q: str, limit: int, offset: int) -> str:
        ver = self._cache_version()
        return "q:" + hashlib.sha256(f"{ver}|{q}|{limit}|{offset}".encode()).hexdigest()

    # Public API
    def process_query(self, user_query: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        schema = SchemaCache.get() or self.discovery.analyze_database(self.conn_str)

        # Check cache
        ckey = self._cache_key(user_query, limit, offset)
        cached = None
        try:
            cached = self.redis.get(ckey)
        except Exception:
            cached = None
        
        if cached:
            try:
                out = orjson.loads(cached.encode())
            except Exception:
                out = {"query_type": "cached", "results": {}, "performance_metrics": {}}
            out.setdefault("performance_metrics", {})
            out["performance_metrics"]["cache_hit"] = True
            return out

        # Classify query
        qtype = self._classify(user_query)

        results: Dict[str, Any] = {}
        
        # Execute SQL queries using semantic parser
        if qtype in ("sql", "hybrid"):
            results["table"] = self._run_sql_semantic(user_query, schema, limit, offset)
        
        # Execute document search
        if qtype in ("documents", "hybrid"):
            results["documents"] = self._search_documents(user_query, top_k=3)

        out = {"query_type": qtype, "results": results, "performance_metrics": {"cache_hit": False}}

        # Cache result
        try:
            self.redis.setex(ckey, self.cache_ttl, orjson.dumps(out).decode())
        except Exception:
            pass

        return out

    # Classify query type
    def _classify(self, q: str) -> str:
        ql = q.lower()
        is_doc = any(k in ql for k in ["resume", "cv", "document", "review", "pdf"])
        is_sql = any(k in ql for k in [
            "count", "list", "average", "avg", "sum", "top", "hired", "joined", "trend", "month",
            "salary", "department", "dept", "division", "divisions", "manager", "reports to",
            "before", "after", "location", "mumbai", "bangalore", "chennai", "delhi", "hyderabad",
            "pay", "compensation", "how many", "show", "employees", "staff"
        ])
        if is_doc and is_sql:
            return "hybrid"
        return "documents" if is_doc else "sql"

    # NEW: Semantic SQL generation with CRITICAL FIX
    def _run_sql_semantic(self, query: str, schema: dict, limit: int, offset: int) -> List[dict]:
        """
        Generate and execute SQL using semantic parser
        NO hardcoded patterns
        """
        # Parse query into intent
        intent = self.parser.parse_intent(query, schema)
        
        # Build SQL from intent
        sql, params = self.sql_builder.build_sql(intent, schema)
        
        # CRITICAL FIX: Only add pagination if SQL doesn't already have LIMIT
        if ' LIMIT ' not in sql.upper():
            sql = self._paginate(sql, intent.get('limit') or limit, offset)
        
        # Execute
        return self._exec(sql, params)

    def _exec(self, sql: str, params: Dict[str, Any]) -> List[dict]:
        """
        Execute SQL with parameters
        """
        with self.eng.connect() as conn:
            rows = conn.execute(text(sql), params).mappings().all()
        return [dict(r) for r in rows]

    def _paginate(self, sql: str, limit: int, offset: int) -> str:
        """
        Add LIMIT and OFFSET to SQL
        """
        l = max(1, min(int(limit), 200))
        o = max(0, int(offset))
        return f"{sql} LIMIT {l} OFFSET {o}"

    # Embeddings
    def _ensure_embedder(self) -> SentenceTransformer:
        if self._embedder is None:
            self._embedder = SentenceTransformer(self.embed_model_name)
        return self._embedder

    def _search_documents(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        embedder = self._ensure_embedder()
        qvec = embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype("float32")
        D, I = VectorStore.index.search(qvec, top_k)
        hits: List[Dict[str, Any]] = []
        for idx, score in zip(I[0], D[0]):
            if idx == -1:
                continue
            meta = VectorStore.meta[idx] if idx < len(VectorStore.meta) else {}
            hits.append({"score": float(score), "meta": meta})
        return hits
