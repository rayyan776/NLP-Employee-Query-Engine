import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from api.routes import schema_routes, ingestion, query
from logger import logger

app = FastAPI(title="NLP Employee Query Engine", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(schema_routes.router, prefix="/api")
app.include_router(ingestion.router, prefix="/api")
app.include_router(query.router, prefix="/api")
