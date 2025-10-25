import io, csv
from typing import List, Dict, Any
from fastapi import UploadFile
from sentence_transformers import SentenceTransformer
import faiss, numpy as np

try:
    from unstructured.partition.pdf import partition_pdf
except Exception:
    partition_pdf = None
try:
    from unstructured.partition.docx import partition_docx
except Exception:
    partition_docx = None

class IngestionJobs:
    _jobs: Dict[str, Dict[str, Any]] = {}
    @classmethod
    def init(cls, job_id: str, total: int):
        cls._jobs[job_id] = {"total": total, "done": 0, "errors": [], "files": []}
    @classmethod
    def inc(cls, job_id: str, fname: str):
        cls._jobs[job_id]["done"] += 1
        cls._jobs[job_id]["files"].append({"file": fname, "status": "processed"})
    @classmethod
    def error(cls, job_id: str, msg: str):
        cls._jobs[job_id]["errors"].append(msg)
    @classmethod
    def get(cls, job_id: str):
        return cls._jobs.get(job_id)

class VectorStore:
    index = faiss.IndexFlatIP(384)  # all-MiniLM-L6-v2
    meta: List[Dict[str, Any]] = []

class DocumentProcessor:
    def __init__(self, model_name: str, batch_size: int = 32):
        self.model = SentenceTransformer(model_name)
        self.batch = batch_size

    async def process_uploads_async(self, files: List[UploadFile], job_id: str):
        blobs = []
        for f in files:
            raw = await f.read()
            blobs.append({"filename": f.filename, "bytes": raw})
        self.process_uploads_bytes(blobs, job_id)

    def process_uploads_bytes(self, blobs: List[Dict[str, Any]], job_id: str):
        texts, metas = [], []
        for blob in blobs:
            try:
                detected, chunks = self._extract_and_chunk(blob["filename"], blob["bytes"])
                for ch in chunks:
                    texts.append(ch)
                    metas.append({
                        "filename": blob["filename"],
                        "type": detected,
                        "snippet": ch[:300]
                    })
                IngestionJobs.inc(job_id, blob["filename"])
            except Exception as e:
                IngestionJobs.error(job_id, f'{blob.get("filename")}: {e}')
        if texts:
            vecs = self.model.encode(texts, batch_size=self.batch, convert_to_numpy=True, normalize_embeddings=True)
            VectorStore.index.add(vecs.astype(np.float32))
            VectorStore.meta.extend(metas)

    def _extract_and_chunk(self, filename: str, raw: bytes):
        name = filename.lower()
        if name.endswith(".pdf") and partition_pdf:
            elements = partition_pdf(file=io.BytesIO(raw))
            txt = "\n".join([getattr(el, "text", "") for el in elements if getattr(el, "text", "")])
            return "pdf", self.dynamic_chunking(txt, "pdf")
        if name.endswith(".docx") and partition_docx:
            elements = partition_docx(file=io.BytesIO(raw))
            txt = "\n".join([getattr(el, "text", "") for el in elements if getattr(el, "text", "")])
            return "docx", self.dynamic_chunking(txt, "docx")
        if name.endswith(".csv"):
            txt = raw.decode(errors="ignore")
            txt = "\n".join([", ".join(r) for r in csv.reader(io.StringIO(txt))])
            return "csv", self.dynamic_chunking(txt, "csv")
        txt = raw.decode(errors="ignore")
        return "txt", self.dynamic_chunking(txt, "txt")

    def dynamic_chunking(self, content: str, doc_type: str) -> list[str]:
        headers = ["skills", "experience", "projects", "education", "summary", "review", "scope", "clause"]
        lines = [ln.strip() for ln in content.splitlines()]
        max_len = 1400 if doc_type in ("pdf", "docx", "txt") else 1600
        parts, buf = [], []
        for ln in lines:
            if any(h in ln.lower() for h in headers) and buf:
                parts.append("\n".join(buf).strip())
                buf = [ln]
            else:
                if len("\n".join(buf)) + len(ln) + 1 > max_len:
                    parts.append("\n".join(buf).strip())
                    buf = [ln]
                else:
                    buf.append(ln)
        if buf:
            parts.append("\n".join(buf).strip())
        return [p for p in parts if p]
