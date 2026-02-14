import { useState } from "react";

const C = {
  bg: "#fafafa",
  bg2: "#f5f5f5",
  card: "#ffffff",
  border: "#e5e5e5",
  borderD: "#d4d4d4",
  black: "#171717",
  dark: "#262626",
  gray: "#525252",
  grayL: "#737373",
  grayLL: "#a3a3a3",
  red: "#dc2626",
  amber: "#d97706",
  green: "#16a34a",
};

const CodeBlock = ({ code, language = "python" }) => {
  const [copied, setCopied] = useState(false);
  const copyCode = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div style={{ margin: "8px 0" }}>
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        background: C.bg2,
        padding: "6px 12px",
        borderRadius: "6px 6px 0 0",
        border: `1px solid ${C.border}`,
        borderBottom: "none",
      }}>
        <span style={{ color: C.grayL, fontSize: 10, textTransform: "uppercase", letterSpacing: 1 }}>{language}</span>
        <button onClick={copyCode} style={{
          background: copied ? C.green : "transparent",
          border: `1px solid ${copied ? C.green : C.border}`,
          borderRadius: 4,
          padding: "2px 10px",
          color: copied ? "#fff" : C.gray,
          fontSize: 10,
          cursor: "pointer",
          transition: "all 0.2s",
        }}>
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre style={{
        background: "#1e1e1e",
        padding: 14,
        borderRadius: "0 0 6px 6px",
        border: `1px solid ${C.border}`,
        borderTop: "none",
        overflow: "auto",
        margin: 0,
        fontSize: 12,
        lineHeight: 1.6,
        color: "#d4d4d4",
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
      }}>{code}</pre>
    </div>
  );
};

