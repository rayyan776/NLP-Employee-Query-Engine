import { useState, useMemo } from "react";

export default function DatabaseConnector() {
  const [conn, setConn] = useState("");
  const [schema, setSchema] = useState(null);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  const connect = async () => {
    setMsg("Connecting…");
    setLoading(true);
    try {
      const r = await fetch("/api/ingest/database", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ connection_string: conn }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Failed to connect");
      setSchema(data.schema);
      setMsg("Connected & analyzed.");
      window.dispatchEvent(new CustomEvent("schema", { detail: data.schema }));
      window.dispatchEvent(new CustomEvent("alias_vocab", { detail: data.schema?.alias_vocab || [] }));
      window.dispatchEvent(new CustomEvent("toast", { detail: { title: "Database", body: "Schema discovery complete", type: "success" } }));
    } catch (e) {
      setMsg(e.message || "Error");
      window.dispatchEvent(new CustomEvent("toast", { detail: { title: "Database", body: e.message || "Connect failed", type: "danger" } }));
    } finally {
      setLoading(false);
    }
  };

  const SchemaTree = useMemo(() => {
    const s = schema;
    if (!s) return () => null;
    const rels = s.relationships || [];
    const relByTable = {};
    rels.forEach((r) => {
      relByTable[r.from_table] = relByTable[r.from_table] || [];
      relByTable[r.from_table].push(r);
    });
    return function Tree() {
      return (
        <div style={{ maxHeight: 240, overflow: "auto" }} className="mt-3">
          <ul className="small mb-0">
            {(s.tables || []).map((t) => (
              <li key={t.name}>
                <details>
                  <summary className="fw-semibold">{t.name} <span className="chip bg-secondary-subtle text-secondary-emphasis">{(t.columns || []).length} cols</span></summary>
                  <ul className="mt-1">
                    {(t.columns || []).map((c) => (
                      <li key={t.name + c.name} className="muted">{c.name} — {c.type}</li>
                    ))}
                  </ul>
                  {relByTable[t.name] && (
                    <div className="mt-1">
                      <em className="muted">Relations</em>
                      <ul>
                        {relByTable[t.name].map((r, i) => (
                          <li key={t.name + "_rel_" + i} className="muted">
                            {r.from_table} [{(r.from_columns || []).join(", ")}] → {r.to_table} [{(r.to_columns || []).join(", ")}]
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </details>
              </li>
            ))}
          </ul>
        </div>
      );
    };
  }, [schema]);

  return (
    <div className="card card-elev">
      <div className="card-header bg-body-tertiary">
        <span className="section-title d-flex align-items-center gap-2">
          <i className="bi bi-database-check text-primary"></i>
          Connect Database
        </span>
      </div>
      <div className="card-body">
        <div className="mb-3">
          <label className="form-label small text-muted">Database Connection String</label>
          <div className="input-group">
            <span className="input-group-text"><i className="bi bi-link-45deg"></i></span>
            <input
              className="form-control"
              placeholder="postgresql://user:pass@localhost:5432/employees_db"
              value={conn}
              onChange={(e) => setConn(e.target.value)}
            />
          </div>
        </div>
        
        <button className="btn btn-brand w-100 d-flex align-items-center justify-content-center gap-2" onClick={connect} disabled={loading}>
          {loading ? (
            <>
              <span className="spinner-border spinner-border-sm" role="status"></span>
              Connecting...
            </>
          ) : (
            <>
              <i className="bi bi-lightning-charge-fill"></i>
              Connect & Analyze
            </>
          )}
        </button>
        
        {msg && <div className="small mt-2 text-muted">{msg}</div>}
        
        {schema && (
          <>
            <div className="mt-3">
              <span className="badge bg-success-subtle text-success-emphasis">
                <i className="bi bi-check-circle me-1"></i>
                Schema Loaded
              </span>
            </div>
            <SchemaTree />
          </>
        )}
      </div>
    </div>
  );
}
