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
      ctx.strokeStyle = "rgba(77,166,255,0.03)";
      ctx.lineWidth = 0.5;
      for (let x = 0; x <= cols; x++) {
        ctx.beginPath(); ctx.moveTo(x * cellSize, 0); ctx.lineTo(x * cellSize, h); ctx.stroke();
      }
      for (let y = 0; y <= rows; y++) {
        ctx.beginPath(); ctx.moveTo(0, y * cellSize); ctx.lineTo(w, y * cellSize); ctx.stroke();
      }
      for (let x = 0; x <= cols; x++) {
        for (let y = 0; y <= rows; y++) {
          ctx.beginPath();
          ctx.arc(x * cellSize, y * cellSize, 1, 0, Math.PI * 2);
          ctx.fillStyle = "rgba(77,166,255,0.06)";
          ctx.fill();
        }
      }
      pulses.forEach(p => {
        p.age++;
        p.radius = (p.age / p.maxAge) * 180;
        const alpha = 0.12 * (1 - p.age / p.maxAge);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(77,166,255,${alpha})`;
        ctx.lineWidth = 1;
        ctx.stroke();
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

// ── Card ──
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
            {["Intelligence", "Features", "API", "Token"].map(t => (
              <a key={t} href={`#${t.toLowerCase()}`} style={{
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
            <a href="/predict" style={{
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
        <div style={{
          position: "absolute", top: "10%", left: "50%", transform: "translateX(-50%)",
          width: 700, height: 700, borderRadius: "50%", pointerEvents: "none",
          background: `radial-gradient(circle, ${C.blue}06 0%, transparent 65%)`,
        }} />

        <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 60, alignItems: "center", minHeight: "80vh", justifyItems: "center", textAlign: "center" }}>
          <div>
            <Reveal delay={0.1}>
              <h1 style={{ fontSize: "clamp(40px, 5.5vw, 68px)", fontWeight: 800, lineHeight: 1.05, color: C.ice, marginBottom: 24, letterSpacing: -1 }}>
                Autonomous<br />
                <span style={{
                  background: `linear-gradient(135deg, ${C.blue}, ${C.teal})`,
                  WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
                }}>Intelligence<br />Layer</span>
              </h1>
            </Reveal>

            <Reveal delay={0.2}>
              <p style={{ fontSize: 16, color: C.frost, lineHeight: 1.8, maxWidth: 580, marginBottom: 36, margin: "0 auto 36px" }}>
                AI-powered analysis for prediction markets and code repositories. Scan Polymarket for mispriced opportunities. Audit GitHub repos for vulnerabilities. All tracked with radical transparency.
              </p>
            </Reveal>

            <Reveal delay={0.3}>
              <div style={{ display: "flex", gap: 14, justifyContent: "center" }}>
                <a href="/predict" className="cta-btn" style={{
                  background: `linear-gradient(135deg, ${C.blue}, ${C.blueM})`,
                  color: "#fff", fontFamily: "'JetBrains Mono', monospace", fontSize: 12, fontWeight: 600,
                  letterSpacing: 1.5, padding: "15px 32px", borderRadius: 6, textDecoration: "none",
                  boxShadow: `0 4px 30px ${C.blue}20`, display: "inline-block",
                }}>PREDICT DASHBOARD</a>
                <a href="/code" style={{
                  background: "transparent", border: `1px solid ${C.teal}60`,
                  color: C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 12, fontWeight: 500,
                  letterSpacing: 1.5, padding: "15px 32px", borderRadius: 6, textDecoration: "none",
                  display: "inline-block",
                }}>CODE ANALYZER</a>
              </div>
            </Reveal>
          </div>
        </div>
      </Sec>

      <div style={{ marginTop: 40 }}>
        <LiveTicker />
      </div>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* INTELLIGENCE MODULES */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Sec id="intelligence" style={{ padding: "100px 0", borderTop: `1px solid ${C.border}` }}>
        <Reveal>
          <div style={{ textAlign: "center", marginBottom: 64 }}>
            <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 4, marginBottom: 12 }}>INTELLIGENCE MODULES</div>
            <h2 style={{ color: C.ice, fontSize: "clamp(28px, 4vw, 42px)", fontWeight: 800, lineHeight: 1.15 }}>Two brains.<br /><span style={{ color: C.teal }}>One mission.</span></h2>
          </div>
        </Reveal>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
          {/* PREDICT Module */}
          <Reveal delay={0.1}>
            <Card glow={C.blue} style={{ padding: 0, height: "100%" }}>
              <div style={{ padding: "32px 28px", borderBottom: `1px solid ${C.border}` }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <div style={{ width: 40, height: 40, background: `linear-gradient(135deg, ${C.blue}, ${C.blueM})`, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <span style={{ color: "#fff", fontFamily: "'JetBrains Mono', monospace", fontSize: 14, fontWeight: 700 }}>P</span>
                    </div>
                    <div>
                      <div style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 16, fontWeight: 700 }}>SENTINEL PREDICT</div>
                      <div style={{ color: C.dim, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 1 }}>POLYMARKET INTELLIGENCE</div>
                    </div>
                  </div>
                  <span style={{ color: C.green, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, padding: "4px 10px", background: `${C.green}15`, borderRadius: 4 }}>LIVE</span>
                </div>
                <p style={{ color: C.frost, fontSize: 14, lineHeight: 1.7, marginBottom: 20 }}>
                  Autonomous prediction market scanner. Dual-model AI (Haiku + Sonnet) identifies mispriced markets, calculates edge, and tracks accuracy with radical transparency.
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {["Dual-Model AI", "Whale Detection", "Edge Calculator", "Accuracy Tracking"].map(t => (
                    <span key={t} style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, padding: "4px 10px", background: `${C.blue}10`, border: `1px solid ${C.blue}20`, borderRadius: 4 }}>{t}</span>
                  ))}
                </div>
              </div>
              <div style={{ padding: "20px 28px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", gap: 24 }}>
                  <div>
                    <div style={{ color: C.dim, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, marginBottom: 2 }}>SCAN INTERVAL</div>
                    <div style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 13 }}>4 hours</div>
                  </div>
                  <div>
                    <div style={{ color: C.dim, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, marginBottom: 2 }}>MARKETS</div>
                    <div style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 13 }}>50+ active</div>
                  </div>
                </div>
                <a href="/predict" style={{
                  background: `linear-gradient(135deg, ${C.blue}, ${C.blueM})`,
                  color: "#fff", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, fontWeight: 600,
                  letterSpacing: 1, padding: "10px 20px", borderRadius: 5, textDecoration: "none",
                }}>OPEN DASHBOARD</a>
              </div>
            </Card>
          </Reveal>

          {/* CODE Module */}
          <Reveal delay={0.2}>
            <Card glow={C.teal} style={{ padding: 0, height: "100%" }}>
              <div style={{ padding: "32px 28px", borderBottom: `1px solid ${C.border}` }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <div style={{ width: 40, height: 40, background: `linear-gradient(135deg, ${C.teal}, ${C.green})`, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <span style={{ color: "#fff", fontFamily: "'JetBrains Mono', monospace", fontSize: 14, fontWeight: 700 }}>C</span>
                    </div>
                    <div>
                      <div style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 16, fontWeight: 700 }}>SENTINEL CODE</div>
                      <div style={{ color: C.dim, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 1 }}>GITHUB INTELLIGENCE</div>
                    </div>
                  </div>
                  <span style={{ color: C.green, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, padding: "4px 10px", background: `${C.green}15`, borderRadius: 4 }}>LIVE</span>
                </div>
                <p style={{ color: C.frost, fontSize: 14, lineHeight: 1.7, marginBottom: 20 }}>
                  AI-powered code analysis. Scan any GitHub repository for security vulnerabilities, bugs, and code quality issues. Perfect for developers and investors auditing projects.
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {["Security Audit", "Bug Detection", "Code Quality", "Auto-Fix Suggestions"].map(t => (
                    <span key={t} style={{ color: C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, padding: "4px 10px", background: `${C.teal}10`, border: `1px solid ${C.teal}20`, borderRadius: 4 }}>{t}</span>
                  ))}
                </div>
              </div>
              <div style={{ padding: "20px 28px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", gap: 24 }}>
                  <div>
                    <div style={{ color: C.dim, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, marginBottom: 2 }}>ANALYSIS TIME</div>
                    <div style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 13 }}>30-60 sec</div>
                  </div>
                  <div>
                    <div style={{ color: C.dim, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, marginBottom: 2 }}>LANGUAGES</div>
                    <div style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 13 }}>15+ supported</div>
                  </div>
                </div>
                <a href="/code" style={{
                  background: `linear-gradient(135deg, ${C.teal}, ${C.green})`,
                  color: "#fff", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, fontWeight: 600,
                  letterSpacing: 1, padding: "10px 20px", borderRadius: 5, textDecoration: "none",
                }}>ANALYZE CODE</a>
              </div>
            </Card>
          </Reveal>
        </div>

        {/* Coming Soon */}
        <Reveal delay={0.3}>
          <div style={{ marginTop: 24, padding: "20px 28px", background: C.bgCard, border: `1px solid ${C.border}`, borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <div style={{ width: 40, height: 40, background: `${C.amber}15`, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ color: C.amber, fontFamily: "'JetBrains Mono', monospace", fontSize: 14, fontWeight: 700 }}>T</span>
              </div>
              <div>
                <div style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 14, fontWeight: 600 }}>SENTINEL TRUST</div>
                <div style={{ color: C.dim, fontSize: 12 }}>Token & project trust scoring based on on-chain data and code analysis</div>
              </div>
            </div>
            <span style={{ color: C.amber, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, padding: "4px 12px", background: `${C.amber}15`, borderRadius: 4 }}>COMING SOON</span>
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
            <h2 style={{ color: C.ice, fontSize: "clamp(28px, 4vw, 42px)", fontWeight: 800, lineHeight: 1.15 }}>Not just data.<br /><span style={{ color: C.blue }}>Intelligence.</span></h2>
          </div>
        </Reveal>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 18 }}>
          {[
            { title: "Dual-Model AI Brain", desc: "Haiku extracts facts. Sonnet assesses probability. Two models cross-validate — eliminating single-model hallucination.", color: C.blue, tag: "AI" },
            { title: "Security Scanner", desc: "Detects SQL injection, XSS, hardcoded secrets, and insecure patterns. Every issue with exact file, line, and fix.", color: C.teal, tag: "SECURITY" },
            { title: "Quantified Edge", desc: "Every signal comes with an exact edge percentage — the mathematical difference between AI probability and market consensus.", color: C.amber, tag: "MATH" },
            { title: "Radical Transparency", desc: "Every prediction tracked at 1h, 6h, 24h. Every code scan logged. No cherry-picking. Accuracy computed from real data.", color: C.red, tag: "TRUST" },
            { title: "Fully Autonomous", desc: "Prediction scans every 4 hours. Code analysis on-demand. Zero human intervention from input to output. 24/7/365.", color: C.green, tag: "AUTO" },
            { title: "Developer First", desc: "Python SDK, REST API, x402 micropayments. Build trading bots, integrate code checks into CI/CD, or just explore.", color: C.blueM, tag: "DEV" },
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
      {/* API */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Sec id="api" style={{ padding: "80px 0 100px", borderTop: `1px solid ${C.border}` }}>
        <Reveal>
          <div style={{ textAlign: "center", marginBottom: 56 }}>
            <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 4, marginBottom: 12 }}>DEVELOPER API</div>
            <h2 style={{ color: C.ice, fontSize: "clamp(28px, 4vw, 42px)", fontWeight: 800, lineHeight: 1.15 }}>Build on <span style={{ color: C.teal }}>Oracle Intelligence.</span></h2>
          </div>
        </Reveal>

        <Reveal delay={0.1}>
          <div style={{ background: C.bgCard, border: `1px solid ${C.border}`, borderRadius: 8, overflow: "hidden", marginBottom: 24 }}>
            <div style={{ display: "grid", gridTemplateColumns: "80px 240px 1fr 80px", gap: 12, padding: "12px 16px", borderBottom: `1px solid ${C.border}`, background: C.bg2 }}>
              <span style={{ color: C.slate, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, letterSpacing: 1 }}>METHOD</span>
              <span style={{ color: C.slate, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, letterSpacing: 1 }}>ENDPOINT</span>
              <span style={{ color: C.slate, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, letterSpacing: 1 }}>DESCRIPTION</span>
              <span style={{ color: C.slate, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, letterSpacing: 1, textAlign: "right" }}>PRICE</span>
            </div>
            {[
              { m: "GET", p: "/api/signals", d: "Active trading signals", price: "FREE", module: "PREDICT" },
              { m: "GET", p: "/api/v1/analysis/{slug}", d: "Full AI analysis with reasoning", price: "$0.03", module: "PREDICT" },
              { m: "POST", p: "/api/code/analyze", d: "Analyze GitHub repository", price: "$0.10", module: "CODE" },
              { m: "GET", p: "/api/code/health", d: "Code analyzer health check", price: "FREE", module: "CODE" },
            ].map((ep, i) => (
              <div key={i} style={{ display: "grid", gridTemplateColumns: "80px 240px 1fr 80px", gap: 12, padding: "14px 16px", borderBottom: i < 3 ? `1px solid ${C.border}` : "none" }}>
                <span style={{ color: ep.m === "POST" ? C.amber : C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, fontWeight: 600 }}>{ep.m}</span>
                <span style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>{ep.p}</span>
                <div>
                  <span style={{ color: C.frost, fontSize: 12 }}>{ep.d}</span>
                  <span style={{ color: ep.module === "CODE" ? C.teal : C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, marginLeft: 8 }}>[{ep.module}]</span>
                </div>
                <span style={{ color: ep.price === "FREE" ? C.green : C.amber, fontFamily: "'JetBrains Mono', monospace", fontSize: 11, fontWeight: 600, textAlign: "right" }}>{ep.price}</span>
              </div>
            ))}
          </div>
        </Reveal>

        <Reveal delay={0.2}>
          <div style={{ padding: "16px 20px", background: `${C.teal}10`, border: `1px solid ${C.teal}30`, borderRadius: 6, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 12 }}>Hold 1,000+ $OSAI = FREE unlimited access to all endpoints</span>
            <a href="/docs" style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 11, textDecoration: "none" }}>FULL DOCS →</a>
          </div>
        </Reveal>
      </Sec>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* TOKEN */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Sec id="token" style={{ padding: "80px 0 100px", borderTop: `1px solid ${C.border}` }}>
        <Reveal>
          <div style={{ textAlign: "center", marginBottom: 48 }}>
            <div style={{ color: C.amber, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 4, marginBottom: 12 }}>$OSAI TOKEN</div>
            <h2 style={{ color: C.ice, fontSize: "clamp(28px, 4vw, 42px)", fontWeight: 800, lineHeight: 1.15 }}>Unlock <span style={{ color: C.amber }}>free access.</span></h2>
          </div>
        </Reveal>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32 }}>
          <Reveal delay={0.1}>
            <Card glow={C.amber} style={{ padding: "32px 28px", height: "100%" }}>
              <div style={{ color: C.amber, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 20 }}>CONTRACT ADDRESS</div>
              <div style={{
                display: "flex", alignItems: "center", gap: 12, padding: "16px",
                background: C.bg, border: `1px solid ${C.border}`, borderRadius: 6,
                cursor: "pointer", transition: "all 0.2s",
              }}
              onClick={() => navigator.clipboard.writeText("HuDBwWRsa4bu8ueaCb7PPgJrqBeZDkcyFqMW5bbXpump")}
              >
                <span style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 11, flex: 1, wordBreak: "break-all" }}>HuDBwWRsa4bu8ueaCb7PPgJrqBeZDkcyFqMW5bbXpump</span>
                <span style={{ color: C.dim, fontSize: 10 }}>[COPY]</span>
              </div>
              <div style={{ marginTop: 24, display: "flex", gap: 12 }}>
                <a href="https://jup.ag/swap/SOL-HuDBwWRsa4bu8ueaCb7PPgJrqBeZDkcyFqMW5bbXpump" target="_blank" rel="noopener noreferrer" style={{
                  background: `linear-gradient(135deg, ${C.amber}, ${C.amber}cc)`,
                  color: "#000", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, fontWeight: 700,
                  letterSpacing: 1, padding: "10px 16px", borderRadius: 4, textDecoration: "none",
                }}>BUY ON JUPITER</a>
                <a href="https://solscan.io/token/HuDBwWRsa4bu8ueaCb7PPgJrqBeZDkcyFqMW5bbXpump" target="_blank" rel="noopener noreferrer" style={{
                  background: "transparent", border: `1px solid ${C.borderL}`,
                  color: C.frost, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, fontWeight: 500,
                  letterSpacing: 1, padding: "10px 16px", borderRadius: 4, textDecoration: "none",
                }}>SOLSCAN</a>
              </div>
            </Card>
          </Reveal>

          <Reveal delay={0.2}>
            <Card glow={C.teal} style={{ padding: "32px 28px", height: "100%" }}>
              <div style={{ color: C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 20 }}>HOLDER BENEFITS</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                {[
                  { tier: "1,000+ $OSAI", benefit: "FREE unlimited API access (Predict + Code)", color: C.teal },
                  { tier: "10,000+ $OSAI", benefit: "Premium features (coming soon)", color: C.blue },
                  { tier: "100,000+ $OSAI", benefit: "VIP tier (coming soon)", color: C.amber },
                ].map((t, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 16, padding: "14px 16px", background: C.bg, border: `1px solid ${C.border}`, borderRadius: 6 }}>
                    <span style={{ color: t.color, fontFamily: "'JetBrains Mono', monospace", fontSize: 12, fontWeight: 600, minWidth: 120 }}>{t.tier}</span>
                    <span style={{ color: C.frost, fontSize: 12 }}>{t.benefit}</span>
                  </div>
                ))}
              </div>
            </Card>
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
            <div style={{ position: "absolute", top: -100, left: "50%", transform: "translateX(-50%)", width: 400, height: 400, borderRadius: "50%", background: `radial-gradient(circle, ${C.blue}08, transparent)`, pointerEvents: "none" }} />

            <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 4, marginBottom: 16, position: "relative" }}>READY TO START?</div>
            <h2 style={{ color: C.ice, fontSize: "clamp(28px, 4vw, 44px)", fontWeight: 800, marginBottom: 20, position: "relative" }}>
              Choose your<br />
              <span style={{ color: C.teal }}>intelligence.</span>
            </h2>
            <p style={{ color: C.frost, fontSize: 14, maxWidth: 480, margin: "0 auto 32px", lineHeight: 1.7, position: "relative" }}>
              Scan prediction markets for alpha. Audit code for vulnerabilities. Or do both. Oracle Sentinel is live and ready.
            </p>
            <div style={{ display: "flex", justifyContent: "center", gap: 14, position: "relative" }}>
              <a href="/predict" className="cta-btn" style={{
                background: `linear-gradient(135deg, ${C.blue}, ${C.blueM})`,
                color: "#fff", fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 600,
                letterSpacing: 1.5, padding: "16px 40px", borderRadius: 6, textDecoration: "none",
                boxShadow: `0 4px 30px ${C.blue}25`,
              }}>PREDICT DASHBOARD</a>
              <a href="/code" style={{
                background: `linear-gradient(135deg, ${C.teal}, ${C.green})`,
                color: "#fff", fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 600,
                letterSpacing: 1.5, padding: "16px 40px", borderRadius: 6, textDecoration: "none",
              }}>ANALYZE CODE</a>
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
            <div style={{ color: C.dim, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, letterSpacing: 1 }}>Autonomous Intelligence Layer | Predict + Code | Built on Solana | 2026</div>
          </div>
          <div style={{ display: "flex", gap: 24 }}>
            {[
              { l: "X", h: "https://x.com/oracle_sentinel" },
              { l: "GitHub", h: "https://github.com/oraclesentinel" },
              { l: "Telegram", h: "https://t.me/oraclesentinelsignals" },
              { l: "$OSAI", h: "https://solscan.io/token/HuDBwWRsa4bu8ueaCb7PPgJrqBeZDkcyFqMW5bbXpump" },
            ].map((lnk, i) => (
              <a key={i} href={lnk.h} target="_blank" rel="noopener noreferrer" style={{ color: C.slate, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, textDecoration: "none", letterSpacing: 1 }}>{lnk.l}</a>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
