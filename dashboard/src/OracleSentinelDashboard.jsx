import { useState, useEffect, useRef } from "react";

// ═══════════════════════════════════════════════════════════════
// ORACLE SENTINEL — TERMINAL INTELLIGENCE DASHBOARD
// Bloomberg Terminal / Cold Blue Aesthetic
// ═══════════════════════════════════════════════════════════════

const BLUE_BRIGHT = "#4da6ff";
const BLUE_MID = "#2d7fd4";
const BLUE_DIM = "#1a5a9e";
const BLUE_DARK = "#0d2847";
const ICE = "#c8ddf0";
const FROST = "#8badc4";
const SLATE = "#5a7184";
const RED_COLD = "#e05565";
const TEAL = "#4ecdc4";
const AMBER_COLD = "#d4a843";
const BG = "#080c12";
const BG_PANEL = "#0b1018";
const BORDER = "#141e2e";
const BORDER_LIGHT = "#1c2d42";
const GRID_LINE = "#0f1924";

const API_BASE = "/api";

function formatNum(n) {
  if (!n || n === 0) return "0";
  if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return n.toFixed(0);
}

function timeAgo(ts) {
  if (!ts) return "—";
  const diff = (Date.now() - new Date(ts + "Z").getTime()) / 1000;
  if (diff < 60) return Math.floor(diff) + "s ago";
  if (diff < 3600) return Math.floor(diff / 60) + "m ago";
  if (diff < 86400) return Math.floor(diff / 3600) + "h ago";
  return Math.floor(diff / 86400) + "d ago";
}

function Cursor() {
  const [on, setOn] = useState(true);
  useEffect(() => { const iv = setInterval(() => setOn(v => !v), 530); return () => clearInterval(iv); }, []);
  return <span style={{ color: BLUE_BRIGHT, fontWeight: "bold" }}>{on ? "█" : " "}</span>;
}

function Scanlines() {
  return (
    <div style={{
      position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
      background: `repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(13,40,71,0.02) 3px, rgba(13,40,71,0.02) 4px)`,
      pointerEvents: "none", zIndex: 9999,
    }} />
  );
}

function Styles() {
  return (
    <style>{`
      @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');
      @keyframes fadeInUp { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
      @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
      @keyframes slideIn { from { opacity: 0; transform: translateX(-8px); } to { opacity: 1; transform: translateX(0); } }
      @keyframes barGrow { from { transform: scaleY(0); } to { transform: scaleY(1); } }
      @keyframes aiGlow { 0%, 100% { box-shadow: 0 0 4px #4ecdc4, 0 0 8px #4ecdc420; } 50% { box-shadow: 0 0 8px #4ecdc4, 0 0 16px #4ecdc440; } }
      .tab-btn.ai-agent-tab { background: linear-gradient(135deg, #0d2847 0%, #1a5a9e20 100%); border-bottom: 2px solid #4ecdc4; color: #4ecdc4; animation: aiGlow 3s ease-in-out infinite; }
      .tab-btn.ai-agent-tab:hover { background: linear-gradient(135deg, #0d284790 0%, #1a5a9e40 100%); }
      .panel { background: ${BG_PANEL}; border: 1px solid ${BORDER}; border-radius: 3px; overflow: hidden; transition: border-color 0.3s; }
      .panel:hover { border-color: ${BORDER_LIGHT}; }
      .panel-head { background: linear-gradient(90deg, ${BLUE_DARK}25, transparent 70%); border-bottom: 1px solid ${BORDER}; padding: 7px 14px; display: flex; align-items: center; gap: 8px; }
      .row-hover:hover { background: ${BLUE_DARK}18 !important; }
      .tab-btn { background: transparent; border: none; border-bottom: 2px solid transparent; color: ${SLATE}; font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 500; letter-spacing: 0.5px; padding: 10px 20px; cursor: pointer; transition: all 0.2s; }
      .tab-btn:hover { color: ${FROST}; background: ${BLUE_DARK}15; }
      .tab-btn.active { color: ${BLUE_BRIGHT}; border-bottom-color: ${BLUE_MID}; background: ${BLUE_DARK}20; }
      ::-webkit-scrollbar { width: 5px; } ::-webkit-scrollbar-track { background: ${BG}; } ::-webkit-scrollbar-thumb { background: ${BORDER_LIGHT}; border-radius: 3px; }
    `}</style>
  );
}

function Header() {
  return (
    <div style={{ textAlign: "center", padding: "16px 0 8px", borderBottom: `1px solid ${BORDER}` }}>
      <div style={{ color: BLUE_BRIGHT, fontFamily: "'JetBrains Mono', monospace", fontSize: "16px", fontWeight: 700, letterSpacing: "4px" }}>
        ORACLE SENTINEL
      </div>
      <div style={{ color: SLATE, fontFamily: "'JetBrains Mono', monospace", fontSize: "12px", letterSpacing: "3px", marginTop: "4px" }}>
        POLYMARKET PREDICTION INTELLIGENCE v2.0
      </div>
    </div>
  );
}

function StatusBar({ scanCount, nextScan, uptime }) {
  const [time, setTime] = useState(new Date());
  useEffect(() => { const iv = setInterval(() => setTime(new Date()), 1000); return () => clearInterval(iv); }, []);
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "7px 20px", background: `linear-gradient(90deg, ${BLUE_DARK}12, ${BG_PANEL}, ${BLUE_DARK}12)`, borderBottom: `1px solid ${BORDER}`, fontFamily: "'JetBrains Mono', monospace", fontSize: "13px" }}>
      <div style={{ display: "flex", gap: "28px", alignItems: "center" }}>
        <span style={{ color: TEAL, display: "flex", alignItems: "center", gap: "6px" }}><span style={{ animation: "pulse 2s infinite", fontSize: "12px" }}>●</span>ONLINE</span>
        <span style={{ color: SLATE }}>UPTIME <span style={{ color: FROST }}>{uptime}</span></span>
        <span style={{ color: SLATE }}>SCANS <span style={{ color: FROST }}>{scanCount}</span></span>
      </div>
      <div style={{ display: "flex", gap: "28px" }}>
        <span style={{ color: SLATE }}>LAST SCAN <span style={{ color: AMBER_COLD }}>{nextScan}</span></span>
        <span style={{ color: SLATE }}>{time.toISOString().replace("T", " ").slice(0, 19)} UTC</span>
      </div>
    </div>
  );
}

function Panel({ title, children, style = {}, headerRight = null }) {
  return (
    <div className="panel" style={style}>
      <div className="panel-head">
        <span style={{ color: BLUE_BRIGHT, fontFamily: "'JetBrains Mono', monospace", fontSize: "12px", fontWeight: 600, letterSpacing: "1.5px", textTransform: "uppercase" }}>{title}</span>
        {headerRight && <div style={{ marginLeft: "auto" }}>{headerRight}</div>}
      </div>
      <div style={{ padding: "10px 14px" }}>{children}</div>
    </div>
  );
}

function Metric({ label, value, color = BLUE_BRIGHT, suffix = "", size = "20px" }) {
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ color, fontFamily: "'JetBrains Mono', monospace", fontSize: size, fontWeight: 600 }}>{value}{suffix}</div>
      <div style={{ color: SLATE, fontFamily: "'JetBrains Mono', monospace", fontSize: "13px", letterSpacing: "1px", marginTop: "3px", textTransform: "uppercase" }}>{label}</div>
    </div>
  );
}

function ProgressBar({ value, max = 100, color = BLUE_MID }) {
  return (
    <div style={{ width: "100%", height: "3px", background: BORDER, borderRadius: "2px", overflow: "hidden" }}>
      <div style={{ width: `${Math.min((value / max) * 100, 100)}%`, height: "100%", background: color, borderRadius: "2px", transition: "width 0.8s ease" }} />
    </div>
  );
}

