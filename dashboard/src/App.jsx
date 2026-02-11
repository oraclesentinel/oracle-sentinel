import { useState, useEffect } from "react";
import OracleSentinelLanding from "./OracleSentinelLanding";
import OracleSentinelDashboard from "./OracleSentinelDashboard";

export default function App() {
  const [currentPath, setCurrentPath] = useState(window.location.pathname);

  useEffect(() => {
    const handlePopState = () => setCurrentPath(window.location.pathname);
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const path = currentPath.replace(/\/$/, "") || "/";

  if (path === "/app") return <OracleSentinelDashboard />;
  return <OracleSentinelLanding />;
}
