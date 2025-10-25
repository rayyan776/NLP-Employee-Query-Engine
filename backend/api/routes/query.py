from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from time import perf_counter
from services.query_engine import QueryEngine, QueryHistory

router = APIRouter()
_engine = None

def engine():
    global _engine
    if _engine is None:
        _engine = QueryEngine()
    return _engine

class QueryIn(BaseModel):
    query: str
    limit: int = 50
    offset: int = 0

@router.post("/query")
def query(inp: QueryIn):
    t0 = perf_counter()
    try:
        out = engine().process_query(inp.query, limit=inp.limit, offset=inp.offset)
        out.setdefault("performance_metrics", {})
        out["performance_metrics"]["response_time_ms"] = int((perf_counter() - t0) * 1000)
        out["performance_metrics"].setdefault("cache_hit", False)
        QueryHistory.append(inp.query, out["performance_metrics"])
        return out
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/query/history")
def history():
    return {"history": QueryHistory.tail(50)}
