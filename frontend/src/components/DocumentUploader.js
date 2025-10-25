import { useState, useCallback, useEffect } from "react";

export default function DocumentUploader() {
  const [files, setFiles] = useState([]);
  const [job, setJob] = useState(null);
  const [status, setStatus] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [completed, setCompleted] = useState(false);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = Array.from(e.dataTransfer.files || []);
    if (dropped.length) setFiles(dropped);
  }, []);

  const onDragOver = (e) => { e.preventDefault(); setDragOver(true); };
  const onDragLeave = (e) => { e.preventDefault(); setDragOver(false); };

  const upload = async () => {
    setError("");
    setCompleted(false);
    if (!files.length) return;
    setUploading(true);
    const fd = new FormData();
    for (const f of files) fd.append("files", f);
    try {
      const r = await fetch("/api/ingest/documents", { method: "POST", body: fd });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Upload failed");
      setJob(data.job_id);
      poll(data.job_id);
      window.dispatchEvent(new CustomEvent("toast", { detail: { title: "Upload", body: "Ingestion started", type: "success" } }));
    } catch (e) {
      setError(e.message || "Upload failed");
      setUploading(false);
      window.dispatchEvent(new CustomEvent("toast", { detail: { title: "Upload", body: e.message || "Failed", type: "danger" } }));
    }
  };

  const poll = async (jid) => {
    const t = setInterval(async () => {
      try {
        const r = await fetch(`/api/ingest/status?job_id=${jid}`);
        const s = await r.json();
        setStatus(s);
        if (s.done && s.total && s.done >= s.total) {
          clearInterval(t);
          setUploading(false);
          setCompleted(true);
          window.dispatchEvent(new CustomEvent("toast", { detail: { title: "Upload", body: "Documents indexed successfully", type: "success" } }));
          window.dispatchEvent(new CustomEvent("docs_complete"));
        }
      } catch (e) {
        clearInterval(t);
        setUploading(false);
        setError("Status check failed");
      }
    }, 800);
  };

  useEffect(() => {
    const prevent = (e) => { e.preventDefault(); e.stopPropagation(); };
    window.addEventListener("dragover", prevent);
    window.addEventListener("drop", prevent);
    return () => {
      window.removeEventListener("dragover", prevent);
      window.removeEventListener("drop", prevent);
    };
  }, []);

  const pct = status?.total ? Math.round((status.done / status.total) * 100) : 0;

  return (
    <div className="card card-elev">
      <div className="card-header bg-body-tertiary">
        <span className="section-title d-flex align-items-center gap-2">
          <i className="bi bi-file-earmark-arrow-up text-primary"></i>
          Upload Documents
        </span>
      </div>
      <div className="card-body">
        <div
          className={`soft rounded p-4 text-center ${dragOver ? "hover" : ""}`}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          style={{ cursor: "copy" }}
        >
          <i className="bi bi-cloud-arrow-up fs-3 text-primary d-block mb-2"></i>
          <div className="muted">Drag & drop files here or choose below</div>
        </div>
        
        <div className="mt-3">
          <label className="form-label small text-muted">Select Files</label>
          <div className="input-group">
            <span className="input-group-text"><i className="bi bi-paperclip"></i></span>
            <input type="file" multiple className="form-control" onChange={(e) => setFiles([...e.target.files])} />
          </div>
        </div>

        {files.length > 0 && (
          <div className="mt-2">
            <span className="badge bg-info-subtle text-info-emphasis">
              {files.length} file(s) ready
            </span>
          </div>
        )}

        <button 
          className="btn btn-brand w-100 mt-3 d-flex align-items-center justify-content-center gap-2" 
          onClick={upload}
          disabled={uploading || files.length === 0}
        >
          {uploading ? (
            <>
              <span className="spinner-border spinner-border-sm" role="status"></span>
              Uploading...
            </>
          ) : (
            <>
              <i className="bi bi-upload"></i>
              Upload & Process
            </>
          )}
        </button>

        {/* Fixed height container for upload status */}
        {(job || status || error) && (
          <div className="upload-status-container">
            {job && <div className="small mt-3 text-muted">Job ID: <code>{job}</code></div>}

            {status && (
              <div className="mt-3">
                <div className="d-flex justify-content-between align-items-center mb-1">
                  <span className="small text-muted">
                    {completed ? (
                      <span className="text-success fw-semibold">
                        <i className="bi bi-check-circle-fill me-1"></i>
                        Completed Successfully!
                      </span>
                    ) : (
                      "Processing..."
                    )}
                  </span>
                  <span className="small fw-semibold">{pct}%</span>
                </div>
                <div className="progress" role="progressbar" aria-valuenow={pct} aria-valuemin="0" aria-valuemax="100">
                  <div className={`progress-bar ${completed ? 'bg-success' : ''}`} style={{ width: `${pct}%` }}></div>
                </div>
                <details className="mt-2">
                  <summary className="small text-muted" style={{ cursor: 'pointer' }}>View Details</summary>
                  <pre className="small mt-2 p-2 code-block-light rounded" style={{ maxHeight: 200, overflow: 'auto' }}>
                    {JSON.stringify(status, null, 2)}
                  </pre>
                </details>
              </div>
            )}

            {error && <div className="alert alert-danger mt-3 py-2 mb-0 small">{error}</div>}
          </div>
        )}
      </div>
    </div>
  );
}
