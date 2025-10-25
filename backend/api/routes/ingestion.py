from fastapi import APIRouter, UploadFile, BackgroundTasks, HTTPException, File, Query
from typing import List
from uuid import uuid4
from services.document_processor import DocumentProcessor, IngestionJobs
from services.schema_discovery import SchemaCache, SchemaDiscovery
from logger import logger
from redis import Redis
import os

router = APIRouter()
processor = DocumentProcessor(
    model_name=os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
    batch_size=int(os.getenv("BATCH_SIZE", "32")),
)

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
        pass

@router.post("/ingest/database")
def ingest_database(connection_string: str | None = None):
    """
    Connect to database and discover schema; persist in SchemaCache.
    """
    try:
        conn = connection_string or os.getenv("DATABASE_URL")
        if not conn:
            raise ValueError("connection_string required")
        schema = SchemaDiscovery().analyze_database(conn)  # type: ignore
        SchemaCache.set(schema)
        _bump_cache_version()
        logger.info(f"[ingest_database] tables={len(schema.get('tables', []))} rels={len(schema.get('relationships', []))}")
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ingest/documents")
async def ingest_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="Multiple files"),
):
    """
    Upload and process documents asynchronously; returns job_id.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    job_id = str(uuid4())
    IngestionJobs.init(job_id, total=len(files))

    # Enforce type/size limits; read into memory for background processing
    allowed = {
        "application/pdf",
        "text/plain",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/csv",
    }
    max_mb = int(os.getenv("DOC_MAX_MB", "10"))
    blobs = []
    for f in files:
        if f.content_type not in allowed:
            IngestionJobs.error(job_id, f"{f.filename}: unsupported type {f.content_type}")
            continue
        raw = await f.read()
        mb = len(raw) / (1024 * 1024)
        if mb > max_mb:
            IngestionJobs.error(job_id, f"{f.filename}: exceeds {max_mb}MB")
            continue
        # sanitize filename (basic)
        safe_name = f.filename.replace("..", "").replace("/", "_").replace("\\", "_")[:180]
        blobs.append({"filename": safe_name, "bytes": raw})

    def _work():
        processor.process_uploads_bytes(blobs, job_id)
        _bump_cache_version()
        logger.info(f"[ingest_documents] completed job_id={job_id} total={IngestionJobs.get(job_id).get('total')}")

    background_tasks.add_task(_work)
    return {"job_id": job_id}

@router.get("/ingest/status")
def ingest_status(job_id: str = Query(...)):
    """
    Return ingestion progress (done/total/errors and per-file statuses if available).
    """
    st = IngestionJobs.get(job_id)
    if not st:
        return {"error": "unknown job", "job_id": job_id}
    return st
