import { useState, useEffect, useRef, useCallback } from "react";

// ═══════════════════════════════════════════════════════════════
// ORACLE SENTINEL — LANDING PAGE
// Cold Intelligence × Luxury Fintech Aesthetic
// ═══════════════════════════════════════════════════════════════

const C = {
  bg: "#050911", bg2: "#080d16", bgCard: "#0a1019", bgHover: "#0d1422",
  blue: "#4da6ff", blueM: "#2d7fd4", blueD: "#1a5a9e", blueDD: "#0d2847",
  ice: "#d0dff0", frost: "#8badc4", slate: "#5a7184", dim: "#3a4f60",
  red: "#e05565", teal: "#4ecdc4", amber: "#d4a843", green: "#5cb85c",
  border: "#121c2a", borderL: "#1a2a3e",
};

// ── Animated Grid Background ──
function GridBG() {
  const canvasRef = useRef(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let w, h, cols, rows, cellSize = 60;
    let pulses = [];
    let frame = 0;

    const resize = () => {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
      cols = Math.ceil(w / cellSize) + 1;
      rows = Math.ceil(h / cellSize) + 1;
    };
    resize();

    const addPulse = () => {
      pulses.push({
        x: Math.floor(Math.random() * cols) * cellSize,
        y: Math.floor(Math.random() * rows) * cellSize,
        age: 0, maxAge: 120, radius: 0,
      });
    };

    const draw = () => {
      ctx.clearRect(0, 0, w, h);

      // Static grid
      ctx.strokeStyle = "rgba(77,166,255,0.03)";
      ctx.lineWidth = 0.5;
      for (let x = 0; x <= cols; x++) {
        ctx.beginPath(); ctx.moveTo(x * cellSize, 0); ctx.lineTo(x * cellSize, h); ctx.stroke();
      }
      for (let y = 0; y <= rows; y++) {
        ctx.beginPath(); ctx.moveTo(0, y * cellSize); ctx.lineTo(w, y * cellSize); ctx.stroke();
      }

      // Intersection dots
      for (let x = 0; x <= cols; x++) {
        for (let y = 0; y <= rows; y++) {
          ctx.beginPath();
          ctx.arc(x * cellSize, y * cellSize, 1, 0, Math.PI * 2);
          ctx.fillStyle = "rgba(77,166,255,0.06)";
          ctx.fill();
        }
      }

      // Pulses
      pulses.forEach(p => {
        p.age++;
        p.radius = (p.age / p.maxAge) * 180;
        const alpha = 0.12 * (1 - p.age / p.maxAge);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(77,166,255,${alpha})`;
        ctx.lineWidth = 1;
        ctx.stroke();
        // Center glow
        const ga = 0.3 * (1 - p.age / p.maxAge);
        ctx.beginPath();
        ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(77,166,255,${ga})`;
        ctx.fill();
      });
      pulses = pulses.filter(p => p.age < p.maxAge);

      if (frame % 50 === 0) addPulse();
      frame++;
      requestAnimationFrame(draw);
    };
    draw();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, []);
  return <canvas ref={canvasRef} style={{ position: "fixed", top: 0, left: 0, width: "100%", height: "100%", pointerEvents: "none", zIndex: 0 }} />;
}

// ── Reveal ──
function Reveal({ children, delay = 0, style = {} }) {
  const ref = useRef(null);
  const [v, setV] = useState(false);
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setV(true); }, { threshold: 0.12 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);
  return <div ref={ref} style={{ ...style, opacity: v ? 1 : 0, transform: v ? "translateY(0)" : "translateY(36px)", transition: `all 0.9s cubic-bezier(0.16,1,0.3,1) ${delay}s` }}>{children}</div>;
}

// ── Animated Number ──
function AnimNum({ target, suffix = "", prefix = "" }) {
  const [val, setVal] = useState(0);
  const ref = useRef(null);
  const started = useRef(false);
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting && !started.current) {
        started.current = true;
        const t0 = performance.now();
        const tick = (now) => {
          const p = Math.min((now - t0) / 2000, 1);
          setVal(Math.round(target * (1 - Math.pow(1 - p, 3))));
          if (p < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      }
    }, { threshold: 0.3 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [target]);
  return <span ref={ref}>{prefix}{val}{suffix}</span>;
}