const IssueCard = ({ item, type }) => {
  const colors = { critical: C.red, warning: C.amber, improvement: C.gray };
  const labels = { critical: "CRITICAL", warning: "WARNING", improvement: "IMPROVEMENT" };
  const color = colors[type] || C.gray;
  
  return (
    <div style={{
      background: C.card,
      border: `1px solid ${C.border}`,
      borderRadius: 8,
      marginBottom: 16,
      overflow: "hidden",
    }}>
      <div style={{
        padding: "12px 16px",
        borderBottom: `1px solid ${C.border}`,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        background: C.bg2,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{
            background: `${color}15`,
            color: color,
            padding: "2px 8px",
            borderRadius: 4,
            fontSize: 10,
            fontWeight: 600,
            letterSpacing: 1,
          }}>{labels[type]}</span>
          <span style={{ color: C.dark, fontSize: 14, fontWeight: 500 }}>{item.title}</span>
        </div>
        <span style={{ 
          color: C.grayL, 
          fontSize: 11, 
          fontFamily: "'JetBrains Mono', monospace",
          background: C.bg,
          padding: "2px 8px",
          borderRadius: 4,
        }}>
          {item.file}:{item.line}
        </span>
      </div>
      
      <div style={{ padding: 16 }}>
        {item.code && (
          <div style={{ marginBottom: 12 }}>
            <div style={{ color: C.grayL, fontSize: 10, marginBottom: 6, letterSpacing: 1 }}>PROBLEMATIC CODE</div>
            <CodeBlock code={item.code} />
          </div>
        )}
        
        {item.current && (
          <div style={{ marginBottom: 12 }}>
            <div style={{ color: C.grayL, fontSize: 10, marginBottom: 6, letterSpacing: 1 }}>CURRENT</div>
            <CodeBlock code={item.current} />
          </div>
        )}
        
        {(item.risk || item.issue || item.benefit) && (
          <div style={{ 
            color: C.gray, 
            fontSize: 13, 
            marginBottom: 12,
            padding: 12,
            background: C.bg2,
            borderRadius: 6,
            borderLeft: `3px solid ${color}`,
          }}>
            {item.risk || item.issue || item.benefit}
          </div>
        )}
        
        {(item.fix_code || item.suggested) && (
          <div>
            <div style={{ color: C.grayL, fontSize: 10, marginBottom: 6, letterSpacing: 1 }}>RECOMMENDED FIX</div>
            <CodeBlock code={item.fix_code || item.suggested} />
          </div>
        )}
        
        {item.fix && !item.fix_code && (
          <div style={{ 
            color: C.green, 
            fontSize: 12, 
            marginTop: 8,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}>
            <span style={{ fontFamily: "'JetBrains Mono', monospace" }}>[FIX]</span>
            {item.fix}
          </div>
        )}
      </div>
    </div>
  );
};

export default function OracleSentinelCode() {
  const [repoUrl, setRepoUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const analyzeRepo = async () => {
    if (!repoUrl.includes("github.com")) {
      setError("Please enter a valid GitHub URL");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const resp = await fetch("/api/code/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl }),
      });
      const data = await resp.json();
      if (data.error) {
        setError(data.error);
      } else {
        setResult(data);
      }
    } catch (err) {
      setError("Failed to analyze repository: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      minHeight: "100vh", 
      display: "flex",
      flexDirection: "column",
      background: C.bg, 
      color: C.dark,
      fontFamily: "'Inter', -apple-system, sans-serif",
    }}>
      {/* Header */}
      <header style={{
        padding: "16px 40px",
        borderBottom: `1px solid ${C.border}`,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        background: C.card,
      }}>
        <a href="/" style={{ textDecoration: "none" }}>
          <span style={{ 
            fontFamily: "'JetBrains Mono', monospace", 
            fontWeight: 600, 
            fontSize: 14,
            color: C.black,
            letterSpacing: 1,
          }}>
            SENTINEL CODE
          </span>
        </a>
        <nav style={{ display: "flex", gap: 32 }}>
          <a href="/" style={{
            color: C.grayL,
            textDecoration: "none",
            fontSize: 13,
            fontWeight: 500,
          }}>Home</a>
          <a href="/docs" style={{
            color: C.grayL,
            textDecoration: "none",
            fontSize: 13,
            fontWeight: 500,
          }}>Docs</a>
        </nav>
      </header>

      {/* Main Content */}
      <main style={{ maxWidth: 900, margin: "0 auto", padding: "60px 24px", flex: 1, width: "100%" }}>
        {/* Title */}
        <div style={{ textAlign: "center", marginBottom: 48 }}>
          <h1 style={{
            fontSize: 40,
            fontWeight: 300,
            marginBottom: 16,
            color: C.black,
            letterSpacing: -1,
          }}>
            Code Analysis
          </h1>
          <p style={{ color: C.grayL, fontSize: 15, maxWidth: 450, margin: "0 auto", lineHeight: 1.6 }}>
            AI-powered security and quality analysis for GitHub repositories
          </p>
        </div>

        {/* Input */}
        <div style={{
          display: "flex",
          gap: 12,
          marginBottom: 48,
          maxWidth: 650,
          margin: "0 auto 48px",
        }}>
          <input
            type="text"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="https://github.com/user/repository"
            style={{
              flex: 1,
              padding: "14px 18px",
              background: C.card,
              border: `1px solid ${C.border}`,
              borderRadius: 8,
              color: C.dark,
              fontSize: 14,
              fontFamily: "'JetBrains Mono', monospace",
              outline: "none",
            }}
            onFocus={(e) => e.target.style.borderColor = C.borderD}
            onBlur={(e) => e.target.style.borderColor = C.border}
            onKeyDown={(e) => e.key === "Enter" && analyzeRepo()}
          />
          <button
            onClick={analyzeRepo}
            disabled={loading}
            style={{
              padding: "14px 32px",
              background: loading ? C.bg2 : C.black,
              border: "none",
              borderRadius: 8,
              color: loading ? C.grayL : "#fff",
              fontSize: 14,
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div style={{
            background: `${C.red}10`,
            border: `1px solid ${C.red}30`,
            borderRadius: 8,
            padding: 16,
            marginBottom: 24,
            color: C.red,
            fontSize: 13,
          }}>{error}</div>
        )}

        {/* Loading */}
        {loading && (
          <div style={{ textAlign: "center", padding: 80, color: C.grayL }}>
            <div style={{
              width: 40, height: 40,
              border: `2px solid ${C.border}`,
              borderTop: `2px solid ${C.dark}`,
              borderRadius: "50%",
              margin: "0 auto 20px",
              animation: "spin 1s linear infinite",
            }} />
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            <div style={{ fontSize: 14, color: C.gray }}>Cloning and analyzing repository...</div>
            <div style={{ fontSize: 12, marginTop: 8 }}>This may take 1-2 minutes</div>
          </div>
        )}

        {/* Result */}
        {result && !loading && (
          <div>
            {/* Stats Header */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 16,
              marginBottom: 32,
            }}>
              <div style={{
                background: C.card,
                border: `1px solid ${C.border}`,
                borderRadius: 8,
                padding: 20,
              }}>
                <div style={{ color: C.grayL, fontSize: 10, marginBottom: 8, letterSpacing: 1 }}>REPOSITORY</div>
                <div style={{ 
                  fontFamily: "'JetBrains Mono', monospace", 
                  fontSize: 13,
                  color: C.dark,
                  wordBreak: "break-all",
                }}>
                  {result.repo?.replace("https://github.com/", "")}
                </div>
              </div>
              
              <div style={{
                background: C.card,
                border: `1px solid ${C.border}`,
                borderRadius: 8,
                padding: 20,
                textAlign: "right",
              }}>
                <div style={{ color: C.grayL, fontSize: 10, marginBottom: 8, letterSpacing: 1 }}>ANALYZED</div>
                <div style={{ fontSize: 14, color: C.dark }}>{result.files_analyzed} files</div>
                <div style={{ fontSize: 12, color: C.grayL }}>{result.total_lines?.toLocaleString()} lines</div>
              </div>
            </div>

            {/* Languages */}
            {result.languages && Object.keys(result.languages).length > 0 && (
              <div style={{ display: "flex", gap: 8, marginBottom: 24, flexWrap: "wrap" }}>
                {Object.entries(result.languages).map(([lang, pct]) => (
                  <span key={lang} style={{
                    padding: "6px 12px",
                    background: C.card,
                    border: `1px solid ${C.border}`,
                    borderRadius: 4,
                    fontSize: 12,
                    color: C.gray,
                    fontFamily: "'JetBrains Mono', monospace",
                  }}>{lang} {pct}%</span>
                ))}
              </div>
            )}

            {/* Summary */}
            {result.summary && (
              <div style={{
                background: C.card,
                border: `1px solid ${C.border}`,
                borderRadius: 8,
                padding: 20,
                marginBottom: 32,
                color: C.gray,
                fontSize: 14,
                lineHeight: 1.7,
              }}>{result.summary}</div>
            )}

            {/* Critical Issues */}
            {result.critical && result.critical.length > 0 && (
              <div style={{ marginBottom: 40 }}>
                <h2 style={{ 
                  color: C.red, 
                  fontSize: 12, 
                  marginBottom: 16,
                  fontWeight: 600,
                  letterSpacing: 2,
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                }}>
                  CRITICAL ISSUES
                  <span style={{
                    background: `${C.red}15`,
                    padding: "2px 8px",
                    borderRadius: 4,
                    fontSize: 11,
                  }}>{result.critical.length}</span>
                </h2>
                {result.critical.map((item, i) => (
                  <IssueCard key={i} item={item} type="critical" />
                ))}
              </div>
            )}

            {/* Warnings */}
            {result.warnings && result.warnings.length > 0 && (
              <div style={{ marginBottom: 40 }}>
                <h2 style={{ 
                  color: C.amber, 
                  fontSize: 12, 
                  marginBottom: 16,
                  fontWeight: 600,
                  letterSpacing: 2,
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                }}>
                  WARNINGS
                  <span style={{
                    background: `${C.amber}15`,
                    padding: "2px 8px",
                    borderRadius: 4,
                    fontSize: 11,
                  }}>{result.warnings.length}</span>
                </h2>
                {result.warnings.map((item, i) => (
                  <IssueCard key={i} item={item} type="warning" />
                ))}
              </div>
            )}

            {/* Improvements */}
            {result.improvements && result.improvements.length > 0 && (
              <div style={{ marginBottom: 40 }}>
                <h2 style={{ 
                  color: C.gray, 
                  fontSize: 12, 
                  marginBottom: 16,
                  fontWeight: 600,
                  letterSpacing: 2,
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                }}>
                  IMPROVEMENTS
                  <span style={{
                    background: `${C.gray}15`,
                    padding: "2px 8px",
                    borderRadius: 4,
                    fontSize: 11,
                  }}>{result.improvements.length}</span>
                </h2>
                {result.improvements.map((item, i) => (
                  <IssueCard key={i} item={item} type="improvement" />
                ))}
              </div>
            )}

            {/* No issues */}
            {(!result.critical || result.critical.length === 0) &&
             (!result.warnings || result.warnings.length === 0) &&
             (!result.improvements || result.improvements.length === 0) && (
              <div style={{
                background: `${C.green}10`,
                border: `1px solid ${C.green}30`,
                borderRadius: 8,
                padding: 32,
                textAlign: "center",
                color: C.green,
              }}>
                No issues found. Code looks good.
              </div>
            )}
          </div>
        )}

        {/* Features - shown when no result */}
        {!result && !loading && (
          <div style={{ 
            display: "grid", 
            gridTemplateColumns: "repeat(3, 1fr)", 
            gap: 16, 
            marginTop: 48 
          }}>
            {[
              { label: "SECURITY", desc: "SQL injection, XSS, hardcoded secrets, auth vulnerabilities", color: C.red },
              { label: "BUGS", desc: "Null pointers, race conditions, unhandled exceptions", color: C.amber },
              { label: "QUALITY", desc: "Error handling, input validation, type hints, tests", color: C.gray },
            ].map((f) => (
              <div key={f.label} style={{
                background: C.card,
                border: `1px solid ${C.border}`,
                borderRadius: 8,
                padding: 24,
              }}>
                <div style={{ 
                  color: f.color, 
                  fontSize: 10, 
                  fontWeight: 600, 
                  marginBottom: 12,
                  letterSpacing: 2,
                }}>{f.label}</div>
                <div style={{ color: C.grayL, fontSize: 13, lineHeight: 1.6 }}>{f.desc}</div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: `1px solid ${C.border}`,
        padding: "24px 40px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        color: C.grayL,
        fontSize: 12,
        background: C.card,
      }}>
        <span>
          Part of <a href="/" style={{ color: C.dark, textDecoration: "none" }}>Oracle Sentinel</a> Intelligence Layer
        </span>
        <div style={{ display: "flex", gap: 24 }}>
          <a href="https://x.com/oracle_sentinel" target="_blank" rel="noopener noreferrer" style={{ color: C.gray, textDecoration: "none" }}>X</a>
          <a href="https://github.com/oraclesentinel" target="_blank" rel="noopener noreferrer" style={{ color: C.gray, textDecoration: "none" }}>GitHub</a>
        </div>
      </footer>
    </div>
  );
}
