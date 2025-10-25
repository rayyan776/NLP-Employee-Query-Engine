import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const [theme, setTheme] = useState("light");
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme") || "light";
    setTheme(savedTheme);
    document.documentElement.setAttribute("data-bs-theme", savedTheme);
  }, []);

  const changeTheme = (newTheme) => {
    if (newTheme === theme) return;
    
    setIsTransitioning(true);
    setTheme(newTheme);
    
    // Add fade effect
    document.documentElement.style.opacity = "0.95";
    
    // Change theme
    setTimeout(() => {
      document.documentElement.setAttribute("data-bs-theme", newTheme);
      localStorage.setItem("theme", newTheme);
      
      // Restore opacity
      setTimeout(() => {
        document.documentElement.style.opacity = "1";
        setIsTransitioning(false);
      }, 100);
    }, 150);
  };

  return (
    <div className="d-flex gap-2">
      <button
        className={`btn btn-sm ${theme === "light" ? "btn-primary" : "btn-outline-secondary"}`}
        onClick={() => changeTheme("light")}
        disabled={isTransitioning}
        title="Light Mode"
      >
        <i className="bi bi-sun-fill"></i>
      </button>
      <button
        className={`btn btn-sm ${theme === "dark" ? "btn-primary" : "btn-outline-secondary"}`}
        onClick={() => changeTheme("dark")}
        disabled={isTransitioning}
        title="Dark Mode"
      >
        <i className="bi bi-moon-fill"></i>
      </button>
    </div>
  );
}
