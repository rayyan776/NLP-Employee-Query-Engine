import { useEffect, useState } from "react";

export default function QueryPanel() {
  const [q, setQ] = useState("");
  const [metrics, setMetrics] = useState(null);
  const [suggest, setSuggest] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const handler = (e) => {
      const sch = e.detail;
      const tokens = [];
      (sch?.tables || []).forEach((t) => {
        tokens.push(t.name);
        (t.columns || []).forEach((c) => tokens.push(c.name));
      });
      setSuggest((prev) => Array.from(new Set([...(prev || []), ...tokens])).slice(0, 300));
    };
    const aliasHandler = (e) => {
      const vocab = e.detail || [];
      setSuggest((prev) => Array.from(new Set([...(prev || []), ...vocab])).slice(0, 400));
    };
    window.addEventListener("schema", handler);
    window.addEventListener("alias_vocab", aliasHandler);
    return () => {
      window.removeEventListener("schema", handler);
      window.removeEventListener("alias_vocab", aliasHandler);
    };
  }, []);

  const loadHistory = async () => {
    try {
      const r = await fetch("/api/query/history");
      const data = await r.json();
      setHistory(data.history || []);
    } catch (e) {
      // Silently fail
    }
  };
  
  useEffect(() => { loadHistory(); }, []);

  const run = async (text) => {
    setError("");
    const queryText = typeof text === "string" ? text : q;
    if (!queryText.trim()) return;
    setLoading(true);
    try {
      const r = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: queryText, limit: 50, offset: 0 }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Query failed");
      setMetrics(data.performance_metrics || {});
      window.dispatchEvent(new CustomEvent("results", { detail: data }));
      window.dispatchEvent(new CustomEvent("toast", { detail: { title: "Query", body: "Query executed successfully", type: "success" } }));
      await loadHistory();
    } catch (e) {
      setError(e.message || "Query failed");
      window.dispatchEvent(new CustomEvent("toast", { detail: { title: "Query", body: e.message || "Failed", type: "danger" } }));
    } finally { 
      setLoading(false); 
    }
  };

  return (
    <div className="card card-elev">
      <div className="card-header bg-body-tertiary">
        <span className="section-title d-flex align-items-center gap-2">
          <i className="bi bi-search text-primary"></i>
          Run Query
        </span>
      </div>
      <div className="card-body">
        <div className="mb-3">
          <label className="form-label small text-muted">Enter your natural language query</label>
          <div className="input-group">
            <span className="input-group-text"><i className="bi bi-search"></i></span>
            <input
              className="form-control"
              list="hints"
              placeholder="e.g., Average salary by department"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && run()}
            />
            <datalist id="hints">
              {suggest.map((s, i) => (<option key={i} value={s} />))}
            </datalist>
          </div>
        </div>
        
        {history.length > 0 && (
          <div className="mb-3">
            <label className="form-label small text-muted">Or select from history</label>
            <select className="form-select" onChange={(e) => { if(e.target.value) { setQ(e.target.value); e.target.value = ""; } }}>
              <option value="">Recent queries...</option>
              {history.map((h, i) => (<option key={i} value={h.query}>{h.query}</option>))}
            </select>
          </div>
        )}

        <button className="btn btn-success w-100" onClick={() => run()} disabled={loading}>
          {loading ? (
            <>
              <span className="spinner-border spinner-border-sm me-2" role="status"></span>
              Running Query...
            </>
          ) : (
            <>
              <i className="bi bi-play-fill me-1"></i>
              Execute Query
            </>
          )}
        </button>
        
        {error && <div className="alert alert-danger mt-3 py-2 mb-0 small">{error}</div>}
        
        {metrics && (
          <details className="mt-3">
            <summary className="small text-muted fw-semibold" style={{ cursor: 'pointer' }}>
              <i className="bi bi-speedometer2 me-1"></i>
              Performance Metrics
            </summary>
            <pre className="small mt-2 p-2 code-block-light rounded" style={{ maxHeight: 200, overflow: 'auto' }}>
              {JSON.stringify(metrics, null, 2)}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
}
