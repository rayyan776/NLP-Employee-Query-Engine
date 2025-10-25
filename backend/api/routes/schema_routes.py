from fastapi import APIRouter, HTTPException
from services.schema_discovery import SchemaDiscovery, SchemaCache
from logger import logger
from redis import Redis
import os

router = APIRouter()
discovery = SchemaDiscovery()

def _redis():
    return Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        decode_responses=True,
    )

def _bump_cache_version():
    try:
        _redis().incr("cache_version")
    except Exception:
        # Redis may be down in dev; do not fail schema ingest
        pass

@router.post("/ingest/database")
def ingest_database(connection_string: str | None = None):
    """
    Connect to DB and discover schema; persists in SchemaCache and bumps cache_version.
    Body (JSON): { "connection_string": "postgresql://user:pass@host:5432/db" }
    """
    try:
        conn = connection_string or os.getenv("DATABASE_URL")
        if not conn:
            raise ValueError("connection_string required")
        schema = discovery.analyze_database(conn)  # type: ignore
        SchemaCache.set(schema)
        _bump_cache_version()
        logger.info(f"[ingest_database] tables={len(schema.get('tables', []))} rels={len(schema.get('relationships', []))}")
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/schema")
def get_schema():
    """
    Return the last discovered schema from cache for UI visualization.
    """
    return {"schema": SchemaCache.get() or {}}
