import { useState, useEffect } from "react";
import OracleSentinelLanding from "./OracleSentinelLanding";
import OracleSentinelDashboard from "./OracleSentinelDashboard";
import OracleSentinelDocs from "./OracleSentinelDocs";
import OracleSentinelCode from "./OracleSentinelCode";

export default function App() {
  const [currentPath, setCurrentPath] = useState(window.location.pathname);
  
  useEffect(() => {
    const handlePopState = () => setCurrentPath(window.location.pathname);
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);
  
  const path = currentPath.replace(/\/$/, "") || "/";
  
  if (path === "/predict") return <OracleSentinelDashboard />;
  if (path === "/docs") return <OracleSentinelDocs />;
  if (path === "/code") return <OracleSentinelCode />;
  return <OracleSentinelLanding />;
}