function SignalRow({ signal, index }) {
  const isYes = signal.signal === "BUY_YES";
  const signalColor = isYes ? TEAL : RED_COLD;
  const st = { TRACKING: { color: AMBER_COLD, label: "TRACKING" }, RESOLVED_WIN: { color: TEAL, label: "CORRECT" }, RESOLVED_LOSS: { color: RED_COLD, label: "WRONG" } }[signal.status];
  return (
    <div className="row-hover" style={{ display: "grid", gridTemplateColumns: "64px 54px 1fr 62px 54px 50px 72px", gap: "8px", alignItems: "center", padding: "7px 10px", fontSize: "13px", fontFamily: "'JetBrains Mono', monospace", borderBottom: `1px solid ${GRID_LINE}`, animation: `fadeInUp 0.3s ease-out ${index * 0.04}s both`, cursor: "default" }}>
      <span style={{ color: SLATE, fontSize: "12px" }}>{signal.time}</span>
      <span style={{ color: signalColor, fontWeight: 600, fontSize: "12px" }}>{isYes ? "▲ YES" : "▼ NO"}</span>
      <span style={{ color: ICE, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{signal.market}</span>
      <span style={{ color: signal.edge > 0 ? TEAL : RED_COLD, textAlign: "right", fontWeight: 500 }}>{signal.edge > 0 ? "+" : ""}{signal.edge}%</span>
      <span style={{ color: FROST, textAlign: "right" }}>${signal.price.toFixed(2)}</span>
      <span style={{ color: signal.confidence === "HIGH" ? BLUE_BRIGHT : AMBER_COLD, textAlign: "center", fontSize: "13px", fontWeight: 500 }}>{signal.confidence}</span>
      <span style={{ color: st.color, textAlign: "right", fontSize: "13px", fontWeight: 500 }}>{st.label}</span>
    </div>
  );
}

function LiveLog({ logs }) {
  const ref = useRef(null);
  const [visibleLogs, setVisibleLogs] = useState([]);
  useEffect(() => { let i = 0; const iv = setInterval(() => { if (i < logs.length) { setVisibleLogs(prev => [...prev, logs[i]]); i++; } else clearInterval(iv); }, 160); return () => clearInterval(iv); }, []);
  useEffect(() => { if (ref.current) ref.current.scrollTop = ref.current.scrollHeight; }, [visibleLogs]);
  return (
    <div ref={ref} style={{ height: "280px", overflowY: "auto", fontFamily: "'JetBrains Mono', monospace", fontSize: "13px" }}>
      {visibleLogs.map((log, i) => {
        let color = SLATE;
        if (log.includes("✓")) color = TEAL;
        if (log.includes("◉ SIGNAL")) color = AMBER_COLD;
        if (log.includes("BUY_YES")) color = TEAL;
        if (log.includes("BUY_NO")) color = RED_COLD;
        if (log.includes("════")) color = BLUE_BRIGHT;
        if (log.includes("▸ Analyzing")) color = BLUE_DIM;
        if (log.includes("INITIATED")) color = BLUE_BRIGHT;
        return <div key={i} style={{ color, padding: "2px 0", lineHeight: "18px", animation: "slideIn 0.2s ease-out" }}>{log}</div>;
      })}
      {visibleLogs.length < logs.length && <Cursor />}
    </div>
  );
}

function Sparkline({ data, color = BLUE_MID, width = 80, height = 24 }) {
  const max = Math.max(...data); const min = Math.min(...data); const range = max - min || 1;
  const points = data.map((v, i) => `${(i / (data.length - 1)) * width},${height - ((v - min) / range) * (height - 4) - 2}`).join(" ");
  return <svg width={width} height={height} style={{ display: "block" }}><polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>;
}

function MarketRow({ market, index }) {
  const priceData = Array.from({ length: 12 }, () => market.price_yes + (Math.random() - 0.5) * 0.08);
  priceData.push(market.price_yes);
  return (
    <div className="row-hover" style={{ display: "grid", gridTemplateColumns: "1fr 90px 90px 70px", gap: "8px", alignItems: "center", padding: "8px 10px", fontSize: "13px", fontFamily: "'JetBrains Mono', monospace", borderBottom: `1px solid ${GRID_LINE}`, animation: `fadeInUp 0.3s ease-out ${index * 0.05}s both` }}>
      <span style={{ color: ICE, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{market.question}</span>
      <div style={{ display: "flex", justifyContent: "flex-end" }}><Sparkline data={priceData} color={market.price_yes > 0.5 ? TEAL : BLUE_MID} /></div>
      <div style={{ textAlign: "right" }}><span style={{ color: TEAL }}>Y:{market.price_yes.toFixed(2)}</span><span style={{ color: BORDER_LIGHT, margin: "0 4px" }}>│</span><span style={{ color: RED_COLD }}>N:{market.price_no.toFixed(2)}</span></div>
      <span style={{ color: FROST, textAlign: "right" }}>${(market.volume / 1000000).toFixed(1)}M</span>
    </div>
  );
}

function AccuracyGauge({ accuracy }) {
  const r = 44; const c = 2 * Math.PI * r; const o = c - (accuracy / 100) * c;
  const color = accuracy >= 70 ? TEAL : accuracy >= 50 ? AMBER_COLD : RED_COLD;
  return (
    <div style={{ position: "relative", width: "110px", height: "110px", margin: "0 auto" }}>
      <svg width="110" height="110" style={{ transform: "rotate(-90deg)" }}>
        <circle cx="55" cy="55" r={r} fill="none" stroke={BORDER} strokeWidth="5" />
        <circle cx="55" cy="55" r={r} fill="none" stroke={color} strokeWidth="5" strokeDasharray={c} strokeDashoffset={o} strokeLinecap="round" style={{ transition: "stroke-dashoffset 1.5s ease" }} />
      </svg>
      <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", textAlign: "center" }}>
        <div style={{ color, fontFamily: "'JetBrains Mono', monospace", fontSize: "24px", fontWeight: 700 }}>{accuracy}%</div>
        <div style={{ color: SLATE, fontFamily: "'JetBrains Mono', monospace", fontSize: "12px", letterSpacing: "1.5px" }}>ACCURACY</div>
      </div>
    </div>
  );
}

function WeeklyAccuracyChart({ data }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0px" }}>
      {/* Bar chart */}
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-around", height: "80px", padding: "0 4px" }}>
        {data.map((d, i) => {
          const h = Math.max((d.pct / 100) * 65, 3);
          const color = d.pct >= 70 ? TEAL : d.pct >= 50 ? AMBER_COLD : RED_COLD;
          return (
            <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "4px" }}>
              <div style={{ fontSize: "13px", fontFamily: "'JetBrains Mono', monospace", color, fontWeight: 500 }}>{d.pct}%</div>
              <div style={{ width: "20px", height: `${h}px`, background: `linear-gradient(180deg, ${color}, ${color}40)`, borderRadius: "2px 2px 0 0", animation: `barGrow 0.5s ease-out ${i * 0.08}s both`, transformOrigin: "bottom" }} />
              <span style={{ color: SLATE, fontFamily: "'JetBrains Mono', monospace", fontSize: "13px" }}>{d.day}</span>
            </div>
          );
        })}
      </div>
      {/* Summary */}
      <div style={{ display: "flex", justifyContent: "space-around", marginTop: "10px", paddingTop: "8px", borderTop: `1px solid ${GRID_LINE}` }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: FROST, fontFamily: "'JetBrains Mono', monospace", fontSize: "13px", fontWeight: 600 }}>
            {data.reduce((s, d) => s + d.resolved, 0)}
          </div>
          <div style={{ color: SLATE, fontFamily: "'JetBrains Mono', monospace", fontSize: "12px", letterSpacing: "1px", marginTop: "2px" }}>RESOLVED</div>
        </div>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: TEAL, fontFamily: "'JetBrains Mono', monospace", fontSize: "13px", fontWeight: 600 }}>
            {data.reduce((s, d) => s + d.correct, 0)}
          </div>
          <div style={{ color: SLATE, fontFamily: "'JetBrains Mono', monospace", fontSize: "12px", letterSpacing: "1px", marginTop: "2px" }}>CORRECT</div>
        </div>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: BLUE_BRIGHT, fontFamily: "'JetBrains Mono', monospace", fontSize: "13px", fontWeight: 600 }}>
            {Math.round(data.reduce((s, d) => s + d.correct, 0) / data.reduce((s, d) => s + d.resolved, 0) * 100)}%
          </div>
          <div style={{ color: SLATE, fontFamily: "'JetBrains Mono', monospace", fontSize: "12px", letterSpacing: "1px", marginTop: "2px" }}>7D AVG</div>
        </div>
      </div>
    </div>
  );
}

