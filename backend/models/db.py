import os
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

DATABASE_URL = os.getenv("DATABASE_URL", "")
POOL_SIZE = int(os.getenv("POOL_SIZE", "10"))

_engine = None

def engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=POOL_SIZE,
            max_overflow=5,
            pool_pre_ping=True,
            future=True,
        )
    return _engine
