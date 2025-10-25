import { useEffect, useState } from "react";

export default function MetricsDashboard() {
  const [schema, setSchema] = useState(null);
  const [hist, setHist] = useState([]);
  const [health, setHealth] = useState({ status: "unknown" });

  const refresh = async () => {
    try {
      const s = await fetch("/api/schema").then(r => r.json());
      setSchema(s.schema || {});
      const h = await fetch("/api/query/history").then(r => r.json());
      setHist(h.history || []);
      const he = await fetch("/health").then(r => r.json());
      setHealth(he || { status: "unknown" });
    } catch {}
  };

  useEffect(() => { refresh(); const t = setInterval(refresh, 5000); return () => clearInterval(t); }, []);

  const cacheRate = (() => {
    const hits = hist.filter(x => x.metrics?.cache_hit).length;
    return hist.length ? Math.round((hits / hist.length) * 100) : 0;
  })();

  const avgLatency = (() => {
    const lat = hist.map(h => Number(h.metrics?.response_time_ms || 0)).filter(x => x > 0);
    if (!lat.length) return 0;
    return Math.round(lat.reduce((a,b)=>a+b,0)/lat.length);
  })();

  return (
    <div className="card card-elev">
      <div className="card-header bg-body-tertiary">
        <span className="section-title d-flex align-items-center gap-2">
          <i className="bi bi-activity text-primary"></i>
          System Metrics
        </span>
      </div>
      <div className="card-body">
        <div className="row g-3">
          <div className="col-md-4">
            <div className="metric-card">
              <div className="d-flex align-items-center justify-content-between mb-3">
                <span className="text-muted small">SYSTEM HEALTH</span>
                <i className="bi bi-heart-pulse fs-5 text-danger"></i>
              </div>
              <div className="fs-5 fw-semibold text-capitalize">{health.status}</div>
              
              <hr className="my-3" />
              
              <div className="mb-2">
                <div className="d-flex justify-content-between align-items-center mb-1">
                  <span className="small text-muted">Cache Hit Rate</span>
                  <span className="small fw-semibold">{cacheRate}%</span>
                </div>
                <div className="progress" style={{ height: '6px' }}>
                  <div className="progress-bar bg-success" style={{ width: `${cacheRate}%` }}></div>
                </div>
              </div>
              
              <div className="mt-3">
                <div className="small text-muted">Avg Response Time</div>
                <div className="fs-6 fw-semibold">{avgLatency} ms</div>
              </div>
            </div>
          </div>
          
          <div className="col-md-4">
            <div className="metric-card">
              <div className="d-flex align-items-center justify-content-between mb-3">
                <span className="text-muted small">RECENT QUERIES</span>
                <i className="bi bi-clock-history fs-5 text-primary"></i>
              </div>
              <div style={{ maxHeight: 180, overflow: "auto" }}>
                {hist.length > 0 ? (
                  <ul className="list-unstyled small mb-0">
                    {hist.slice().reverse().slice(0, 5).map((h, i) => (
                      <li key={i} className="mb-2 pb-2 border-bottom">
                        <div className="text-truncate" title={h.query}>
                          {h.query}
                        </div>
                        <div className="text-muted d-flex justify-content-between align-items-center mt-1">
                          <span>{h.metrics?.response_time_ms || 0} ms</span>
                          {h.metrics?.cache_hit && (
                            <span className="badge bg-success-subtle text-success-emphasis">cached</span>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-muted small text-center py-3">No queries yet</div>
                )}
              </div>
            </div>
          </div>
          
          <div className="col-md-4">
            <div className="metric-card">
              <div className="d-flex align-items-center justify-content-between mb-3">
                <span className="text-muted small">SCHEMA INFO</span>
                <i className="bi bi-diagram-3 fs-5 text-info"></i>
              </div>
              <div className="row g-3">
                <div className="col-6">
                  <div className="text-center">
                    <div className="fs-4 fw-bold text-primary">{(schema?.tables || []).length}</div>
                    <div className="small text-muted">Tables</div>
                  </div>
                </div>
                <div className="col-6">
                  <div className="text-center">
                    <div className="fs-4 fw-bold text-success">{(schema?.relationships || []).length}</div>
                    <div className="small text-muted">Relations</div>
                  </div>
                </div>
                <div className="col-12 mt-3">
                  <div className="small text-muted">Total Columns</div>
                  <div className="fs-6 fw-semibold">
                    {(schema?.tables || []).reduce((sum, t) => sum + (t.columns?.length || 0), 0)}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
