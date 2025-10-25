import { useEffect, useRef, useState } from "react";

export function ToastHost() {
  const [items, setItems] = useState([]);
  const ctr = useRef(0);

  useEffect(() => {
    const h = (e) => {
      const id = ++ctr.current;
      const payload = { id, ...(e.detail || {}) };
      setItems((xs) => [...xs, payload]);
      setTimeout(() => setItems((xs) => xs.filter((i) => i.id !== id)), 3500);
    };
    window.addEventListener("toast", h);
    return () => window.removeEventListener("toast", h);
  }, []);

  return (
    <div className="toast-container position-fixed top-0 end-0 p-3" style={{ zIndex: 1080 }}>
      {items.map((t) => (
        <div key={t.id} className={`toast show border-0 ${t.type === "danger" ? "text-bg-danger" : t.type === "success" ? "text-bg-success" : "text-bg-secondary"}`}>
          <div className="toast-header">
            <strong className="me-auto">{t.title || "Notice"}</strong>
          </div>
          <div className="toast-body">{t.body || ""}</div>
        </div>
      ))}
    </div>
  );
}
