import { useState, useEffect } from "react";

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
  blue: "#2563eb",
  purple: "#7c3aed",
};

const API_BASE = "/api/code";

const CodeBlock = ({ code, language = "rust" }) => {
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

const Badge = ({ children, color = C.gray, bg = null }) => (
  <span style={{
    background: bg || `${color}15`,
    color: color,
    padding: "3px 10px",
    borderRadius: 4,
    fontSize: 10,
    fontWeight: 600,
    letterSpacing: 0.5,
    textTransform: "uppercase",
  }}>{children}</span>
);

const ScoreCircle = ({ score }) => {
  const getColor = (s) => {
    if (s >= 80) return C.green;
    if (s >= 60) return C.amber;
    if (s >= 40) return "#f97316";
    return C.red;
  };
  const color = getColor(score);
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div style={{ position: "relative", width: 120, height: 120 }}>
      <svg width="120" height="120" style={{ transform: "rotate(-90deg)" }}>
        <circle cx="60" cy="60" r="45" stroke={C.border} strokeWidth="8" fill="none" />
        <circle
          cx="60" cy="60" r="45"
          stroke={color}
          strokeWidth="8"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.5s ease" }}
        />
      </svg>
      <div style={{
        position: "absolute",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        textAlign: "center",
      }}>
        <div style={{ fontSize: 28, fontWeight: 600, color: color }}>{score}</div>
        <div style={{ fontSize: 10, color: C.grayL, letterSpacing: 1 }}>SCORE</div>
      </div>
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
        flexWrap: "wrap",
        gap: 8,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <Badge color={color}>{labels[type]}</Badge>
          {item.id && <span style={{ color: C.grayL, fontSize: 10, fontFamily: "'JetBrains Mono', monospace" }}>{item.id}</span>}
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
            lineHeight: 1.6,
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
  const [forceRefresh, setForceRefresh] = useState(false);

  const analyzeRepo = async () => {
    if (!repoUrl.includes("github.com")) {
      setError("Please enter a valid GitHub URL");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const resp = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl, force_refresh: forceRefresh }),
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

  const downloadReport = (format) => {
    if (!result?.scan_id) return;
    window.open(`${API_BASE}/report/${format}/${result.scan_id}`, "_blank");
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
          <span style={{ marginLeft: 8, fontSize: 10, color: C.grayL }}>v2.2</span>
        </a>
        <nav style={{ display: "flex", gap: 24, alignItems: "center" }}>
          <a href="/" style={{ color: C.grayL, textDecoration: "none", fontSize: 13, fontWeight: 500 }}>Home</a>
          <a href="https://docs.oraclesentinel.xyz" style={{ color: C.grayL, textDecoration: "none", fontSize: 13, fontWeight: 500 }}>Docs</a>
        </nav>
      </header>

      {/* Main Content */}
      <main style={{ maxWidth: 1000, margin: "0 auto", padding: "40px 24px", flex: 1, width: "100%" }}>
        {/* Title */}
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <h1 style={{
            fontSize: 36,
            fontWeight: 300,
            marginBottom: 12,
            color: C.black,
            letterSpacing: -1,
          }}>
            Solana Security Scanner
          </h1>
          <p style={{ color: C.grayL, fontSize: 14, maxWidth: 500, margin: "0 auto", lineHeight: 1.6 }}>
            AI-powered vulnerability detection for Solana/Anchor programs and DeFi protocols
          </p>
        </div>

        {/* Input */}
        <div style={{
          display: "flex",
          gap: 12,
          marginBottom: 16,
          maxWidth: 700,
          margin: "0 auto 16px",
        }}>
          <input
            type="text"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="https://github.com/user/solana-program"
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
            {loading ? "Scanning..." : "Scan"}
          </button>
        </div>

        {/* Options */}
        <div style={{
          display: "flex",
          justifyContent: "center",
          gap: 16,
          marginBottom: 40,
        }}>
          <label style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontSize: 12,
            color: C.grayL,
            cursor: "pointer",
          }}>
            <input
              type="checkbox"
              checked={forceRefresh}
              onChange={(e) => setForceRefresh(e.target.checked)}
              style={{ cursor: "pointer" }}
            />
            Force refresh (bypass cache)
          </label>
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
            <div style={{ fontSize: 14, color: C.gray }}>Analyzing repository for vulnerabilities...</div>
            <div style={{ fontSize: 12, marginTop: 8 }}>This may take 1-2 minutes</div>
          </div>
        )}

        {/* Result */}
        {result && !loading && (
          <div>
            {/* Header with Score and Badges */}
            <div style={{
              display: "flex",
              gap: 24,
              marginBottom: 32,
              flexWrap: "wrap",
            }}>
              {/* Score */}
              <div style={{
                background: C.card,
                border: `1px solid ${C.border}`,
                borderRadius: 12,
                padding: 24,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}>
                <ScoreCircle score={result.score || 0} />
              </div>

              {/* Info */}
              <div style={{ flex: 1, minWidth: 280 }}>
                <div style={{
                  background: C.card,
                  border: `1px solid ${C.border}`,
                  borderRadius: 12,
                  padding: 20,
                  height: "100%",
                }}>
                  {/* Repo name */}
                  <div style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 14,
                    color: C.dark,
                    marginBottom: 12,
                    wordBreak: "break-all",
                  }}>
                    {result.repo?.replace("https://github.com/", "")}
                  </div>

                  {/* Badges */}
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
                    {result.is_solana_project && (
                      <Badge color={C.purple}>Solana</Badge>
                    )}
                    {result.framework && (
                      <Badge color={C.blue}>{result.framework}</Badge>
                    )}
                    {result.is_defi && (
                      <Badge color={C.amber}>DeFi</Badge>
                    )}
                    {result._cache?.cached && (
                      <Badge color={C.grayL}>Cached</Badge>
                    )}
                  </div>

                  {/* Stats */}
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
                    <div>
                      <div style={{ fontSize: 20, fontWeight: 600, color: C.red }}>{result.critical?.length || 0}</div>
                      <div style={{ fontSize: 10, color: C.grayL, letterSpacing: 0.5 }}>CRITICAL</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 20, fontWeight: 600, color: C.amber }}>{result.warnings?.length || 0}</div>
                      <div style={{ fontSize: 10, color: C.grayL, letterSpacing: 0.5 }}>WARNINGS</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 20, fontWeight: 600, color: C.gray }}>{result.improvements?.length || 0}</div>
                      <div style={{ fontSize: 10, color: C.grayL, letterSpacing: 0.5 }}>IMPROVE</div>
                    </div>
                  </div>

                  {/* Files info */}
                  <div style={{ marginTop: 12, fontSize: 12, color: C.grayL }}>
                    {result.files_analyzed} files analyzed • {result.total_lines?.toLocaleString()} lines
                  </div>
                </div>
              </div>
            </div>

            {/* Download Reports */}
            {result.scan_id && (
              <div style={{
                display: "flex",
                gap: 12,
                marginBottom: 24,
              }}>
                <button
                  onClick={() => downloadReport("pdf")}
                  style={{
                    padding: "10px 20px",
                    background: C.card,
                    border: `1px solid ${C.border}`,
                    borderRadius: 6,
                    color: C.dark,
                    fontSize: 12,
                    fontWeight: 500,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  📄 Download PDF Report
                </button>
                <button
                  onClick={() => downloadReport("markdown")}
                  style={{
                    padding: "10px 20px",
                    background: C.card,
                    border: `1px solid ${C.border}`,
                    borderRadius: 6,
                    color: C.dark,
                    fontSize: 12,
                    fontWeight: 500,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  📝 Download Markdown
                </button>
              </div>
            )}

            {/* Programs found */}
            {result.programs_found && result.programs_found.length > 0 && (
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontSize: 10, color: C.grayL, marginBottom: 8, letterSpacing: 1 }}>PROGRAMS DETECTED</div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {result.programs_found.map((prog, i) => (
                    <span key={i} style={{
                      padding: "6px 12px",
                      background: C.bg2,
                      border: `1px solid ${C.border}`,
                      borderRadius: 4,
                      fontSize: 11,
                      color: C.gray,
                      fontFamily: "'JetBrains Mono', monospace",
                    }}>{prog}</span>
                  ))}
                </div>
              </div>
            )}

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
                ✓ No issues found. Code looks good!
              </div>
            )}
          </div>
        )}

        {/* Features - shown when no result */}
        {!result && !loading && (
          <div>
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: 16,
              marginTop: 32,
            }}>
              {[
                { label: "SOLANA/ANCHOR", desc: "15+ vulnerability checks including signer, owner, PDA, CPI validation", color: C.purple },
                { label: "DEFI PROTOCOLS", desc: "Flash loan attacks, oracle manipulation, slippage, liquidation issues", color: C.amber },
                { label: "GENERAL SECURITY", desc: "SQL injection, XSS, hardcoded secrets, auth vulnerabilities", color: C.red },
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

            {/* Vulnerability IDs */}
            <div style={{
              marginTop: 32,
              background: C.card,
              border: `1px solid ${C.border}`,
              borderRadius: 8,
              padding: 24,
            }}>
              <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: 1, color: C.grayL, marginBottom: 16 }}>
                SOLANA VULNERABILITY DETECTION
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {[
                  "SOL-001 Missing Signer",
                  "SOL-002 Missing Owner",
                  "SOL-003 Arbitrary CPI",
                  "SOL-004 PDA Validation",
                  "SOL-005 Integer Overflow",
                  "SOL-006 Account Matching",
                  "SOL-007 Type Cosplay",
                  "SOL-008 Account Closing",
                ].map((v) => (
                  <span key={v} style={{
                    padding: "4px 10px",
                    background: C.bg2,
                    borderRadius: 4,
                    fontSize: 11,
                    color: C.gray,
                    fontFamily: "'JetBrains Mono', monospace",
                  }}>{v}</span>
                ))}
              </div>
            </div>
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
