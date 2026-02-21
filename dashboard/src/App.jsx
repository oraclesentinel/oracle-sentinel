import { useState, useEffect } from "react";
import OracleSentinelLanding from "./OracleSentinelLanding";
import OracleSentinelDashboard from "./OracleSentinelDashboard";
import OracleSentinelDocs from "./OracleSentinelDocs";
import OracleSentinelCode from "./OracleSentinelCode";
import SentinelEconomicDashboard from "./SentinelEconomicDashboard";

export default function App() {
  const [currentPath, setCurrentPath] = useState(window.location.pathname);

  useEffect(() => {
    const handlePopState = () => setCurrentPath(window.location.pathname);
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const path = currentPath.replace(/\/$/, "") || "/";
  const hostname = window.location.hostname;

  // Check subdomain first
  if (hostname.startsWith("predict.")) return <OracleSentinelDashboard />;
  if (hostname.startsWith("docs.")) return <OracleSentinelDocs />;
  if (hostname.startsWith("code.")) return <OracleSentinelCode />;
  if (hostname.startsWith("economic.")) return <SentinelEconomicDashboard />;

  // Fallback to path-based routing (for backward compatibility)
  if (path === "/predict") return <OracleSentinelDashboard />;
  if (path === "/docs") return <OracleSentinelDocs />;
  if (path === "/code") return <OracleSentinelCode />;
  if (path === "/economic") return <SentinelEconomicDashboard />;

  return <OracleSentinelLanding />;
}