// ── Live Ticker ──
function LiveTicker() {
  const markets = [
    { q: "Fed rate increase March 2026?", y: 1.7, signal: "NO_TRADE" },
    { q: "Tesla unsupervised FSD by June?", y: 99.9, signal: "BUY_NO" },
    { q: "Khamenei out by March 31?", y: 20.5, signal: "BUY_NO" },
    { q: "Human moon landing 2026?", y: 6.3, signal: "BUY_NO" },
    { q: "Gov shutdown 4+ days?", y: 97.3, signal: "BUY_YES" },
    { q: "Trump nominates Warsh?", y: 98.8, signal: "BUY_NO" },
    { q: "Russia-Ukraine ceasefire?", y: 11.5, signal: "NO_TRADE" },
    { q: "US strikes Iran by March?", y: 43.5, signal: "NO_TRADE" },
  ];

  const [offset, setOffset] = useState(0);
  useEffect(() => {
    const iv = setInterval(() => setOffset(o => o - 0.5), 30);
    return () => clearInterval(iv);
  }, []);

  const doubled = [...markets, ...markets];

  return (
    <div style={{ overflow: "hidden", borderTop: `1px solid ${C.border}`, borderBottom: `1px solid ${C.border}`, background: `${C.bg2}cc`, backdropFilter: "blur(8px)", position: "relative", zIndex: 2 }}>
      <div style={{ display: "flex", whiteSpace: "nowrap", transform: `translateX(${offset}px)`, transition: "none" }}>
        {doubled.map((m, i) => {
          const sigColor = m.signal === "BUY_YES" ? C.teal : m.signal === "BUY_NO" ? C.red : C.dim;
          return (
            <div key={i} style={{ display: "inline-flex", alignItems: "center", gap: 12, padding: "12px 32px", borderRight: `1px solid ${C.border}`, fontFamily: "'JetBrains Mono', monospace", fontSize: 11, flexShrink: 0 }}>
              <span style={{ color: sigColor, fontSize: 9, fontWeight: 700 }}>{m.signal === "BUY_YES" ? "▲" : m.signal === "BUY_NO" ? "▼" : "●"}</span>
              <span style={{ color: C.frost }}>{m.q}</span>
              <span style={{ color: m.y > 50 ? C.teal : C.amber, fontWeight: 600 }}>{m.y}¢</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Glowing border card ──
function Card({ children, style = {}, glow = C.blue }) {
  const [h, setH] = useState(false);
  return (
    <div onMouseEnter={() => setH(true)} onMouseLeave={() => setH(false)} style={{
      background: h ? C.bgHover : C.bgCard, border: `1px solid ${h ? glow + "30" : C.border}`,
      borderRadius: 10, position: "relative", overflow: "hidden",
      transition: "all 0.4s ease", cursor: "default",
      boxShadow: h ? `0 8px 40px ${glow}08` : "none", ...style,
    }}>
      {h && <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 1, background: `linear-gradient(90deg, transparent, ${glow}50, transparent)` }} />}
      {children}
    </div>
  );
}

// ── Section ──
function Sec({ children, id, style = {} }) {
  return <section id={id} style={{ position: "relative", zIndex: 1, ...style }}><div style={{ maxWidth: 1140, margin: "0 auto", padding: "0 36px" }}>{children}</div></section>;
}

// ── Terminal Window ──
function TerminalWindow({ lines }) {
  const [visible, setVisible] = useState([]);
  const started = useRef(false);
  const ref = useRef(null);

  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting && !started.current) {
        started.current = true;
        let i = 0;
        const iv = setInterval(() => {
          if (i < lines.length) {
            const line = lines[i];
            i++;
            if (line) setVisible(prev => [...prev, line]);
          } else {
            clearInterval(iv);
          }
        }, 120);
      }
    }, { threshold: 0.3 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [lines]);

  return (
    <div ref={ref} style={{ background: "#060a10", border: `1px solid ${C.border}`, borderRadius: 8, overflow: "hidden" }}>
      {/* Title bar */}
      <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "10px 16px", borderBottom: `1px solid ${C.border}`, background: C.bg2 }}>
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: C.red, opacity: 0.7 }} />
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: C.amber, opacity: 0.7 }} />
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: C.green, opacity: 0.7 }} />
        <span style={{ color: C.dim, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, marginLeft: 8 }}>oracle-sentinel — scan_cycle</span>
      </div>
      {/* Content */}
      <div style={{ padding: "16px 20px", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, lineHeight: 1.8, minHeight: 240, maxHeight: 320, overflowY: "auto" }}>
        {visible.map((line, i) => (
          <div key={i} style={{ color: line.c || C.frost, opacity: line.dim ? 0.5 : 1 }}>{line.t}</div>
        ))}
        {visible.length < lines.length && (
          <span style={{ color: C.blue, fontWeight: "bold", animation: "pulse 1s infinite" }}>█</span>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// MAIN LANDING PAGE
// ═══════════════════════════════════════════════════════════════

export default function OracleSentinelLanding() {
  const [scrollY, setScrollY] = useState(0);
  useEffect(() => {
    const onScroll = () => setScrollY(window.scrollY);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div style={{ background: C.bg, color: C.frost, fontFamily: "'Syne', sans-serif", minHeight: "100vh", overflowX: "hidden" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Syne:wght@400;500;600;700;800&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html { scroll-behavior: smooth; }
        body { background: ${C.bg}; }
        ::selection { background: ${C.blue}30; color: ${C.ice}; }
        ::-webkit-scrollbar { width: 5px; } ::-webkit-scrollbar-track { background: ${C.bg}; } ::-webkit-scrollbar-thumb { background: ${C.borderL}; border-radius: 3px; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
        @keyframes shimmer { 0% { background-position: -200% center; } 100% { background-position: 200% center; } }
        @keyframes borderGlow { 0%, 100% { border-color: ${C.border}; } 50% { border-color: ${C.blue}30; } }
        .cta-btn { position: relative; overflow: hidden; }
        .cta-btn::after { content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: linear-gradient(45deg, transparent, rgba(255,255,255,0.03), transparent); transform: rotate(45deg); transition: 0.5s; }
        .cta-btn:hover::after { left: 100%; }
      `}</style>

      <GridBG />

      {/* ── NAV ── */}
      <nav style={{
        position: "fixed", top: 0, left: 0, right: 0, zIndex: 100,
        background: scrollY > 80 ? `${C.bg}e8` : "transparent",
        backdropFilter: scrollY > 80 ? "blur(16px)" : "none",
        borderBottom: scrollY > 80 ? `1px solid ${C.border}` : "1px solid transparent",
        transition: "all 0.4s", padding: "0 36px",
      }}>
        <div style={{ maxWidth: 1140, margin: "0 auto", display: "flex", justifyContent: "space-between", alignItems: "center", height: 60 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ color: C.blue, fontSize: 7, animation: "pulse 2s infinite" }}>●</span>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <img src="/logo.png" alt="Oracle Sentinel" style={{ width: 60, height: 60, borderRadius: "50%" }} />
            <span style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 700, letterSpacing: 3 }}>ORACLE SENTINEL</span>
          </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
            {["Features", "How It Works", "Stack", "API"].map(t => (
              <a key={t} href={`#${t.toLowerCase().replace(/ /g, "-")}`} style={{
                color: C.slate, fontFamily: "'JetBrains Mono', monospace", fontSize: 10,
                letterSpacing: 1.5, textDecoration: "none", textTransform: "uppercase",
                transition: "color 0.2s",
              }} onMouseEnter={e => e.target.style.color = C.frost} onMouseLeave={e => e.target.style.color = C.slate}>{t}</a>
            ))}
            <a href="/docs" style={{
              color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10,
              letterSpacing: 1.5, textDecoration: "none", border: `1px solid ${C.blue}40`,
              padding: "6px 16px", borderRadius: 4, transition: "all 0.3s",
            }}>DOCS</a>
            <a href="/app" style={{
              background: `linear-gradient(135deg, ${C.blue}, ${C.blueM})`,
              color: "#fff", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, fontWeight: 600,
              letterSpacing: 1.5, textDecoration: "none", padding: "7px 18px", borderRadius: 4,
            }}>DASHBOARD</a>
          </div>
        </div>
      </nav>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* HERO */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Sec id="hero" style={{ paddingTop: 140, paddingBottom: 0, minHeight: "100vh" }}>
        {/* Giant glow */}
        <div style={{
          position: "absolute", top: "10%", left: "50%", transform: "translateX(-50%)",
          width: 700, height: 700, borderRadius: "50%", pointerEvents: "none",
          background: `radial-gradient(circle, ${C.blue}06 0%, transparent 65%)`,
        }} />

        <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 60, alignItems: "center", minHeight: "80vh", justifyItems: "center", textAlign: "center" }}>
          {/* Left — Copy */}
          <div>

            <Reveal delay={0.1}>
              <h1 style={{ fontSize: "clamp(40px, 5.5vw, 68px)", fontWeight: 800, lineHeight: 1.05, color: C.ice, marginBottom: 24, letterSpacing: -1 }}>
                The AI That<br />
                <span style={{
                  background: `linear-gradient(135deg, ${C.blue}, ${C.teal})`,
                  WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
                }}>Predicts the<br />Predictors</span>
              </h1>
            </Reveal>

            <Reveal delay={0.2}>
              <p style={{ fontSize: 16, color: C.frost, lineHeight: 1.8, maxWidth: 560, marginBottom: 36, margin: "0 auto 36px" }}>
                Oracle Sentinel autonomously scans Polymarket 24/7, identifies mispriced prediction markets using dual-model AI intelligence, and tracks every call with radical transparency.
              </p>
            </Reveal>

            <Reveal delay={0.3}>
              <div style={{ display: "flex", gap: 14, justifyContent: "center" }}>
                <a href="/app" className="cta-btn" style={{
                  background: `linear-gradient(135deg, ${C.blue}, ${C.blueM})`,
                  color: "#fff", fontFamily: "'JetBrains Mono', monospace", fontSize: 12, fontWeight: 600,
                  letterSpacing: 1.5, padding: "15px 32px", borderRadius: 6, textDecoration: "none",
                  boxShadow: `0 4px 30px ${C.blue}20`, display: "inline-block",
                }}>OPEN DASHBOARD →</a>
                <a href="/docs" style={{
                  background: "transparent", border: `1px solid ${C.borderL}`,
                  color: C.frost, fontFamily: "'JetBrains Mono', monospace", fontSize: 12, fontWeight: 500,
                  letterSpacing: 1.5, padding: "15px 32px", borderRadius: 6, textDecoration: "none",
                  display: "inline-block",
                }}>READ DOCS</a>
              </div>
            </Reveal>
          </div>
        </div>
      </Sec>

      {/* ── LIVE TICKER ── */}
      <div style={{ marginTop: 40 }}>
        <LiveTicker />
      </div>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* SOCIAL PROOF BAR */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Sec style={{ padding: "56px 0" }}>
        <Reveal>
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 48, flexWrap: "wrap" }}>
            {[
              { l: "Powered by", v: "Anthropic Claude", c: C.blue },
              { l: "Data from", v: "Polymarket", c: C.teal },
              { l: "Automated via", v: "OpenClaw", c: C.amber },
              { l: "Alerts via", v: "Telegram", c: C.frost },
              { l: "Built on", v: "Solana Ecosystem", c: C.blue },
            ].map((b, i) => (
              <div key={i} style={{ textAlign: "center" }}>
                <div style={{ color: C.dim, fontFamily: "'JetBrains Mono', monospace", fontSize: 8, letterSpacing: 2, marginBottom: 4 }}>{b.l}</div>
                <div style={{ color: b.c, fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 600 }}>{b.v}</div>
              </div>
            ))}
          </div>
        </Reveal>
      </Sec>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* FEATURES */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Sec id="features" style={{ padding: "80px 0 100px", borderTop: `1px solid ${C.border}` }}>
        <Reveal>
          <div style={{ textAlign: "center", marginBottom: 56 }}>
            <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 4, marginBottom: 12 }}>CORE CAPABILITIES</div>
            <h2 style={{ color: C.ice, fontSize: "clamp(28px, 4vw, 42px)", fontWeight: 800, lineHeight: 1.15 }}>Not just signals.<br /><span style={{ color: C.blue }}>Intelligence.</span></h2>
          </div>
        </Reveal>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 18 }}>
          {[
            { title: "Dual-Model AI Brain", desc: "Haiku extracts. Sonnet assesses. Two models cross-validate each other — eliminating single-model hallucination risk.", color: C.blue, tag: "AI" },
            { title: "Whale Detection", desc: "Real-time order book analysis. Large bids, asks, and sentiment shifts tracked per market. When smart money moves, you know.", color: C.teal, tag: "DATA" },
            { title: "Quantified Edge", desc: "Every signal comes with an exact edge percentage — the mathematical difference between AI probability and market consensus.", color: C.amber, tag: "MATH" },
            { title: "Radical Transparency", desc: "Every prediction tracked at 1h, 6h, 24h. No cherry-picking wins. Accuracy computed live from real data.", color: C.red, tag: "TRUST" },
            { title: "Fully Autonomous", desc: "OpenClaw cron triggers every 4 hours. Zero human intervention from scan to signal to tracking. 24/7/365.", color: C.green, tag: "AUTO" },
            { title: "Safety Overrides", desc: "High edge + medium confidence = forced NO_TRADE. The system is designed to distrust its own overconfidence.", color: C.blueM, tag: "SAFE" },
          ].map((f, i) => (
            <Reveal key={i} delay={i * 0.07}>
              <Card glow={f.color} style={{ padding: "28px 24px", height: "100%" }}>
                <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 16 }}>
                  <span style={{ color: f.color, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, letterSpacing: 1.5, opacity: 0.6 }}>{f.tag}</span>
                </div>
                <div style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 14, fontWeight: 600, marginBottom: 10 }}>{f.title}</div>
                <div style={{ color: C.slate, fontSize: 13, lineHeight: 1.7 }}>{f.desc}</div>
              </Card>
            </Reveal>
          ))}
        </div>
      </Sec>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* HOW IT WORKS */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Sec id="how-it-works" style={{ padding: "80px 0 100px", borderTop: `1px solid ${C.border}` }}>
        <Reveal>
          <div style={{ textAlign: "center", marginBottom: 64 }}>
            <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 4, marginBottom: 12 }}>HOW IT WORKS</div>
            <h2 style={{ color: C.ice, fontSize: "clamp(28px, 4vw, 42px)", fontWeight: 800, lineHeight: 1.15 }}>Five stages.<br /><span style={{ color: C.teal }}>Zero human input.</span></h2>
          </div>
        </Reveal>

        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {[
            { num: "01", title: "INGEST", desc: "Pull real-time market data, prices, volume, liquidity, and order books from Polymarket's API. Scrape relevant news articles for each active market.", accent: C.blue },
            { num: "02", title: "EXTRACT", desc: "Claude Haiku 3.5 processes raw news articles and extracts structured facts — removing noise, bias, and irrelevant information. Pure signal.", accent: C.teal },
            { num: "03", title: "ASSESS", desc: "Claude Sonnet 4.5 receives extracted facts + whale data and computes an independent AI probability with full reasoning chain. No market anchoring.", accent: C.amber },
            { num: "04", title: "SIGNAL", desc: "Edge calculator compares AI probability vs market price. Generates BUY_YES, BUY_NO, or NO_TRADE with confidence scoring and safety overrides.", accent: C.red },
            { num: "05", title: "TRACK", desc: "Accuracy tracker snapshots market prices at 1h, 6h, and 24h after each signal. Every prediction measured. Every result permanent.", accent: C.green },
          ].map((step, i) => (
            <Reveal key={i} delay={i * 0.08}>
              <div style={{ display: "grid", gridTemplateColumns: "80px 1fr 1fr", gap: 32, alignItems: "center", padding: "36px 0", borderBottom: i < 4 ? `1px solid ${C.border}` : "none" }}>
                {/* Number */}
                <div style={{ textAlign: "center" }}>
                  <div style={{ color: step.accent, fontFamily: "'JetBrains Mono', monospace", fontSize: 36, fontWeight: 700, opacity: 0.3 }}>{step.num}</div>
                </div>
                {/* Info */}
                <div>
                  <div style={{ marginBottom: 8 }}>
                    <span style={{ color: step.accent, fontFamily: "'JetBrains Mono', monospace", fontSize: 14, fontWeight: 700, letterSpacing: 1 }}>{step.title}</span>
                  </div>
                  <div style={{ color: C.frost, fontSize: 14, lineHeight: 1.7, maxWidth: 420 }}>{step.desc}</div>
                </div>
                {/* Visual bar */}
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ flex: 1, height: 3, background: C.border, borderRadius: 2, overflow: "hidden" }}>
                    <div style={{ width: `${20 + i * 20}%`, height: "100%", background: `linear-gradient(90deg, ${step.accent}, ${step.accent}40)`, borderRadius: 2, transition: "width 1s ease" }} />
                  </div>
                  <span style={{ color: C.dim, fontFamily: "'JetBrains Mono', monospace", fontSize: 9 }}>{["12.4s", "3.2s", "8.7s", "0.3s", "∞"][i]}</span>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </Sec>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* TECH STACK */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Sec id="stack" style={{ padding: "80px 0 100px", borderTop: `1px solid ${C.border}` }}>
        <Reveal>
          <div style={{ textAlign: "center", marginBottom: 56 }}>
            <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 4, marginBottom: 12 }}>TECHNOLOGY</div>
            <h2 style={{ color: C.ice, fontSize: "clamp(28px, 4vw, 42px)", fontWeight: 800 }}>Built to <span style={{ color: C.amber }}>last.</span></h2>
          </div>
        </Reveal>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16, maxWidth: 600, margin: "0 auto" }}>
          {[
            { cat: "INTELLIGENCE", items: ["Claude Sonnet 4.5 — Deep Reasoning", "Claude Haiku 3.5 — Fact Extraction", "Multi-model Routing Engine", "Cross-validation Pipeline"], c: C.blue },
            { cat: "INFRASTRUCTURE", items: ["24/7 Agent Orchestration", "Real-time Signal Delivery", "REST API Gateway", "Time-series Data Engine"], c: C.frost },
          ].map((g, i) => (
            <Reveal key={i} delay={i * 0.08}>
              <Card glow={g.c} style={{ padding: "24px 20px" }}>
                <div style={{ color: g.c, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, letterSpacing: 2, marginBottom: 16 }}>{g.cat}</div>
                {g.items.map((item, j) => (
                  <div key={j} style={{ color: C.frost, fontFamily: "'JetBrains Mono', monospace", fontSize: 12, padding: "6px 0", borderBottom: j < g.items.length - 1 ? `1px solid ${C.border}` : "none" }}>{item}</div>
                ))}
              </Card>
            </Reveal>
          ))}
        </div>
      </Sec>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* API PREVIEW */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Sec id="api" style={{ padding: "80px 0 100px", borderTop: `1px solid ${C.border}` }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 48, alignItems: "center" }}>
          <div>
            <Reveal>
              <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 4, marginBottom: 12 }}>DEVELOPER API</div>
              <h2 style={{ color: C.ice, fontSize: 36, fontWeight: 800, marginBottom: 20, lineHeight: 1.15 }}>Build on top of<br /><span style={{ color: C.teal }}>Oracle Intelligence.</span></h2>
            </Reveal>
            <Reveal delay={0.1}>
              <p style={{ color: C.frost, fontSize: 14, lineHeight: 1.8, marginBottom: 28, maxWidth: 400 }}>
                RESTful API serving real-time signals, market data, predictions, and system logs. Integrate Oracle Sentinel's intelligence into your own trading tools, bots, or dashboards.
              </p>
            </Reveal>
            <Reveal delay={0.2}>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {[
                  { m: "GET", p: "/api/dashboard", d: "Complete data payload" },
                  { m: "GET", p: "/api/signals", d: "Active trading signals" },
                  { m: "GET", p: "/api/markets", d: "All tracked markets" },
                  { m: "GET", p: "/api/predictions", d: "Tracked predictions" },
                  { m: "GET", p: "/api/health", d: "System health check" },
                ].map((ep, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "8px 0" }}>
                    <span style={{ color: C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, fontWeight: 700, width: 30 }}>{ep.m}</span>
                    <span style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 12, fontWeight: 500, flex: 1 }}>{ep.p}</span>
                    <span style={{ color: C.dim, fontSize: 11 }}>{ep.d}</span>
                  </div>
                ))}
              </div>
            </Reveal>
            <Reveal delay={0.3}>
              <a href="/docs#api" style={{
                display: "inline-block", marginTop: 24, color: C.blue,
                fontFamily: "'JetBrains Mono', monospace", fontSize: 12, letterSpacing: 1,
                textDecoration: "none", borderBottom: `1px solid ${C.blue}40`, paddingBottom: 2,
              }}>FULL API REFERENCE →</a>
            </Reveal>
          </div>

          <Reveal delay={0.2}>
            <div style={{ background: "#060a10", border: `1px solid ${C.border}`, borderRadius: 8, overflow: "hidden" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "10px 16px", borderBottom: `1px solid ${C.border}`, background: C.bg2 }}>
                <div style={{ width: 10, height: 10, borderRadius: "50%", background: C.red, opacity: 0.7 }} />
                <div style={{ width: 10, height: 10, borderRadius: "50%", background: C.amber, opacity: 0.7 }} />
                <div style={{ width: 10, height: 10, borderRadius: "50%", background: C.green, opacity: 0.7 }} />
                <span style={{ color: C.dim, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, marginLeft: 8 }}>fetch_signals.py</span>
              </div>
              <pre style={{ padding: "20px", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, lineHeight: 1.8, color: C.frost, overflowX: "auto", margin: 0 }}>
{`import requests

signals = requests.get(
    "https://oraclesentinel.xyz/api/signals"
).json()

for s in signals:
    edge = s["edge"]
    conf = s["confidence"]
    
    if edge > 10 and conf == "HIGH":
        print(f"🎯 {s['signal_type']}")
        print(f"   {s['question']}")
        print(f"   Edge: +{edge}%")
        print(f"   AI:   {s['ai_probability']}")
        print()`}
              </pre>
            </div>
          </Reveal>
        </div>
      </Sec>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* CTA */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Sec style={{ padding: "100px 0 80px", borderTop: `1px solid ${C.border}` }}>
        <Reveal>
          <div style={{
            textAlign: "center", padding: "64px 48px", borderRadius: 12,
            background: `linear-gradient(135deg, ${C.blueDD}40, ${C.bgCard}, ${C.blueDD}20)`,
            border: `1px solid ${C.blue}15`, position: "relative", overflow: "hidden",
          }}>
            {/* Glow */}
            <div style={{ position: "absolute", top: -100, left: "50%", transform: "translateX(-50%)", width: 400, height: 400, borderRadius: "50%", background: `radial-gradient(circle, ${C.blue}08, transparent)`, pointerEvents: "none" }} />

            <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 4, marginBottom: 16, position: "relative" }}>READY TO SEE THE EDGE?</div>
            <h2 style={{ color: C.ice, fontSize: "clamp(28px, 4vw, 44px)", fontWeight: 800, marginBottom: 20, position: "relative" }}>
              Start tracking predictions.<br />
              <span style={{ color: C.teal }}>Right now.</span>
            </h2>
            <p style={{ color: C.frost, fontSize: 14, maxWidth: 480, margin: "0 auto 32px", lineHeight: 1.7, position: "relative" }}>
              Oracle Sentinel is live, scanning Polymarket every 4 hours, generating signals, and tracking accuracy. Open the dashboard and see AI intelligence in action.
            </p>
            <div style={{ display: "flex", justifyContent: "center", gap: 14, position: "relative" }}>
              <a href="/app" className="cta-btn" style={{
                background: `linear-gradient(135deg, ${C.blue}, ${C.blueM})`,
                color: "#fff", fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 600,
                letterSpacing: 1.5, padding: "16px 40px", borderRadius: 6, textDecoration: "none",
                boxShadow: `0 4px 30px ${C.blue}25`,
              }}>OPEN DASHBOARD</a>
              <a href="#api" style={{
                background: "transparent", border: `1px solid ${C.borderL}`,
                color: C.frost, fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 500,
                letterSpacing: 1.5, padding: "16px 40px", borderRadius: 6, textDecoration: "none",
              }}>VIEW API</a>
            </div>
          </div>
        </Reveal>
      </Sec>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* FOOTER */}
      {/* ═══════════════════════════════════════════════════════ */}
      <footer style={{ borderTop: `1px solid ${C.border}`, padding: "40px 36px", position: "relative", zIndex: 1 }}>
        <div style={{ maxWidth: 1140, margin: "0 auto", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
              <span style={{ color: C.blue, fontSize: 7, animation: "pulse 2s infinite" }}>●</span>
              <span style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 12, fontWeight: 700, letterSpacing: 3 }}>ORACLE SENTINEL</span>
            </div>
            <div style={{ color: C.dim, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, letterSpacing: 1 }}>Autonomous Prediction Intelligence · Built on Solana Ecosystem · © 2026</div>
          </div>
          <div style={{ display: "flex", gap: 24 }}>
            {[
              { l: "X", h: "https://x.com/oracle_sentinel" },
              { l: "Telegram", h: "https://t.me/oraclesentinelsignals" },
              { l: "$OSAI", h: "https://solscan.io/token/HuDBwWRsa4bu8ueaCb7PPgJrqBeZDkcyFqMW5bbXpump" },
            ].map((lnk, i) => (
              <a key={i} href={lnk.h} style={{ color: C.slate, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, textDecoration: "none", letterSpacing: 1 }}>{lnk.l}</a>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}