function BootSequence({ onComplete }) {
  const lines = [
    { text: "ORACLE SENTINEL v2.0", color: BLUE_BRIGHT },
    { text: "Polymarket Prediction Intelligence System", color: FROST },
    { text: "─────────────────────────────────────────", color: BORDER_LIGHT },
    { text: "> Initializing prediction engine...", color: SLATE },
    { text: "> Loading market data from Polymarket API...", color: SLATE },
    { text: "> Connecting to OpenRouter AI backend...", color: SLATE },
    { text: "> Mounting accuracy tracker...", color: SLATE },
    { text: "> Establishing Telegram channel...", color: SLATE },
    { text: "> Loading tracked predictions...", color: SLATE },
    { text: "> Verifying cron daemon (4h interval)...", color: SLATE },
    { text: "─────────────────────────────────────────", color: BORDER_LIGHT },
    { text: "✓ ALL SYSTEMS OPERATIONAL", color: TEAL },
  ];
  const [currentLine, setCurrentLine] = useState(0);
  const [displayedLines, setDisplayedLines] = useState([]);
  useEffect(() => {
    if (currentLine >= lines.length) { setTimeout(onComplete, 600); return; }
    const delay = currentLine === lines.length - 1 ? 500 : 100 + Math.random() * 180;
    const timer = setTimeout(() => { setDisplayedLines(prev => [...prev, lines[currentLine]]); setCurrentLine(prev => prev + 1); }, delay);
    return () => clearTimeout(timer);
  }, [currentLine]);
  return (
    <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: BG, display: "flex", alignItems: "center", justifyContent: "center", zIndex: 10000 }}>
      <div style={{ width: "480px" }}>
        {displayedLines.map((line, i) => (
          <div key={i} style={{ color: line.color, fontFamily: "'JetBrains Mono', monospace", fontSize: i < 2 ? "14px" : "12px", fontWeight: i === 0 ? 700 : i === 1 ? 500 : 400, lineHeight: "24px", animation: "fadeInUp 0.2s ease-out" }}>{line.text}</div>
        ))}
        {currentLine < lines.length && <Cursor />}
      </div>
    </div>
  );
}

function ColHeaders({ columns }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: columns.map(c => c.w).join(" "), gap: "8px", padding: "6px 10px", fontSize: "13px", color: SLATE, letterSpacing: "1px", fontWeight: 500, borderBottom: `1px solid ${BORDER}`, fontFamily: "'JetBrains Mono', monospace" }}>
      {columns.map(c => <span key={c.l} style={{ textAlign: c.a || "left" }}>{c.l}</span>)}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// AI AGENT CHAT COMPONENT
