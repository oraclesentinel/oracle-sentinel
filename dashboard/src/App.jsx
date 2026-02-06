import { useState } from "react";
import OracleSentinelDashboard from "./OracleSentinelDashboard";
import OracleSentinelDocs from "./OracleSentinelDocs";
import OracleSentinelLanding from "./OracleSentinelLanding";

export default function App() {
  const path = window.location.pathname;
  if (path === "/docs") return <OracleSentinelDocs />;
  if (path === "/app") return <OracleSentinelDashboard />;
  return <OracleSentinelLanding />;
}
