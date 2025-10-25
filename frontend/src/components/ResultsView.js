import { useEffect, useMemo, useState } from "react";

export default function ResultsView() {
  const [payload, setPayload] = useState(null);
  const [page, setPage] = useState(1);
  const pageSize = 10;

  useEffect(() => {
    const h = (e) => { setPayload(e.detail); setPage(1); };
    window.addEventListener("results", h);
    return () => window.removeEventListener("results", h);
  }, []);

  const rows = payload?.results?.table || [];
  const docs = payload?.results?.documents || [];

  const pageRows = useMemo(() => {
    const start = (page - 1) * pageSize;
    return rows.slice(start, start + pageSize);
  }, [rows, page]);

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(rows, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    triggerDownload(url, "results.json");
  };

  const exportCSV = () => {
    if (!rows.length) return;
    const headers = Object.keys(rows[0]);
    const csv = [headers.join(",")].concat(rows.map((r) => headers.map((h) => stringifyCSV(r[h])).join(","))).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    triggerDownload(url, "results.csv");
  };

  const stringifyCSV = (v) => {
    if (v === null || v === undefined) return "";
    const s = String(v);
    if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
    return s;
  };

  const triggerDownload = (url, name) => {
    const a = document.createElement("a"); a.href = url; a.download = name; a.click(); URL.revokeObjectURL(url);
  };

  return (
    <div className="card card-elev">
      <div className="card-header bg-body-tertiary d-flex align-items-center justify-content-between">
        <span className="section-title d-flex align-items-center gap-2">
          <i className="bi bi-table text-primary"></i>
          Query Results
        </span>
        {rows.length > 0 && (
          <div className="d-flex gap-2">
            <button className="btn btn-outline-primary btn-sm" onClick={exportCSV}>
              <i className="bi bi-filetype-csv me-1"></i>CSV
            </button>
            <button className="btn btn-outline-secondary btn-sm" onClick={exportJSON}>
              <i className="bi bi-braces-asterisk me-1"></i>JSON
            </button>
          </div>
        )}
      </div>

      <div className="card-body">
        {rows.length > 0 && (
          <>
            <div className="table-responsive">
              <table className="table table-sm table-hover table-striped align-middle mb-0">
                <thead className="table-light">
                  <tr>{Object.keys(rows[0]).map((k) => (<th key={k} className="fw-semibold">{k}</th>))}</tr>
                </thead>
                <tbody>
                  {pageRows.map((r, i) => (
                    <tr key={i}>{Object.keys(rows[0]).map((k) => (<td key={k + i}>{String(r[k])}</td>))}</tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="d-flex justify-content-between align-items-center mt-3 pt-3 border-top">
              <div className="small text-muted">
                Showing {Math.min((page - 1) * pageSize + 1, rows.length)}-{Math.min(page * pageSize, rows.length)} of {rows.length} results
              </div>
              <div className="btn-group btn-group-sm">
                <button className="btn btn-outline-secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                  <i className="bi bi-chevron-left"></i> Prev
                </button>
                <button className="btn btn-outline-secondary" disabled={page * pageSize >= rows.length} onClick={() => setPage((p) => p + 1)}>
                  Next <i className="bi bi-chevron-right"></i>
                </button>
              </div>
            </div>
          </>
        )}

        {docs.length > 0 && (
          <>
            <div className="mt-4 mb-2">
              <span className="badge bg-primary-subtle text-primary-emphasis">
                <i className="bi bi-file-text me-1"></i>
                Related Documents ({docs.length})
              </span>
            </div>
            <div className="row g-3">
              {docs.map((d, i) => (
                <div className="col-md-6" key={i}>
                  <div className="card h-100">
                    <div className="card-body">
                      <div className="d-flex justify-content-between align-items-start mb-2">
                        <h6 className="card-subtitle text-muted mb-0">
                          <i className="bi bi-file-earmark-text me-1"></i>
                          {d.meta?.filename || "Document"}
                        </h6>
                        <span className="badge bg-success-subtle text-success-emphasis">
                          {d.score?.toFixed(3)}
                        </span>
                      </div>
                      <pre className="small mb-0 text-muted" style={{ maxHeight: 160, overflow: "auto", whiteSpace: 'pre-wrap' }}>
                        {d.meta?.snippet || JSON.stringify(d.meta, null, 2)}
                      </pre>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {rows.length === 0 && docs.length === 0 && (
          <div className="text-center text-muted py-5">
            <i className="bi bi-inbox fs-1 d-block mb-2 opacity-25"></i>
            <div>No results yet. Run a query to see results here.</div>
          </div>
        )}
      </div>
    </div>
  );
}
