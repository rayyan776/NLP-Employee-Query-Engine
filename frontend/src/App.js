import { useState, useEffect } from "react";
import DatabaseConnector from "./components/DatabaseConnector";
import DocumentUploader from "./components/DocumentUploader";
import QueryPanel from "./components/QueryPanel";
import ResultsView from "./components/ResultsView";
import MetricsDashboard from "./components/MetricsDashboard";
import ThemeToggle from "./components/ThemeToggle";
import { ToastHost } from "./components/ToastHost";

export default function App() {
  const [dbConnected, setDbConnected] = useState(false);
  const [docsUploaded, setDocsUploaded] = useState(false);
  const [queryRun, setQueryRun] = useState(false);

  useEffect(() => {
    const schemaHandler = () => setDbConnected(true);
    const uploadHandler = () => setDocsUploaded(true);
    const resultsHandler = () => setQueryRun(true);
    
    window.addEventListener("schema", schemaHandler);
    window.addEventListener("docs_complete", uploadHandler);
    window.addEventListener("results", resultsHandler);
    
    return () => {
      window.removeEventListener("schema", schemaHandler);
      window.removeEventListener("docs_complete", uploadHandler);
      window.removeEventListener("results", resultsHandler);
    };
  }, []);

  const scrollToSection = (id) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
      // Add highlight class
      element.classList.add("section-highlight");
      setTimeout(() => {
        element.classList.remove("section-highlight");
      }, 3000);
    }
  };

  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className="sidebar p-3 bg-body-tertiary">
        <div className="d-flex align-items-center gap-2 mb-3">
          <i className="bi bi-stack fs-4 text-primary"></i>
          <span className="fw-semibold">Navigation</span>
        </div>
        <nav className="nav nav-pills flex-column gap-1">
          <a className="nav-link active" onClick={() => scrollToSection("connect")}>
            <i className="bi bi-database-check me-2"></i>Connect Data
          </a>
          <a 
            className={`nav-link ${!dbConnected ? 'disabled' : ''}`} 
            onClick={() => dbConnected && scrollToSection("upload")}
            style={{ cursor: dbConnected ? 'pointer' : 'not-allowed', opacity: dbConnected ? 1 : 0.5 }}
          >
            <i className="bi bi-cloud-arrow-up me-2"></i>Upload Documents
          </a>
          <a 
            className={`nav-link ${!docsUploaded ? 'disabled' : ''}`} 
            onClick={() => docsUploaded && scrollToSection("query")}
            style={{ cursor: docsUploaded ? 'pointer' : 'not-allowed', opacity: docsUploaded ? 1 : 0.5 }}
          >
            <i className="bi bi-search me-2"></i>Query
          </a>
          <a 
            className={`nav-link ${!queryRun ? 'disabled' : ''}`} 
            onClick={() => queryRun && scrollToSection("results")}
            style={{ cursor: queryRun ? 'pointer' : 'not-allowed', opacity: queryRun ? 1 : 0.5 }}
          >
            <i className="bi bi-table me-2"></i>Results
          </a>
          <a className="nav-link" onClick={() => scrollToSection("metrics")}>
            <i className="bi bi-activity me-2"></i>Metrics
          </a>
        </nav>

        <div className="mt-4">
          <div className="fw-semibold mb-2">Appearance</div>
          <ThemeToggle />
        </div>
      </aside>

      {/* Main content */}
      <div>
        {/* Topbar */}
        <div className="topbar brand-bar text-white">
          <div className="container-fluid py-2 d-flex align-items-center justify-content-between">
            <div className="brand d-flex align-items-center gap-2">
              <i className="bi bi-bar-chart-steps fs-5"></i>
              <span>NLP Employee Query Engine</span>
            </div>
            <div className="d-none d-lg-flex align-items-center gap-3">
              <span className="small opacity-75">Schema-adaptive • SQL + Documents • Cached</span>
            </div>
          </div>
        </div>

        <main className="container-fluid py-4">
          {/* Step 1: Connect Database */}
          <div className="mb-4 fade-in-section" id="connect">
            <div className="d-flex align-items-center mb-2">
              <span className={`step-indicator ${dbConnected ? 'completed' : 'active'}`}>1</span>
              <span className="text-muted small">STEP 1</span>
            </div>
            <DatabaseConnector />
          </div>

          {/* Step 2: Upload Documents - Only show after DB connected */}
          {dbConnected && (
            <div className="mb-4 fade-in-section" id="upload">
              <div className="d-flex align-items-center mb-2">
                <span className={`step-indicator ${docsUploaded ? 'completed' : 'active'}`}>2</span>
                <span className="text-muted small">STEP 2</span>
              </div>
              <DocumentUploader />
            </div>
          )}

          {/* Step 3: Query - Only show after docs uploaded */}
          {docsUploaded && (
            <div className="mb-4 fade-in-section" id="query">
              <div className="d-flex align-items-center mb-2">
                <span className={`step-indicator ${queryRun ? 'completed' : 'active'}`}>3</span>
                <span className="text-muted small">STEP 3</span>
              </div>
              <QueryPanel />
            </div>
          )}

          {/* Step 4: Results - Only show after query run */}
          {queryRun && (
            <div className="mb-4 fade-in-section" id="results">
              <div className="d-flex align-items-center mb-2">
                <span className="step-indicator active">4</span>
                <span className="text-muted small">STEP 4</span>
              </div>
              <ResultsView />
            </div>
          )}

          {/* Metrics Dashboard - Always visible */}
          <div className="mb-4" id="metrics">
            <div className="d-flex align-items-center mb-2">
              <span className="step-indicator">
                <i className="bi bi-graph-up" style={{ fontSize: '0.85rem' }}></i>
              </span>
              <span className="text-muted small">METRICS</span>
            </div>
            <MetricsDashboard />
          </div>
        </main>
      </div>

      <ToastHost />
    </div>
  );
}