// ═══════════════════════════════════════════════════════════════
function AIAgentChat() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch(API_BASE + "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage,
          history: messages
        })
      });

      const data = await response.json();
      
      if (data.error) {
        setMessages(prev => [...prev, { role: "assistant", content: `Error: ${data.error}`, isError: true }]);
      } else {
        setMessages(prev => [...prev, { role: "assistant", content: data.response }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: "assistant", content: "Failed to connect to AI agent. Please try again.", isError: true }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Floating button when closed
  if (!isOpen) {
    return (
      <div
        onClick={() => setIsOpen(true)}
        style={{
          position: "fixed",
          bottom: "50px",
          right: "20px",
          width: "56px",
          height: "56px",
          borderRadius: "50%",
          background: `linear-gradient(135deg, ${BLUE_MID}, ${BLUE_DARK})`,
          border: `2px solid ${BLUE_BRIGHT}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          boxShadow: `0 4px 20px ${BLUE_DARK}80`,
          transition: "all 0.3s ease",
          zIndex: 9998,
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = "scale(1.1)";
          e.currentTarget.style.boxShadow = `0 6px 30px ${BLUE_BRIGHT}60`;
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = "scale(1)";
          e.currentTarget.style.boxShadow = `0 4px 20px ${BLUE_DARK}80`;
        }}
      >
        <span style={{ fontSize: "24px" }}>🤖</span>
      </div>
    );
  }

  // Chat box when open
  return (
    <div style={{
      position: "fixed",
      bottom: "50px",
      right: "20px",
      width: "400px",
      height: "500px",
      background: BG_PANEL,
      border: `1px solid ${BORDER_LIGHT}`,
      borderRadius: "8px",
      display: "flex",
      flexDirection: "column",
      boxShadow: `0 8px 32px ${BG}`,
      zIndex: 9998,
      overflow: "hidden",
    }}>
      {/* Header */}
      <div style={{
        background: `linear-gradient(90deg, ${BLUE_DARK}, ${BG_PANEL})`,
        padding: "12px 16px",
        borderBottom: `1px solid ${BORDER}`,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "20px" }}>🤖</span>
          <div>
            <div style={{ color: BLUE_BRIGHT, fontFamily: "'JetBrains Mono', monospace", fontSize: "12px", fontWeight: 600, letterSpacing: "1px" }}>AI AGENT</div>
            <div style={{ color: SLATE, fontFamily: "'JetBrains Mono', monospace", fontSize: "13px" }}>Prediction Market Analyst</div>
          </div>
        </div>
        <div
          onClick={() => setIsOpen(false)}
          style={{
            color: SLATE,
            cursor: "pointer",
            fontSize: "18px",
            padding: "4px 8px",
            borderRadius: "4px",
            transition: "all 0.2s",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.color = RED_COLD; e.currentTarget.style.background = `${RED_COLD}20`; }}
          onMouseLeave={(e) => { e.currentTarget.style.color = SLATE; e.currentTarget.style.background = "transparent"; }}
        >
          ✕
        </div>
      </div>

      {/* Messages */}
      <div style={{
        flex: 1,
        overflowY: "auto",
        padding: "12px",
        display: "flex",
        flexDirection: "column",
        gap: "12px",
      }}>
        {messages.length === 0 && (
          <div style={{ color: SLATE, fontFamily: "'JetBrains Mono', monospace", fontSize: "13px", textAlign: "center", padding: "40px 20px" }}>
            <div style={{ fontSize: "32px", marginBottom: "12px" }}>🤖</div>
            <div style={{ color: FROST, marginBottom: "8px" }}>Oracle Sentinel AI Agent</div>
            <div style={{ lineHeight: "1.6" }}>
              Analyze any Polymarket with:<br />
              <span style={{ color: TEAL }}>"Analyze this market and check the resolution rules carefully: [URL]"</span>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} style={{
            alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
            maxWidth: "85%",
          }}>
            <div style={{
              background: msg.role === "user" ? BLUE_DARK : BG,
              border: `1px solid ${msg.isError ? RED_COLD : (msg.role === "user" ? BLUE_MID : BORDER)}`,
              borderRadius: msg.role === "user" ? "12px 12px 4px 12px" : "12px 12px 12px 4px",
              padding: "10px 14px",
              color: msg.isError ? RED_COLD : ICE,
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: "13px",
              lineHeight: "1.6",
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}>
              {msg.content}
            </div>
            <div style={{
              color: SLATE,
              fontSize: "13px",
              fontFamily: "'JetBrains Mono', monospace",
              marginTop: "4px",
              textAlign: msg.role === "user" ? "right" : "left",
            }}>
              {msg.role === "user" ? "You" : "AI Agent"}
            </div>
          </div>
        ))}
        {isLoading && (
          <div style={{ alignSelf: "flex-start", maxWidth: "85%" }}>
            <div style={{
              background: BG,
              border: `1px solid ${BORDER}`,
              borderRadius: "12px 12px 12px 4px",
              padding: "10px 14px",
              color: FROST,
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: "13px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}>
              <span style={{ animation: "pulse 1s infinite" }}>●</span>
              Analyzing...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{
        padding: "12px",
        borderTop: `1px solid ${BORDER}`,
        background: BG,
      }}>
        <div style={{ display: "flex", gap: "8px" }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about any Polymarket..."
            disabled={isLoading}
            style={{
              flex: 1,
              background: BG_PANEL,
              border: `1px solid ${BORDER_LIGHT}`,
              borderRadius: "6px",
              padding: "10px 12px",
              color: ICE,
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: "13px",
              resize: "none",
              height: "40px",
              outline: "none",
            }}
            onFocus={(e) => { e.target.style.borderColor = BLUE_MID; }}
            onBlur={(e) => { e.target.style.borderColor = BORDER_LIGHT; }}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            style={{
              background: isLoading || !input.trim() ? BORDER : `linear-gradient(135deg, ${BLUE_MID}, ${BLUE_DIM})`,
              border: "none",
              borderRadius: "6px",
              padding: "0 16px",
              color: isLoading || !input.trim() ? SLATE : ICE,
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: "13px",
              fontWeight: 600,
              cursor: isLoading || !input.trim() ? "not-allowed" : "pointer",
              transition: "all 0.2s",
            }}
          >
            {isLoading ? "..." : "SEND"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// AI AGENT PANEL (Full Page Version)
// ═══════════════════════════════════════════════════════════════
function AIAgentPanel() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;
    const userMessage = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);
    try {
      const response = await fetch(API_BASE + "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, history: messages })
      });
      const data = await response.json();
      if (data.error) {
        setMessages(prev => [...prev, { role: "assistant", content: `Error: ${data.error}`, isError: true }]);
      } else {
        setMessages(prev => [...prev, { role: "assistant", content: data.response }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: "assistant", content: "Failed to connect to AI agent. Please try again.", isError: true }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 320px)" }}>
      <div style={{ flex: 1, overflowY: "auto", padding: "12px", display: "flex", flexDirection: "column", gap: "12px", background: BG, borderRadius: "4px", marginBottom: "12px" }}>
        {messages.length === 0 && (
          <div style={{ color: SLATE, fontFamily: "'JetBrains Mono', monospace", fontSize: "13px", textAlign: "center", padding: "60px 20px" }}>
            <div style={{ fontSize: "48px", marginBottom: "16px" }}>🤖</div>
            <div style={{ color: FROST, marginBottom: "12px", fontSize: "14px" }}>Oracle Sentinel AI Agent</div>
            <div style={{ lineHeight: "1.8", maxWidth: "500px", margin: "0 auto" }}>
              Analyze any Polymarket with:<br />
              <span style={{ color: TEAL }}>"Analyze this market: [URL]"</span><br /><br />
              Or ask questions like:<br />
              <span style={{ color: AMBER_COLD }}>"What are the current signals?"</span><br />
              <span style={{ color: AMBER_COLD }}>"Show me accuracy stats"</span>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} style={{ alignSelf: msg.role === "user" ? "flex-end" : "flex-start", maxWidth: "75%" }}>
            <div style={{ background: msg.role === "user" ? BLUE_DARK : BG_PANEL, border: `1px solid ${msg.isError ? RED_COLD : (msg.role === "user" ? BLUE_MID : BORDER)}`, borderRadius: msg.role === "user" ? "12px 12px 4px 12px" : "12px 12px 12px 4px", padding: "12px 16px", color: msg.isError ? RED_COLD : ICE, fontFamily: "'JetBrains Mono', monospace", fontSize: "12px", lineHeight: "1.7", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
              {msg.content}
            </div>
            <div style={{ color: SLATE, fontSize: "13px", fontFamily: "'JetBrains Mono', monospace", marginTop: "4px", textAlign: msg.role === "user" ? "right" : "left" }}>
              {msg.role === "user" ? "You" : "AI Agent"}
            </div>
          </div>
        ))}
        {isLoading && (
          <div style={{ alignSelf: "flex-start", maxWidth: "75%" }}>
            <div style={{ background: BG_PANEL, border: `1px solid ${BORDER}`, borderRadius: "12px 12px 12px 4px", padding: "12px 16px", color: FROST, fontFamily: "'JetBrains Mono', monospace", fontSize: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ animation: "pulse 1s infinite" }}>●</span>Analyzing...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div style={{ display: "flex", gap: "10px" }}>
        <textarea value={input} onChange={(e) => setInput(e.target.value)} onKeyPress={handleKeyPress} placeholder="Ask about any Polymarket or paste a URL to analyze..." disabled={isLoading} style={{ flex: 1, background: BG, border: `1px solid ${BORDER_LIGHT}`, borderRadius: "6px", padding: "12px 14px", color: ICE, fontFamily: "'JetBrains Mono', monospace", fontSize: "12px", resize: "none", height: "50px", outline: "none" }} onFocus={(e) => { e.target.style.borderColor = BLUE_MID; }} onBlur={(e) => { e.target.style.borderColor = BORDER_LIGHT; }} />
        <button onClick={sendMessage} disabled={isLoading || !input.trim()} style={{ background: isLoading || !input.trim() ? BORDER : `linear-gradient(135deg, ${BLUE_MID}, ${BLUE_DIM})`, border: "none", borderRadius: "6px", padding: "0 24px", color: isLoading || !input.trim() ? SLATE : ICE, fontFamily: "'JetBrains Mono', monospace", fontSize: "12px", fontWeight: 600, cursor: isLoading || !input.trim() ? "not-allowed" : "pointer", transition: "all 0.2s" }}>
          {isLoading ? "..." : "SEND"}
        </button>
      </div>
    </div>
  );
}

export default function OracleSentinelDashboard() {
  const [booted, setBooted] = useState(false);
  const [activeTab, setActiveTab] = useState("signals");
  const [data, setData] = useState(null);
  const [apiOk, setApiOk] = useState(false);
  const [streamLogs, setStreamLogs] = useState([]);
  const [sseOk, setSseOk] = useState(false);
  const [whaleData, setWhaleData] = useState(null);
  const [selectedSignal, setSelectedSignal] = useState(null);
  const [signalDetail, setSignalDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const logEndRef = useRef(null);

  useEffect(() => {
    if (!booted) return;
    const load = async () => {
      try {
        const res = await fetch(API_BASE + "/dashboard");
        if (!res.ok) throw new Error("API error");
        const json = await res.json();
        setData(json);
        setApiOk(true);
      } catch (e) {
        setApiOk(false);
      }
    };
    load();
    const iv = setInterval(load, 30000);
    return () => clearInterval(iv);
  }, [booted]);

  // Fetch whale data
  useEffect(() => {
    if (!booted) return;
    const loadWhales = async () => {
      try {
        const res = await fetch(API_BASE + "/whales");
        if (res.ok) {
          const json = await res.json();
          setWhaleData(json);
        }
      } catch (e) {}
    };
    loadWhales();
    const iv = setInterval(loadWhales, 60000);
    return () => clearInterval(iv);
  }, [booted]);

  // ─── SSE: Real-time log streaming ───
  useEffect(() => {
    if (!booted) return;
    let es;
    const connect = () => {
      es = new EventSource(API_BASE + "/logs/stream");
      es.onopen = () => setSseOk(true);
      es.onmessage = (e) => {
        try {
          const log = JSON.parse(e.data);
          if (log.error) return;
          setStreamLogs(prev => {
            const next = [...prev, log];
            return next.length > 500 ? next.slice(-500) : next;
          });
        } catch(err) {}
      };
      es.onerror = () => {
        setSseOk(false);
        es.close();
        setTimeout(connect, 5000);
      };
    };
    connect();
    return () => { if (es) es.close(); };
  }, [booted]);

  useEffect(() => {
    if (logEndRef.current) logEndRef.current.scrollIntoView({ behavior: "smooth" });
  }, [streamLogs]);

  if (!booted) return <><Styles /><Scanlines /><BootSequence onComplete={() => setBooted(true)} /></>;

  // Extract data
  const stats = data?.stats || {};
  const acc = data?.accuracy_stats || {};
  const rawSignals = (data?.active_signals || []);
  const signals = (() => {
    const seen = new Map();
    for (const s of rawSignals) {
      const key = s.market_id || s.question;
      const existing = seen.get(key);
      if (!existing) {
        seen.set(key, s);
      } else if (s.signal_type !== existing.signal_type) {
        // Signal changed on same market — keep both
        seen.set(key + "_" + s.signal_type, s);
      } else if ((s.created_at || "") > (existing.created_at || "")) {
        seen.set(key, s);
      }
    }
    return Array.from(seen.values());
  })();
  const markets = (data?.markets || []);
  const predictions = (data?.predictions || []);
  const logs = (data?.system_logs || []);

  // Compute confidence breakdown from predictions
  const highConf = predictions.filter(p => p.confidence === "HIGH");
  const medConf = predictions.filter(p => p.confidence === "MEDIUM");
  const highResolved = highConf.filter(p => p.direction_correct !== null);
  const medResolved = medConf.filter(p => p.direction_correct !== null);
  const highCorrect = highConf.filter(p => p.direction_correct === 1);
  const medCorrect = medConf.filter(p => p.direction_correct === 1);

  return (
    <div style={{ background: BG, minHeight: "100vh", color: FROST, fontFamily: "'JetBrains Mono', monospace", paddingBottom: "36px" }}>
      <Styles /><Scanlines />
      <Header />
      <StatusBar scanCount={stats.total_signals || 0} nextScan={timeAgo(stats.last_scan)} uptime={apiOk ? "LIVE" : "OFFLINE"} />

      {/* Top Metrics */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "1px", background: BORDER, borderBottom: `1px solid ${BORDER}` }}>
        {[
          { label: "Markets", value: stats.total_markets || 0, color: BLUE_BRIGHT },
          { label: "Signals", value: signals.length, color: TEAL },
          { label: "Accuracy", value: acc.accuracy_pct ? acc.accuracy_pct : "—", suffix: acc.accuracy_pct ? "%" : "", color: TEAL },
          { label: "Predictions", value: acc.total || 0, color: BLUE_BRIGHT },
          { label: "Resolved", value: acc.resolved || 0, color: AMBER_COLD },
        ].map(m => <div key={m.label} style={{ background: BG_PANEL, padding: "14px 8px" }}><Metric label={m.label} value={m.value} suffix={m.suffix || ""} color={m.color} size="18px" /></div>)}
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", borderBottom: `1px solid ${BORDER}`, background: BG_PANEL }}>
        {["signals", "markets", "accuracy", "log", "whales", "ai agent"].map(t => (
          <button key={t} className={`tab-btn ${activeTab === t ? "active" : ""} ${t === "ai agent" ? "ai-agent-tab" : ""}`} onClick={() => setActiveTab(t)}>{t.toUpperCase()}</button>
        ))}
        <div style={{ marginLeft: "auto", padding: "10px 20px", fontSize: "12px", color: SLATE, display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ color: apiOk ? TEAL : RED_COLD, animation: "pulse 2s infinite", fontSize: "12px" }}>●</span>{apiOk ? "LIVE" : "OFFLINE"}
        </div>
      </div>

      <div style={{ padding: "14px" }}>

        {/* ── SIGNALS ── */}
        {activeTab === "signals" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: "14px" }}>
            <Panel title="PREDICTION SIGNALS" headerRight={<span style={{ color: SLATE, fontSize: "12px", fontFamily: "'JetBrains Mono', monospace" }}>{predictions.length} tracked</span>}>
              <ColHeaders columns={[{l:"SIGNAL",w:"60px"},{l:"MARKET",w:"1fr"},{l:"EDGE",w:"60px",a:"right"},{l:"CONF",w:"60px",a:"center"},{l:"STATUS",w:"80px",a:"right"}]} />
              {predictions.length === 0 ? (
                <div style={{ textAlign: "center", padding: "30px 0", color: SLATE, fontSize: "13px" }}>No predictions tracked yet. Scanning every 4 hours.</div>
              ) : (
                predictions.map((p, i) => {
                  const status = p.direction_correct === 1 ? { color: TEAL, label: "CORRECT" } 
                               : p.direction_correct === 0 ? { color: RED_COLD, label: "WRONG" } 
                               : { color: AMBER_COLD, label: "TRACKING" };
                  return (
                    <div key={p.id || i} className="row-hover" onClick={() => {
                      setSelectedSignal({ question: p.question, signal_type: p.signal_type, edge: p.edge_at_signal, confidence: p.confidence, reasoning: "" });
                      if (p.opportunity_id) {
                        setDetailLoading(true);
                        fetch(API_BASE + "/prediction/" + p.opportunity_id)
                          .then(r => r.json())
                          .then(d => { setSignalDetail(d); setDetailLoading(false); })
                          .catch(() => { setSignalDetail(null); setDetailLoading(false); });
                      } else {
                        setSignalDetail(null);
                      }
                    }} style={{ display: "grid", gridTemplateColumns: "60px 1fr 60px 60px 80px", gap: "8px", alignItems: "center", padding: "7px 10px", fontSize: "13px", fontFamily: "'JetBrains Mono', monospace", borderBottom: `1px solid ${GRID_LINE}`, animation: `fadeInUp 0.3s ease-out ${i * 0.04}s both`, cursor: "pointer" }}>
                      <span style={{ color: p.signal_type === "BUY_YES" ? TEAL : RED_COLD, fontWeight: 600, fontSize: "12px" }}>{p.signal_type === "BUY_YES" ? "▲ YES" : "▼ NO"}</span>
                      <span style={{ color: ICE, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.question}</span>
                      <span style={{ color: FROST, textAlign: "right", fontWeight: 500 }}>{p.edge_at_signal}%</span>
                      <span style={{ color: p.confidence === "HIGH" ? BLUE_BRIGHT : AMBER_COLD, textAlign: "center", fontSize: "13px", fontWeight: 500 }}>{p.confidence || "—"}</span>
                      <span style={{ color: status.color, textAlign: "right", fontSize: "13px", fontWeight: 500 }}>{status.label}</span>
                    </div>
                  );
                })
              )}
            </Panel>
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <Panel title="DISTRIBUTION">
                <div style={{ display: "flex", justifyContent: "space-around", padding: "12px 0" }}>
                  {[{ label: "BUY_YES", value: acc.buy_yes || 0, color: TEAL }, { label: "BUY_NO", value: acc.buy_no || 0, color: RED_COLD }].map(d => (
                    <div key={d.label} style={{ textAlign: "center" }}>
                      <div style={{ width: "52px", height: "52px", borderRadius: "50%", border: `2px solid ${d.color}50`, display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 8px" }}>
                        <span style={{ color: d.color, fontSize: "18px", fontWeight: 700, fontFamily: "'JetBrains Mono', monospace" }}>{d.value}</span>
                      </div>
                      <span style={{ color: SLATE, fontSize: "13px", letterSpacing: "0.5px", fontFamily: "'JetBrains Mono', monospace" }}>{d.label}</span>
                    </div>
                  ))}
                </div>
              </Panel>
              <Panel title="ACCURACY">
                <AccuracyGauge accuracy={acc.accuracy_pct || 0} />
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginTop: "12px" }}>
                  <Metric label="Resolved" value={acc.resolved || 0} color={AMBER_COLD} size="14px" />
                  <Metric label="Correct" value={acc.correct || 0} color={TEAL} size="14px" />
                </div>
              </Panel>
              <Panel title="SYSTEM">
                <div style={{ display: "flex", flexDirection: "column", gap: "7px", fontSize: "13px" }}>
                  {[
                    { l: "Polymarket API", s: apiOk ? "CONNECTED" : "OFFLINE", c: apiOk ? TEAL : RED_COLD },
                    { l: "OpenRouter AI", s: "CONNECTED", c: TEAL },
                    { l: "Telegram Bot", s: "CONNECTED", c: TEAL },
                    { l: "Cron Daemon", s: "4H CYCLE", c: TEAL },
                    { l: "Last Scan", s: timeAgo(stats.last_scan), c: AMBER_COLD },
                  ].map(x => <div key={x.l} style={{ display: "flex", justifyContent: "space-between" }}><span style={{ color: SLATE }}>{x.l}</span><span style={{ color: x.c, fontSize: "12px", fontWeight: 500 }}>{x.s}</span></div>)}
                </div>
              </Panel>
              <Panel title="HOW TO USE">
                <div style={{ color: FROST, fontSize: "12px", lineHeight: "1.7", fontFamily: "'JetBrains Mono', monospace" }}>
                  <div style={{ color: BLUE_BRIGHT, fontWeight: 600, marginBottom: "8px" }}>DASHBOARD GUIDE</div>
                  <div style={{ marginBottom: "6px" }}><span style={{ color: TEAL }}>SIGNALS</span> — AI-generated signals with rigorous multi-factor analysis.</div>
                  <div style={{ marginBottom: "6px" }}><span style={{ color: TEAL }}>MARKETS</span> — Browse tracked Polymarket markets with real-time prices.</div>
                  <div style={{ marginBottom: "6px" }}><span style={{ color: TEAL }}>ACCURACY</span> — Monitor prediction performance and win rate.</div>
                  <div style={{ marginBottom: "6px" }}><span style={{ color: TEAL }}>WHALES</span> — Track large trades ($5K+) from whales.</div>
                  <div style={{ marginBottom: "6px" }}><span style={{ color: TEAL }}>AI AGENT</span> — Ask for instant analysis of any Polymarket URL.</div>
                  <div style={{ color: AMBER_COLD, fontSize: "13px", marginTop: "8px", padding: "8px", background: BG, borderRadius: "4px" }}>💡 Can't find your market? Use the AI Agent tab for instant analysis.</div>
                </div>
              </Panel>
            </div>
          </div>
        )}

        {/* ── MARKETS ── */}
        {activeTab === "markets" && (
          <Panel title="MARKET WATCHLIST" headerRight={<span style={{ color: SLATE, fontSize: "12px", fontFamily: "'JetBrains Mono', monospace" }}>{markets.length} monitored</span>}>
            <ColHeaders columns={[{l:"MARKET",w:"1fr"},{l:"YES",w:"60px",a:"right"},{l:"NO",w:"60px",a:"right"},{l:"VOLUME",w:"80px",a:"right"},{l:"LIQUIDITY",w:"80px",a:"right"}]} />
            {markets.map((m, i) => (
              <div key={m.id} className="row-hover" style={{ display: "grid", gridTemplateColumns: "1fr 60px 60px 80px 80px", gap: "8px", alignItems: "center", padding: "8px 10px", fontSize: "13px", fontFamily: "'JetBrains Mono', monospace", borderBottom: `1px solid ${GRID_LINE}`, animation: `fadeInUp 0.3s ease-out ${i * 0.03}s both` }}>
                <span style={{ color: ICE, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{m.question}</span>
                <span style={{ color: TEAL, textAlign: "right", fontWeight: 500 }}>{(m.yes_price * 100).toFixed(1)}¢</span>
                <span style={{ color: RED_COLD, textAlign: "right", fontWeight: 500 }}>{(m.no_price * 100).toFixed(1)}¢</span>
                <span style={{ color: FROST, textAlign: "right" }}>${formatNum(m.volume)}</span>
                <span style={{ color: SLATE, textAlign: "right" }}>${formatNum(m.liquidity)}</span>
              </div>
            ))}
          </Panel>
        )}

        {/* ── ACCURACY ── */}
        {activeTab === "accuracy" && (
          <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: "14px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <Panel title="PREDICTION ACCURACY">
                <AccuracyGauge accuracy={acc.accuracy_pct || 0} />
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", marginTop: "16px" }}>
                  <Metric label="Resolved" value={acc.resolved || 0} color={AMBER_COLD} size="16px" />
                  <Metric label="Correct" value={acc.correct || 0} color={TEAL} size="16px" />
                  <Metric label="Avg Edge" value={acc.avg_edge || "—"} suffix={acc.avg_edge ? "%" : ""} color={BLUE_BRIGHT} size="14px" />
                  <Metric label="Total" value={acc.total || 0} color={FROST} size="14px" />
                </div>
              </Panel>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <Panel title="CONFIDENCE BREAKDOWN">
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  {[
                    { label: "HIGH CONFIDENCE", total: highConf.length, resolved: highResolved.length, correct: highCorrect.length, accuracy: highResolved.length > 0 ? Math.round(highCorrect.length / highResolved.length * 100) : 0, color: BLUE_BRIGHT },
                    { label: "MEDIUM CONFIDENCE", total: medConf.length, resolved: medResolved.length, correct: medCorrect.length, accuracy: medResolved.length > 0 ? Math.round(medCorrect.length / medResolved.length * 100) : 0, color: AMBER_COLD },
                  ].map(d => (
                    <div key={d.label} style={{ fontSize: "13px", marginBottom: "16px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                        <span style={{ color: d.color, fontSize: "12px", fontWeight: 500, letterSpacing: "0.5px" }}>{d.label}</span>
                        <span style={{ color: SLATE, fontSize: "12px" }}>{d.correct}/{d.resolved} of {d.total}</span>
                      </div>
                      <ProgressBar value={d.resolved > 0 ? d.accuracy : 0} color={d.color} />
                      <div style={{ display: "flex", justifyContent: "space-between", marginTop: "6px" }}>
                        <span style={{ color: SLATE, fontSize: "13px" }}>
                          {d.resolved > 0 ? `${d.correct} correct, ${d.resolved - d.correct} wrong` : "No resolved predictions yet"}
                        </span>
                        <span style={{ color: d.color, fontSize: "13px", fontWeight: 600 }}>
                          {d.resolved > 0 ? d.accuracy + "%" : "—"}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </Panel>
              <Panel title="PREDICTION HISTORY">
                {predictions.length === 0 ? (
                  <div style={{ color: SLATE, textAlign: "center", padding: "20px 0", fontSize: "13px" }}>No predictions tracked yet</div>
                ) : predictions.map((p, i) => {
                  const change1h = p.price_after_1h && p.market_price_at_signal ? ((p.price_after_1h - p.market_price_at_signal) * 100).toFixed(1) : null;
                  return (
                    <div key={i} className="row-hover" style={{ display: "flex", justifyContent: "space-between", padding: "7px 6px", borderBottom: `1px solid ${GRID_LINE}`, animation: `fadeInUp 0.3s ease-out ${i * 0.06}s both`, fontSize: "13px", fontFamily: "'JetBrains Mono', monospace" }}>
                      <span style={{ color: p.signal_type === "BUY_YES" ? TEAL : RED_COLD, width: "50px", fontWeight: 600, fontSize: "13px" }}>{p.signal_type === "BUY_YES" ? "▲ YES" : "▼ NO"}</span>
                      <span style={{ color: ICE, flex: 1, margin: "0 8px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.question}</span>
                      <span style={{ color: FROST, width: "50px", textAlign: "right" }}>{p.edge_at_signal}%</span>
                      <span style={{ color: FROST, width: "50px", textAlign: "right" }}>{(p.market_price_at_signal * 100).toFixed(1)}¢</span>
                      <span style={{ color: change1h === null ? SLATE : (parseFloat(change1h) > 0 ? TEAL : RED_COLD), width: "56px", textAlign: "right", fontWeight: 500 }}>{change1h !== null ? (parseFloat(change1h) > 0 ? "+" : "") + change1h + "¢" : "pending"}</span>
                    </div>
                  );
                })}
              </Panel>
              <Panel title="STATS">
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px" }}>
                  <Metric label="Total" value={acc.total || 0} color={BLUE_BRIGHT} size="22px" />
                  <Metric label="BUY_YES" value={acc.buy_yes || 0} color={TEAL} size="22px" />
                  <Metric label="BUY_NO" value={acc.buy_no || 0} color={RED_COLD} size="22px" />
                </div>
              </Panel>
            </div>
          </div>
        )}

        {/* ── LOG ── */}
        {activeTab === "log" && (
          <Panel title="SYSTEM LOG" headerRight={<span style={{ color: sseOk ? TEAL : AMBER_COLD, fontSize: "12px", fontFamily: "'JetBrains Mono', monospace", display: "flex", alignItems: "center", gap: "6px" }}><span style={{ animation: "pulse 1.5s infinite", fontSize: "12px" }}>●</span>{sseOk ? "STREAMING" : "CONNECTING..."}</span>}>
            <div style={{ maxHeight: "calc(100vh - 300px)", overflowY: "auto", fontFamily: "'JetBrains Mono', monospace", fontSize: "13px" }}>
              {streamLogs.length === 0 ? (
                <div style={{ color: SLATE, textAlign: "center", padding: "30px 0" }}>Connecting to log stream...</div>
              ) : streamLogs.map((l, i) => {
                const levelColor = l.level === "ERROR" ? RED_COLD : l.level === "WARNING" ? AMBER_COLD : SLATE;
                return (
                  <div key={l.id || i} style={{ padding: "3px 0", borderBottom: `1px solid ${GRID_LINE}`, lineHeight: "18px" }}>
                    <span style={{ color: BLUE_DIM, marginRight: "8px" }}>{(l.timestamp || "").split(" ")[1] || ""}</span>
                    <span style={{ color: levelColor, marginRight: "8px", fontWeight: 600, display: "inline-block", width: "42px" }}>{l.level}</span>
                    <span style={{ color: FROST, marginRight: "8px" }}>[{l.component}]</span>
                    <span style={{ color: ICE }}>{l.message}</span>
                  </div>
                );
              })}
              <div ref={logEndRef} />
            </div>
          </Panel>
        )}

        {/* ── WHALES ── */}
        {activeTab === "whales" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: "14px" }}>
            <Panel title="RECENT WHALE TRADES" headerRight={<span style={{ color: SLATE, fontSize: "12px", fontFamily: "'JetBrains Mono', monospace" }}>{whaleData?.trades?.length || 0} trades</span>}>
              <ColHeaders columns={[{l:"TIME",w:"70px"},{l:"MARKET",w:"1fr"},{l:"SIDE",w:"50px",a:"center"},{l:"OUTCOME",w:"60px",a:"center"},{l:"SIZE",w:"80px",a:"right"},{l:"PRICE",w:"50px",a:"right"},{l:"TRADER",w:"90px",a:"right"},{l:"TX",w:"30px",a:"right"}]} />
              <div style={{ maxHeight: "calc(100vh - 340px)", overflowY: "auto" }}>
                {!whaleData?.trades?.length ? (
                  <div style={{ textAlign: "center", padding: "30px 0", color: SLATE, fontSize: "13px" }}>No whale trades detected yet.</div>
                ) : (
                  whaleData.trades.map((t, i) => (
                    <div key={t.tx_hash} className="row-hover" style={{ display: "grid", gridTemplateColumns: "70px 1fr 50px 60px 80px 50px 90px 30px", gap: "8px", alignItems: "center", padding: "7px 10px", fontSize: "13px", fontFamily: "'JetBrains Mono', monospace", borderBottom: `1px solid ${GRID_LINE}`, animation: `fadeInUp 0.3s ease-out ${i * 0.03}s both` }}>
                      <span style={{ color: SLATE, fontSize: "12px" }}>{(t.time || "").split(" ")[1]?.slice(0,5) || "—"}</span>
                      <span style={{ color: ICE, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{t.market}</span>
                      <span style={{ color: t.side === "BUY" ? TEAL : RED_COLD, fontWeight: 600, textAlign: "center", fontSize: "12px" }}>{t.side}</span>
                      <span style={{ color: FROST, textAlign: "center", fontSize: "12px" }}>{t.outcome}</span>
                      <span style={{ color: t.size >= 20000 ? AMBER_COLD : FROST, textAlign: "right", fontWeight: 500 }}>${formatNum(t.size)}</span>
                      <span style={{ color: FROST, textAlign: "right" }}>{(t.price * 100).toFixed(0)}¢</span>
                      <span style={{ color: SLATE, textAlign: "right", fontSize: "13px", overflow: "hidden", textOverflow: "ellipsis" }}>{t.trader?.slice(0,10)}</span>
                      <a href={`https://polygonscan.com/tx/${t.tx_hash}`} target="_blank" rel="noopener noreferrer" style={{ color: BLUE_DIM, textAlign: "right", fontSize: "13px", textDecoration: "none" }}>🔗</a>
                    </div>
                  ))
                )}
              </div>
            </Panel>
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <Panel title="24H STATS">
                <div style={{ display: "flex", flexDirection: "column", gap: "14px", padding: "8px 0" }}>
                  <Metric label="Total Trades" value={whaleData?.stats?.total_trades || 0} color={BLUE_BRIGHT} size="18px" />
                  <Metric label="Volume" value={formatNum(whaleData?.stats?.total_volume || 0)} color={TEAL} size="18px" />
                  <Metric label="Avg Size" value={formatNum(whaleData?.stats?.avg_size || 0)} color={FROST} size="16px" />
                </div>
              </Panel>
          
              <Panel title="TOP MARKETS (24H)">
                <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "13px", fontFamily: "'JetBrains Mono', monospace" }}>
                  {!whaleData?.top_markets?.length ? (
                    <div style={{ color: SLATE, textAlign: "center", padding: "16px 0" }}>No data</div>
                  ) : whaleData.top_markets.map((m, i) => (
                    <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: `1px solid ${GRID_LINE}` }}>
                      <span style={{ color: ICE, flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", marginRight: "8px" }}>{m.market}</span>
                      <span style={{ color: TEAL, fontWeight: 500 }}>${formatNum(m.volume)}</span>
                    </div>
                  ))}
                </div>
              </Panel>
            </div>
          </div>
        )}

        {/* ── AI AGENT ── */}
        {activeTab === "ai agent" && (
          <Panel title="AI AGENT" headerRight={<span style={{ color: TEAL, fontSize: "12px", fontFamily: "'JetBrains Mono', monospace" }}>Prediction Market Analyst</span>}>
            <AIAgentPanel />
          </Panel>
        )}
      </div>

      {/* Signal Detail Modal */}
      {selectedSignal && (
        <div onClick={() => { setSelectedSignal(null); setSignalDetail(null); }} style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.75)", zIndex: 10000, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div onClick={(e) => e.stopPropagation()} style={{ background: BG_PANEL, border: `1px solid ${BORDER_LIGHT}`, borderRadius: "6px", width: "720px", maxHeight: "85vh", overflowY: "auto", fontFamily: "'JetBrains Mono', monospace" }}>
            {/* Modal Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", padding: "16px 20px", borderBottom: `1px solid ${BORDER}`, background: `linear-gradient(90deg, ${BLUE_DARK}30, transparent)` }}>
              <div style={{ flex: 1, marginRight: "16px" }}>
                <div style={{ color: ICE, fontSize: "13px", fontWeight: 600, lineHeight: "1.4" }}>{selectedSignal.question}</div>
                <div style={{ display: "flex", gap: "12px", marginTop: "8px" }}>
                  <span style={{ color: (signalDetail?.signal_type || selectedSignal.signal_type) === "BUY_YES" ? TEAL : RED_COLD, fontSize: "13px", fontWeight: 600 }}>{(signalDetail?.signal_type || selectedSignal.signal_type) === "BUY_YES" ? "▲ BUY YES" : "▼ BUY NO"}</span>
                  <span style={{ color: AMBER_COLD, fontSize: "12px" }}>EDGE: {signalDetail?.edge || selectedSignal.edge}%</span>
                  <span style={{ color: BLUE_BRIGHT, fontSize: "12px" }}>CONF: {signalDetail?.confidence || selectedSignal.confidence}</span>
                </div>
              </div>
              <div onClick={() => { setSelectedSignal(null); setSignalDetail(null); }} style={{ color: SLATE, cursor: "pointer", fontSize: "16px", padding: "2px 6px" }}>✕</div>
            </div>

            {detailLoading ? (
              <div style={{ padding: "40px", textAlign: "center", color: FROST, fontSize: "12px" }}>
                <span style={{ animation: "pulse 1s infinite" }}>●</span> Loading analysis...
              </div>
            ) : (
              <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: "16px" }}>
                {/* Market Data */}
                {signalDetail && (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "12px", padding: "12px", background: BG, borderRadius: "4px" }}>
                    <div style={{ textAlign: "center" }}>
                      <div style={{ color: TEAL, fontSize: "16px", fontWeight: 600 }}>{(signalDetail.market_yes_price * 100).toFixed(1)}¢</div>
                      <div style={{ color: SLATE, fontSize: "13px", marginTop: "2px" }}>YES PRICE</div>
                    </div>
                    <div style={{ textAlign: "center" }}>
                      <div style={{ color: RED_COLD, fontSize: "16px", fontWeight: 600 }}>{(signalDetail.market_no_price * 100).toFixed(1)}¢</div>
                      <div style={{ color: SLATE, fontSize: "13px", marginTop: "2px" }}>NO PRICE</div>
                    </div>
                    <div style={{ textAlign: "center" }}>
                      <div style={{ color: BLUE_BRIGHT, fontSize: "16px", fontWeight: 600 }}>{((signalDetail.ai_probability || 0) * 100).toFixed(0)}%</div>
                      <div style={{ color: SLATE, fontSize: "13px", marginTop: "2px" }}>AI ESTIMATE</div>
                    </div>
                    <div style={{ textAlign: "center" }}>
                      <div style={{ color: FROST, fontSize: "16px", fontWeight: 600 }}>${formatNum(signalDetail.volume || 0)}</div>
                      <div style={{ color: SLATE, fontSize: "13px", marginTop: "2px" }}>VOLUME</div>
                    </div>
                  </div>
                )}

                {/* AI Reasoning */}
                <div>
                  <div style={{ color: BLUE_BRIGHT, fontSize: "12px", fontWeight: 600, letterSpacing: "1px", marginBottom: "8px" }}>AI ANALYSIS</div>
                  <div style={{ color: FROST, fontSize: "13px", lineHeight: "1.7", whiteSpace: "pre-wrap", background: BG, padding: "12px", borderRadius: "4px", border: `1px solid ${GRID_LINE}` }}>
                    {signalDetail?.reasoning || selectedSignal.reasoning || "No reasoning available for this prediction."}
                  </div>
                </div>

                {/* Recommendation */}
                {signalDetail?.recommendation && (
                  <div>
                    <div style={{ color: TEAL, fontSize: "12px", fontWeight: 600, letterSpacing: "1px", marginBottom: "8px" }}>RECOMMENDATION</div>
                    <div style={{ color: ICE, fontSize: "13px", lineHeight: "1.6", background: BG, padding: "12px", borderRadius: "4px", border: `1px solid ${GRID_LINE}` }}>
                      {signalDetail.recommendation}
                    </div>
                  </div>
                )}

                {/* Key Factors */}
                {((signalDetail?.key_factors_for?.length > 0) || (signalDetail?.key_factors_against?.length > 0)) && (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    <div>
                      <div style={{ color: TEAL, fontSize: "12px", fontWeight: 600, letterSpacing: "1px", marginBottom: "8px" }}>FACTORS FOR</div>
                      <div style={{ background: BG, padding: "10px", borderRadius: "4px", border: `1px solid ${GRID_LINE}` }}>
                        {(signalDetail.key_factors_for || []).map((f, i) => (
                          <div key={i} style={{ color: FROST, fontSize: "12px", lineHeight: "1.6", padding: "3px 0" }}>+ {f}</div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <div style={{ color: RED_COLD, fontSize: "12px", fontWeight: 600, letterSpacing: "1px", marginBottom: "8px" }}>FACTORS AGAINST</div>
                      <div style={{ background: BG, padding: "10px", borderRadius: "4px", border: `1px solid ${GRID_LINE}` }}>
                        {(signalDetail.key_factors_against || []).map((f, i) => (
                          <div key={i} style={{ color: FROST, fontSize: "12px", lineHeight: "1.6", padding: "3px 0" }}>- {f}</div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Risks */}
                {signalDetail?.risks && (
                  <div>
                    <div style={{ color: AMBER_COLD, fontSize: "12px", fontWeight: 600, letterSpacing: "1px", marginBottom: "8px" }}>RISKS</div>
                    <div style={{ color: FROST, fontSize: "13px", lineHeight: "1.6", background: BG, padding: "12px", borderRadius: "4px", border: `1px solid ${GRID_LINE}` }}>
                      {signalDetail.risks}
                    </div>
                  </div>
                )}

                {/* Price Tracking */}
                {signalDetail?.tracking && (
                  <div>
                    <div style={{ color: BLUE_BRIGHT, fontSize: "12px", fontWeight: 600, letterSpacing: "1px", marginBottom: "8px" }}>PRICE TRACKING</div>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "8px" }}>
                      {[
                        { label: "At Signal", value: signalDetail.tracking.market_price_at_signal, color: FROST },
                        { label: "After 1H", value: signalDetail.tracking.price_after_1h, color: BLUE_MID },
                        { label: "After 6H", value: signalDetail.tracking.price_after_6h, color: BLUE_BRIGHT },
                        { label: "After 24H", value: signalDetail.tracking.price_after_24h, color: AMBER_COLD },
                        { label: "After 48H", value: signalDetail.tracking.price_after_48h, color: TEAL },
                      ].map(t => (
                        <div key={t.label} style={{ textAlign: "center", background: BG, padding: "8px", borderRadius: "4px" }}>
                          <div style={{ color: t.value ? t.color : SLATE, fontSize: "14px", fontWeight: 600 }}>
                            {t.value ? (t.value * 100).toFixed(1) + "¢" : "—"}
                          </div>
                          <div style={{ color: SLATE, fontSize: "12px", marginTop: "2px" }}>{t.label}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Whale Activity */}
                {signalDetail?.whales?.length > 0 && (
                  <div>
                    <div style={{ color: AMBER_COLD, fontSize: "12px", fontWeight: 600, letterSpacing: "1px", marginBottom: "8px" }}>WHALE ACTIVITY</div>
                    {signalDetail.whales.map((w, i) => (
                      <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "4px 8px", fontSize: "12px", borderBottom: `1px solid ${GRID_LINE}` }}>
                        <span style={{ color: w.trade_side === "BUY" ? TEAL : RED_COLD }}>{w.trade_side}</span>
                        <span style={{ color: FROST }}>${formatNum(w.trade_size)}</span>
                        <span style={{ color: SLATE }}>{w.trader_name?.slice(0,12)}</span>
                        <span style={{ color: SLATE }}>{(w.alerted_at || "").split(" ")[1]?.slice(0,5)}</span>
                      </div>
                    ))}
                  </div>
                )}


              </div>
            )}
          </div>
        </div>
      )}

      {/* Footer */}
      <div style={{ position: "fixed", bottom: 0, left: 0, right: 0, background: BG_PANEL, borderTop: `1px solid ${BORDER}`, padding: "5px 20px", display: "flex", justifyContent: "space-between", fontSize: "13px", color: SLATE }}>
        <span>ORACLE SENTINEL v2.0 — Claude Sonnet 4.5</span>
        <span style={{ display: "flex", gap: "16px" }}>
          <span>OpenClaw 2026.1.30</span><a href="https://x.com/oracle_sentinel" target="_blank" rel="noopener noreferrer" style={{ color: AMBER_COLD, textDecoration: "none" }}>$OSAI</a>
          <span style={{ color: apiOk ? TEAL : RED_COLD }}>{apiOk ? "API: connected" : "API: offline"}</span>
        </span>
      </div>
    </div>
  );
}
