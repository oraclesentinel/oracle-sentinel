import { useState, useEffect, useRef, useCallback } from "react";

// ═══════════════════════════════════════════════════════════════
// ORACLE SENTINEL — DOCUMENTATION / LANDING PAGE
// Cinematic Cold-Intelligence Aesthetic
// ═══════════════════════════════════════════════════════════════

const C = {
  bg: "#060a10", bgPanel: "#0a0f18", bgCard: "#0c1220",
  blue: "#4da6ff", blueMid: "#2d7fd4", blueDim: "#1a5a9e", blueDark: "#0d2847",
  ice: "#c8ddf0", frost: "#8badc4", slate: "#5a7184", slateD: "#3a4f60",
  red: "#e05565", teal: "#4ecdc4", amber: "#d4a843", green: "#5cb85c",
  border: "#141e2e", borderL: "#1c2d42", grid: "#0f1924",
  glow: "rgba(77,166,255,0.08)", glowT: "rgba(78,205,196,0.06)",
};

const SECTIONS = [
  { id: "hero", label: "ORACLE" },
  { id: "problem", label: "PROBLEM" },
  { id: "architecture", label: "ARCH" },
  { id: "features", label: "FEATURES" },
  { id: "filters", label: "FILTERS" },
  { id: "pipeline", label: "PIPELINE" },
  { id: "tech", label: "STACK" },
  { id: "accuracy", label: "ACCURACY" },
  { id: "sentinel-code", label: "CODE" },
  { id: "api", label: "API" },
  { id: "sdk", label: "SDK" },
  { id: "token", label: "TOKEN" },
  { id: "openclaw", label: "OPENCLAW" },
  { id: "agents", label: "AGENTS" },
];

// ── Particle Canvas ──
function ParticleField() {
  const canvasRef = useRef(null);
  const particles = useRef([]);
  const animRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let w = canvas.width = window.innerWidth;
    let h = canvas.height = window.innerHeight * 6;

    const init = () => {
      particles.current = Array.from({ length: 80 }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.3, vy: (Math.random() - 0.5) * 0.15 - 0.05,
        r: Math.random() * 1.5 + 0.3, a: Math.random() * 0.4 + 0.05,
      }));
    };
    init();

    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      particles.current.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = w; if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h; if (p.y > h) p.y = 0;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(77,166,255,${p.a})`;
        ctx.fill();
      });
      // connection lines
      for (let i = 0; i < particles.current.length; i++) {
        for (let j = i + 1; j < particles.current.length; j++) {
          const dx = particles.current[i].x - particles.current[j].x;
          const dy = particles.current[i].y - particles.current[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 150) {
            ctx.beginPath();
            ctx.moveTo(particles.current[i].x, particles.current[i].y);
            ctx.lineTo(particles.current[j].x, particles.current[j].y);
            ctx.strokeStyle = `rgba(77,166,255,${0.04 * (1 - dist / 150)})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }
      animRef.current = requestAnimationFrame(draw);
    };
    draw();
    const onResize = () => { w = canvas.width = window.innerWidth; h = canvas.height = window.innerHeight * 6; init(); };
    window.addEventListener("resize", onResize);
    return () => { cancelAnimationFrame(animRef.current); window.removeEventListener("resize", onResize); };
  }, []);

  return <canvas ref={canvasRef} style={{ position: "fixed", top: 0, left: 0, width: "100%", height: "100%", pointerEvents: "none", zIndex: 0, opacity: 0.6 }} />;
}

// ── Animated counter ──
function AnimNum({ target, suffix = "", duration = 2000 }) {
  const [val, setVal] = useState(0);
  const ref = useRef(null);
  const started = useRef(false);

  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting && !started.current) {
        started.current = true;
        const start = performance.now();
        const tick = (now) => {
          const p = Math.min((now - start) / duration, 1);
          const ease = 1 - Math.pow(1 - p, 3);
          setVal(Math.round(target * ease));
          if (p < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      }
    }, { threshold: 0.3 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [target, duration]);

  return <span ref={ref}>{val}{suffix}</span>;
}

// ── Reveal on scroll ──
function Reveal({ children, delay = 0, style = {} }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setVisible(true); }, { threshold: 0.15 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);
  return (
    <div ref={ref} style={{
      ...style,
      opacity: visible ? 1 : 0,
      transform: visible ? "translateY(0)" : "translateY(30px)",
      transition: `all 0.8s cubic-bezier(0.16,1,0.3,1) ${delay}s`,
    }}>{children}</div>
  );
}

// ── Code block ──
function CodeBlock({ code, lang = "python" }) {
  return (
    <pre style={{
      background: "#070b12", border: `1px solid ${C.border}`, borderRadius: 6,
      padding: "16px 20px", fontFamily: "'JetBrains Mono', monospace", fontSize: 12,
      color: C.frost, overflowX: "auto", lineHeight: 1.7, position: "relative",
    }}>
      <span style={{ position: "absolute", top: 8, right: 12, fontSize: 9, color: C.slateD, letterSpacing: 1 }}>{lang.toUpperCase()}</span>
      <code>{code}</code>
    </pre>
  );
}

// ── Glowing card ──
function GlowCard({ children, style = {}, accent = C.blue }) {
  const [hover, setHover] = useState(false);
  return (
    <div
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        background: C.bgCard, border: `1px solid ${hover ? accent + "40" : C.border}`,
        borderRadius: 8, padding: "28px 24px", position: "relative", overflow: "hidden",
        transition: "all 0.4s ease", cursor: "default",
        boxShadow: hover ? `0 0 40px ${accent}10, inset 0 1px 0 ${accent}15` : "none",
        ...style,
      }}
    >
      {hover && <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 1, background: `linear-gradient(90deg, transparent, ${accent}60, transparent)` }} />}
      {children}
    </div>
  );
}

// ── Section wrapper ──
function Section({ id, children, style = {} }) {
  return (
    <section id={id} style={{ position: "relative", zIndex: 1, padding: "100px 0", ...style }}>
      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "0 32px" }}>{children}</div>
    </section>
  );
}

// ── Section label ──
function SectionLabel({ text, sub }) {
  return (
    <div style={{ marginBottom: 48 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
        <div style={{ width: 32, height: 1, background: C.blue }} />
        <span style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 11, fontWeight: 600, letterSpacing: 3 }}>{text}</span>
      </div>
      {sub && <h2 style={{ color: C.ice, fontFamily: "'Space Mono', 'JetBrains Mono', monospace", fontSize: 32, fontWeight: 700, lineHeight: 1.2, marginTop: 8 }}>{sub}</h2>}
    </div>
  );
}

// ── Pipeline step ──
function PipelineStep({ num, title, desc, icon, delay }) {
  return (
    <Reveal delay={delay} style={{ flex: 1 }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center", position: "relative" }}>
        <div style={{
          width: 64, height: 64, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
          background: `linear-gradient(135deg, ${C.blueDark}, ${C.bgCard})`,
          border: `2px solid ${C.blue}30`, fontSize: 24, marginBottom: 16,
          boxShadow: `0 0 30px ${C.blue}10`,
        }}>{num}</div>
        <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 6 }}>STEP {num}</div>
        <div style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 14, fontWeight: 600, marginBottom: 8 }}>{title}</div>
        <div style={{ color: C.slate, fontSize: 12, lineHeight: 1.6, maxWidth: 200 }}>{desc}</div>
      </div>
    </Reveal>
  );
}

// ── Nav dot ──
function NavDot({ active, label, onClick }) {
  return (
    <button onClick={onClick} title={label} style={{
      width: active ? 24 : 8, height: 8, borderRadius: 4, border: "none", cursor: "pointer",
      background: active ? C.blue : C.border, transition: "all 0.3s",
      opacity: active ? 1 : 0.5,
    }} />
  );
}

// ═══════════════════════════════════════════════════════════════
// MAIN DOCS PAGE
// ═══════════════════════════════════════════════════════════════

export default function OracleSentinelDocs() {
  const [activeSection, setActiveSection] = useState("hero");
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const onScroll = () => {
      setScrollY(window.scrollY);
      const sections = SECTIONS.map(s => {
        const el = document.getElementById(s.id);
        if (!el) return { id: s.id, top: 99999 };
        return { id: s.id, top: Math.abs(el.getBoundingClientRect().top) };
      });
      sections.sort((a, b) => a.top - b.top);
      if (sections[0]) setActiveSection(sections[0].id);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div style={{ background: C.bg, color: C.frost, fontFamily: "'Syne', 'JetBrains Mono', monospace", minHeight: "100vh", position: "relative", overflowX: "hidden" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Syne:wght@400;500;600;700;800&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        ::selection { background: ${C.blue}30; color: ${C.ice}; }
        ::-webkit-scrollbar { width: 5px; } ::-webkit-scrollbar-track { background: ${C.bg}; } ::-webkit-scrollbar-thumb { background: ${C.borderL}; border-radius: 3px; }
        html { scroll-behavior: smooth; }
        body { background: ${C.bg}; }
        @keyframes heroGlow { 0%, 100% { opacity: 0.3; } 50% { opacity: 0.7; } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-8px); } }
        @keyframes scanline { 0% { top: -10%; } 100% { top: 110%; } }
        @keyframes typewriter { from { width: 0; } to { width: 100%; } }
      `}</style>

      <ParticleField />

      {/* ── Scanline effect ── */}
      <div style={{
        position: "fixed", top: 0, left: 0, right: 0, bottom: 0, pointerEvents: "none", zIndex: 9998,
        background: "repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(13,40,71,0.015) 3px, rgba(13,40,71,0.015) 4px)",
      }} />

      {/* ── Side nav dots ── */}
      <div style={{
        position: "fixed", right: 20, top: "50%", transform: "translateY(-50%)", zIndex: 100,
        display: "flex", flexDirection: "column", gap: 8, alignItems: "flex-end",
      }}>
        {SECTIONS.map(s => <NavDot key={s.id} active={activeSection === s.id} label={s.label} onClick={() => scrollTo(s.id)} />)}
      </div>

      {/* ── Top bar ── */}
      <div style={{
        position: "fixed", top: 0, left: 0, right: 0, zIndex: 100,
        background: scrollY > 50 ? `${C.bg}ee` : "transparent",
        backdropFilter: scrollY > 50 ? "blur(12px)" : "none",
        borderBottom: scrollY > 50 ? `1px solid ${C.border}` : "none",
        transition: "all 0.3s", padding: "12px 32px",
        display: "flex", justifyContent: "space-between", alignItems: "center",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ color: C.blue, fontSize: 8, animation: "pulse 2s infinite" }}>●</span>
          <a href="/" style={{ display: "flex", alignItems: "center", gap: 8, textDecoration: "none" }}>
            <img src="/logo.png" alt="Oracle Sentinel" style={{ width: 60, height: 60, borderRadius: "50%" }} />
            <span style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 12, fontWeight: 700, letterSpacing: 3 }}>ORACLE SENTINEL</span>
          </a>
          <span style={{ color: C.slateD, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, letterSpacing: 1, marginLeft: 4 }}>DOCS</span>
        </div>
        <div style={{ display: "flex", gap: 24 }}>
          {["architecture", "api", "sdk", "token", "openclaw"].map(s => (
            <button key={s} onClick={() => scrollTo(s)} style={{
              background: "none", border: "none", color: activeSection === s ? C.blue : C.slate,
              fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 1.5, cursor: "pointer",
              transition: "color 0.2s", textTransform: "uppercase",
            }}>{s}</button>
          ))}
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* HERO */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Section id="hero" style={{ padding: "160px 0 120px", minHeight: "100vh", display: "flex", alignItems: "center" }}>
        <div style={{ textAlign: "center" }}>
          {/* Glow orb */}
          <div style={{
            position: "absolute", top: "20%", left: "50%", transform: "translateX(-50%)",
            width: 500, height: 500, borderRadius: "50%",
            background: `radial-gradient(circle, ${C.blue}08 0%, transparent 70%)`,
            animation: "heroGlow 4s ease-in-out infinite", pointerEvents: "none",
          }} />

          <Reveal>
            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: C.blue, letterSpacing: 4, marginBottom: 20 }}>
              POLYMARKET PREDICTION INTELLIGENCE
            </div>
          </Reveal>

          <Reveal delay={0.1}>
            <h1 style={{ fontFamily: "'Syne', sans-serif", fontSize: "clamp(48px, 7vw, 80px)", fontWeight: 800, lineHeight: 1.05, color: C.ice, marginBottom: 24 }}>
              ORACLE<br />
              <span style={{ color: C.blue }}>SENTINEL</span>
            </h1>
          </Reveal>

          <Reveal delay={0.2}>
            <p style={{ fontSize: 16, color: C.frost, maxWidth: 560, lineHeight: 1.8, marginBottom: 40, margin: "0 auto 40px" }}>
              Autonomous AI system that scans prediction markets 24/7, detects mispriced opportunities using multi-model intelligence, and tracks its own accuracy with radical transparency.
            </p>
          </Reveal>
        </div>
      </Section>

      {/* ── SOCIAL PROOF BAR ── */}
      <Section style={{ padding: "48px 0", borderTop: `1px solid ${C.border}` }}>
        <Reveal>
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 40, flexWrap: "wrap" }}>
            {[
              { l: "Powered by", v: "Anthropic Claude", c: C.blue },
              { l: "Data from", v: "Polymarket", c: C.teal },
              { l: "Automated via", v: "OpenClaw", c: C.amber },
              { l: "Alerts via", v: "Telegram", c: C.frost },
              { l: "Payments via", v: "PayAI Network", c: C.green },
              { l: "Listed on", v: "JUICE", c: C.amber },
              { l: "Built on", v: "Solana", c: C.blue },
            ].map((b, i) => (
              <div key={i} style={{ textAlign: "center" }}>
                <div style={{ color: C.slateD, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, letterSpacing: 2, marginBottom: 4 }}>{b.l}</div>
                <div style={{ color: b.c, fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 600 }}>{b.v}</div>
              </div>
            ))}
          </div>
        </Reveal>
      </Section>


      {/* ═══════════════════════════════════════════════════════ */}
      {/* PROBLEM */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Section id="problem" style={{ borderTop: `1px solid ${C.border}` }}>
        <Reveal><SectionLabel text="THE PROBLEM" sub="Prediction markets are inefficient." /></Reveal>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32 }}>
          <Reveal delay={0.1}>
            <GlowCard accent={C.red}>
              <div style={{ color: C.red, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 12 }}>WITHOUT ORACLE SENTINEL</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                {[
                  "Manual scanning of hundreds of markets",
                  "Emotional trading decisions based on gut feel",
                  "No systematic edge calculation",
                  "No accountability — wins are remembered, losses forgotten",
                  "Information asymmetry favors whales",
                ].map((t, i) => (
                  <div key={i} style={{ display: "flex", gap: 10, fontSize: 13, color: C.frost, lineHeight: 1.6 }}>
                    <span style={{ color: C.red, fontSize: 14, flexShrink: 0 }}>✕</span>{t}
                  </div>
                ))}
              </div>
            </GlowCard>
          </Reveal>
          <Reveal delay={0.2}>
            <GlowCard accent={C.teal}>
              <div style={{ color: C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 12 }}>WITH ORACLE SENTINEL</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                {[
                  "Autonomous 4-hour market scanning cycles",
                  "AI probability assessment with reasoning chains",
                  "Quantified edge with confidence scoring",
                  "Every prediction tracked, every result transparent",
                  "Whale signal detection levels the playing field",
                ].map((t, i) => (
                  <div key={i} style={{ display: "flex", gap: 10, fontSize: 13, color: C.frost, lineHeight: 1.6 }}>
                    <span style={{ color: C.teal, fontSize: 14, flexShrink: 0 }}>✓</span>{t}
                  </div>
                ))}
              </div>
            </GlowCard>
          </Reveal>
        </div>
      </Section>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* ARCHITECTURE */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Section id="architecture" style={{ borderTop: `1px solid ${C.border}` }}>
        <Reveal><SectionLabel text="SYSTEM ARCHITECTURE" sub="Intelligence stack, end to end." /></Reveal>
        <Reveal delay={0.1}>
          <div style={{ background: C.bgCard, border: `1px solid ${C.border}`, borderRadius: 8, padding: "40px 36px", position: "relative" }}>
            {/* Architecture diagram */}
            <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
              {/* Layer 1: Data Ingestion */}
              <div style={{ display: "flex", gap: 16, justifyContent: "center", flexWrap: "wrap" }}>
                {["Polymarket API", "News Scrapers", "Whale Tracker", "Order Book"].map((t, i) => (
                  <div key={i} style={{
                    background: C.bg, border: `1px solid ${C.border}`, borderRadius: 4,
                    padding: "10px 20px", fontFamily: "'JetBrains Mono', monospace", fontSize: 11,
                    color: C.frost, textAlign: "center",
                  }}>
                    <div style={{ color: C.slate, fontSize: 8, letterSpacing: 1.5, marginBottom: 4 }}>INPUT</div>
                    {t}
                  </div>
                ))}
              </div>
              {/* Arrow */}
              <div style={{ textAlign: "center", color: C.blue, fontSize: 20, padding: "12px 0", opacity: 0.5 }}>▼</div>
              {/* Layer 2: Processing */}
              <div style={{ display: "flex", gap: 16, justifyContent: "center" }}>
                {[
                  { t: "Haiku 3.5", s: "Fact Extraction", c: C.amber },
                  { t: "Sonnet 4.5", s: "Probability Assessment", c: C.blue },
                  { t: "Edge Calculator", s: "Signal Generation", c: C.teal },
                ].map((item, i) => (
                  <div key={i} style={{
                    background: `linear-gradient(135deg, ${item.c}08, ${C.bgCard})`,
                    border: `1px solid ${item.c}25`, borderRadius: 6,
                    padding: "14px 24px", textAlign: "center", flex: 1,
                  }}>
                    <div style={{ color: item.c, fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 600 }}>{item.t}</div>
                    <div style={{ color: C.slate, fontSize: 10, marginTop: 4 }}>{item.s}</div>
                  </div>
                ))}
              </div>
              <div style={{ textAlign: "center", color: C.blue, fontSize: 20, padding: "12px 0", opacity: 0.5 }}>▼</div>
              {/* Layer 3: Storage & Output */}
              <div style={{ display: "flex", gap: 16, justifyContent: "center" }}>
                {[
                  { t: "SQLite Database", c: C.blue },
                  { t: "Accuracy Tracker", s: "1h / 6h / 24h Snapshots", c: C.teal },
                ].map((item, i) => (
                  <div key={i} style={{
                    background: C.bg, border: `1px solid ${item.c}20`, borderRadius: 6,
                    padding: "14px 28px", textAlign: "center", flex: 1,
                  }}>
                    <div style={{ color: item.c, fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 600 }}>{item.t}</div>
                    <div style={{ color: C.slate, fontSize: 10, marginTop: 4 }}>{item.s}</div>
                  </div>
                ))}
              </div>
              <div style={{ textAlign: "center", color: C.blue, fontSize: 20, padding: "12px 0", opacity: 0.5 }}>▼</div>
              {/* Layer 4: Distribution */}
              <div style={{ display: "flex", gap: 16, justifyContent: "center" }}>
                {[
                  { t: "Terminal Dashboard" },
                  { t: "Telegram Bot" },
                  { t: "REST API" },
                ].map((item, i) => (
                  <div key={i} style={{
                    background: `linear-gradient(135deg, ${C.blueDark}40, ${C.bg})`,
                    border: `1px solid ${C.borderL}`, borderRadius: 6,
                    padding: "14px 20px", textAlign: "center", flex: 1,
                  }}>
                    <div style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 600 }}>{item.t}</div>
                    <div style={{ color: C.slate, fontSize: 10, marginTop: 4 }}>{item.s}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Reveal>
      </Section>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* FEATURES */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Section id="features" style={{ borderTop: `1px solid ${C.border}` }}>
        <Reveal><SectionLabel text="CORE CAPABILITIES" sub="What makes Oracle Sentinel different." /></Reveal>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 20 }}>
          {[
            { title: "Dual-Model AI Brain", desc: "Stage 1: Claude Haiku extracts facts. Stage 2: Claude Sonnet assesses probability. Two models, one verdict — eliminating single-model bias.", accent: C.blue },
            { title: "Whale Signal Detection", desc: "Tracks large bids/asks, order book imbalance, and sentiment shifts. When smart money moves, Oracle Sentinel sees it first.", accent: C.teal },
            { title: "Quantified Edge", desc: "Every signal includes exact edge percentage: the difference between AI probability and market price. No vague calls — pure math.", accent: C.amber },
            { title: "Radical Transparency", desc: "Every prediction is tracked at 1h, 6h, and 24h intervals. No hiding losses. Accuracy is computed live, not cherry-picked.", accent: C.red },
            { title: "Autonomous Operation", desc: "OpenClaw cron triggers every 4 hours. Zero human intervention. Scan, analyze, signal, track — all automated.", accent: C.green },
            { title: "Safety Override", desc: "Even if AI says BUY, high edge + medium confidence triggers NO_TRADE override. The system protects against its own overconfidence.", accent: C.blue },
          ].map((f, i) => (
            <Reveal key={i} delay={i * 0.08}>
              <GlowCard accent={f.accent} style={{ height: "100%" }}>
                <div style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 14, fontWeight: 600, marginBottom: 10, lineHeight: 1.4 }}>{f.title}</div>
                <div style={{ color: C.slate, fontSize: 13, lineHeight: 1.7 }}>{f.desc}</div>
              </GlowCard>
            </Reveal>
          ))}
        </div>
      </Section>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* QUALITY FILTERS */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Section id="filters" style={{ borderTop: `1px solid ${C.border}` }}>
        <Reveal><SectionLabel text="QUALITY FILTERS" sub="Intelligence gates that ensure signal reliability." /></Reveal>
        
        <Reveal delay={0.1}>
          <div style={{ marginBottom: 32 }}>
            <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>MARKET QUALITY GATES</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              {[
                { 
                  title: "Short-Term Filter", 
                  desc: "Markets closing in <24 hours are automatically skipped. Short-term price predictions are inherently volatile and unpredictable — Oracle Sentinel focuses on longer-timeframe opportunities where analysis has higher signal-to-noise ratio.",
                  color: C.amber
                },
                { 
                  title: "Liquidity Filter", 
                  desc: "Markets with <$10,000 liquidity are rejected. Thin markets are easily manipulated by single large trades and don't reflect genuine price discovery. Only liquid markets with real two-sided depth are analyzed.",
                  color: C.teal
                },
                { 
                  title: "Timestamp Validation", 
                  desc: "Closed or expired markets are automatically filtered out with 2-hour buffer. The system validates end dates before analysis to prevent wasting compute on resolved events. Current UTC time is injected into AI context for temporal awareness.",
                  color: C.blue
                },
                { 
                  title: "Resolution Parser", 
                  desc: "Market descriptions are parsed to extract exact resolution criteria — thresholds, time ranges, data sources, and special cases. This structured parsing ensures AI analyzes based on actual resolution mechanics, not just question titles.",
                  color: C.green
                },
              ].map((f, i) => (
                <Reveal key={i} delay={0.1 + i * 0.05}>
                  <GlowCard accent={f.color} style={{ height: "100%" }}>
                    <div style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 14, fontWeight: 600, marginBottom: 10, lineHeight: 1.4 }}>{f.title}</div>
                    <div style={{ color: C.slate, fontSize: 13, lineHeight: 1.7 }}>{f.desc}</div>
                  </GlowCard>
                </Reveal>
              ))}
            </div>
          </div>
        </Reveal>

        <Reveal delay={0.3}>
          <div style={{ marginBottom: 32 }}>
            <div style={{ color: C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>CATEGORY-SPECIFIC ANALYSIS</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
              {[
                { 
                  category: "Crypto Markets", 
                  calibration: [
                    "Bitcoin/Ethereum can swing 5-10% in 24 hours",
                    "Short-term price moves (<48h) are extremely difficult to predict",
                    "24/7 markets mean overnight volatility is common",
                    "Historical volatility: BTC averages 3-5% daily (10%+ in volatile periods)",
                  ],
                  color: C.amber
                },
                { 
                  category: "Sports Markets", 
                  calibration: [
                    "Recent form (last 10 matches) matters more than reputation",
                    "League standings show current position and gap to leader",
                    "Head-to-head stats reveal matchup-specific dynamics",
                    "Betting streaks (goals, clean sheets) indicate momentum",
                  ],
                  color: C.green
                },
                { 
                  category: "Political Markets", 
                  calibration: [
                    "Politicians often delay, extend deadlines, or find last-minute compromises",
                    "Government shutdowns usually resolve with temporary measures",
                    "Announced intentions ≠ actual outcomes (consider base rates)",
                    "Political brinkmanship goes to the wire then resolves",
                  ],
                  color: C.blue
                },
              ].map((cat, i) => (
                <Reveal key={i} delay={0.3 + i * 0.05}>
                  <GlowCard accent={cat.color} style={{ height: "100%" }}>
                    <div style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 600, marginBottom: 12 }}>{cat.category}</div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      {cat.calibration.map((rule, j) => (
                        <div key={j} style={{ display: "flex", gap: 8, fontSize: 12, color: C.slate, lineHeight: 1.6 }}>
                          <span style={{ color: cat.color, flexShrink: 0 }}>•</span>
                          <span>{rule}</span>
                        </div>
                      ))}
                    </div>
                  </GlowCard>
                </Reveal>
              ))}
            </div>
          </div>
        </Reveal>

        <Reveal delay={0.5}>
          <div>
            <div style={{ color: C.red, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>NEWS QUALITY CONTROL</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
              {[
                { 
                  title: "Date Validation", 
                  desc: "Articles with impossible future dates are automatically rejected. News claiming to be from tomorrow is either misdated or fabricated — the system validates publish timestamps against current time.",
                  color: C.red
                },
                { 
                  title: "Freshness Filter", 
                  desc: "Articles older than 30 days are filtered out. Stale news lacks relevance for real-time market analysis. Only recent, contextual information is fed to the AI assessment layer.",
                  color: C.amber
                },
                { 
                  title: "Source Diversity", 
                  desc: "News scoring prioritizes multiple credible sources over single-source claims. Trusted outlets (Reuters, Bloomberg, AP) receive bonus weighting. The system discourages echo chambers.",
                  color: C.teal
                },
              ].map((item, i) => (
                <Reveal key={i} delay={0.5 + i * 0.05}>
                  <GlowCard accent={item.color} style={{ height: "100%" }}>
                    <div style={{ color: item.color, fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 600, marginBottom: 8 }}>{item.title}</div>
                    <div style={{ color: C.slate, fontSize: 12, lineHeight: 1.7 }}>{item.desc}</div>
                  </GlowCard>
                </Reveal>
              ))}
            </div>
          </div>
        </Reveal>
      </Section>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* PIPELINE */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Section id="pipeline" style={{ borderTop: `1px solid ${C.border}` }}>
        <Reveal><SectionLabel text="ANALYSIS PIPELINE" sub="From raw data to actionable signal." /></Reveal>
        <div style={{ display: "flex", gap: 8, alignItems: "flex-start", position: "relative" }}>
          {/* Connector line */}
          <div style={{ position: "absolute", top: 32, left: "10%", right: "10%", height: 1, background: `linear-gradient(90deg, transparent, ${C.blue}30, ${C.blue}30, transparent)`, zIndex: 0 }} />
          {[
            { num: "01", title: "INGEST", desc: "Pull markets, prices, volume, and news from Polymarket API" },
            { num: "02", title: "EXTRACT", desc: "Claude Haiku distills raw articles into structured facts" },
            { num: "03", title: "ASSESS", desc: "Claude Sonnet computes AI probability with full reasoning" },
            { num: "04", title: "SIGNAL", desc: "Edge calculator generates BUY_YES / BUY_NO / NO_TRADE" },
            { num: "05", title: "TRACK", desc: "Accuracy tracker snapshots at 1h, 6h, 24h intervals" },
          ].map((s, i) => (
            <PipelineStep key={i} num={s.num} title={s.title} desc={s.desc} icon={s.icon} delay={i * 0.1} />
          ))}
        </div>
      </Section>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* TECH STACK */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Section id="tech" style={{ borderTop: `1px solid ${C.border}` }}>
        <Reveal><SectionLabel text="TECHNOLOGY STACK" sub="Built for reliability and speed." /></Reveal>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          {[
            { cat: "AI / LLM", items: [{ n: "Claude Sonnet 4.5", d: "Probability assessment" }, { n: "Claude Haiku 3.5", d: "Fact extraction" }, { n: "OpenRouter", d: "API gateway" }] },
            { cat: "INFRA", items: [{ n: "OpenClaw", d: "Cron automation" }, { n: "Moltbook", d: "Social publishing" }, { n: "Telegram Bot API", d: "Alert distribution" }] },
          ].map((group, i) => (
            <Reveal key={i} delay={i * 0.1}>
              <GlowCard>
                <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>{group.cat}</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {group.items.map((item, j) => (
                    <div key={j} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 500 }}>{item.n}</span>
                      <span style={{ color: C.slateD, fontSize: 11 }}>{item.d}</span>
                    </div>
                  ))}
                </div>
              </GlowCard>
            </Reveal>
          ))}
        </div>
      </Section>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* ACCURACY */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Section id="accuracy" style={{ borderTop: `1px solid ${C.border}` }}>
        <Reveal><SectionLabel text="TRUST FRAMEWORK" sub="Don't trust claims. Verify data." /></Reveal>
        <Reveal delay={0.1}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
            {[
              { title: "Verifiable Track Record", desc: "Every signal is permanently recorded in the database the moment it's generated. No edits, no deletions, no retroactive changes. What the AI said is what the AI said.", color: C.blue },
              { title: "No Human Interference", desc: "From market scan to signal generation to accuracy tracking — zero manual override. The AI decides, publishes, and measures itself autonomously.", color: C.teal },
              { title: "Open Audit Trail", desc: "All predictions, signals, and market data are accessible via REST API. Anyone can independently verify every claim Oracle Sentinel makes.", color: C.amber },
            ].map((t, i) => (
              <Reveal key={i} delay={i * 0.08}>
                <GlowCard accent={t.color} style={{ height: "100%" }}>
                  <div style={{ color: t.color, fontFamily: "'JetBrains Mono', monospace", fontSize: 14, fontWeight: 700, marginBottom: 10 }}>{t.title}</div>
                  <div style={{ color: C.slate, fontSize: 13, lineHeight: 1.7 }}>{t.desc}</div>
                </GlowCard>
              </Reveal>
            ))}
          </div>
        </Reveal>
      </Section>

      {/* ═══════════════════════════════════════════════════════ */}

      {/* ═══════════════════════════════════════════════════════ */}
      {/* SENTINEL CODE */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Section id="sentinel-code" style={{ borderTop: `1px solid ${C.border}` }}>
        <Reveal><SectionLabel text="SENTINEL CODE" sub="AI-Powered Code Analysis." /></Reveal>

        <Reveal delay={0.1}>
          <GlowCard accent={C.teal} style={{ marginBottom: 32 }}>
            <div style={{ color: C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>WHAT IS SENTINEL CODE</div>
            <p style={{ color: C.frost, fontSize: 14, lineHeight: 1.8, marginBottom: 16 }}>
              Sentinel Code is an AI-powered code analysis module that scans any public GitHub repository for security vulnerabilities, bugs, and code quality issues. It provides detailed reports with exact file locations, code snippets, and fix suggestions.
            </p>
            <p style={{ color: C.slate, fontSize: 13, lineHeight: 1.7 }}>
              Built for developers who want cleaner code and investors who want to verify the quality of projects they're holding. Drop a repo URL, get a comprehensive audit in 30-60 seconds.
            </p>
          </GlowCard>
        </Reveal>

        {/* Use Cases */}
        <Reveal delay={0.15}>
          <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>USE CASES</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 32 }}>
            {[
              { title: "For Developers", desc: "Catch security issues before hackers do. Find bugs, missing error handling, and code quality problems. Get AI-suggested fixes with exact code examples.", color: C.teal },
              { title: "For Investors", desc: "Verify if the project you're holding is actually well-built. Check for red flags like hardcoded secrets, SQL injection risks, or missing authentication.", color: C.amber },
              { title: "For Code Reviews", desc: "Automate the first pass of code review. Identify obvious issues so human reviewers can focus on architecture and logic.", color: C.blue },
              { title: "For Due Diligence", desc: "Before integrating a dependency or forking a project, understand its code quality and security posture.", color: C.green },
            ].map((item, i) => (
              <Reveal key={i} delay={0.15 + i * 0.05}>
                <GlowCard accent={item.color} style={{ height: "100%" }}>
                  <div style={{ color: item.color, fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 600, marginBottom: 8 }}>{item.title}</div>
                  <div style={{ color: C.slate, fontSize: 12, lineHeight: 1.7 }}>{item.desc}</div>
                </GlowCard>
              </Reveal>
            ))}
          </div>
        </Reveal>

        {/* What It Detects */}
        <Reveal delay={0.2}>
          <div style={{ color: C.red, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>WHAT IT DETECTS</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 14, marginBottom: 32 }}>
            {[
              { cat: "CRITICAL", items: ["SQL Injection", "XSS Vulnerabilities", "Hardcoded Secrets", "API Keys Exposed"], color: C.red },
              { cat: "BUGS", items: ["Null Pointers", "Race Conditions", "Unhandled Exceptions", "Memory Leaks"], color: C.amber },
              { cat: "QUALITY", items: ["No Error Handling", "No Input Validation", "Code Duplication", "Complex Functions"], color: C.blue },
              { cat: "IMPROVEMENTS", items: ["Missing Type Hints", "No Documentation", "No Unit Tests", "Outdated Patterns"], color: C.green },
            ].map((cat, i) => (
              <Reveal key={i} delay={0.2 + i * 0.04}>
                <GlowCard accent={cat.color} style={{ padding: "20px 16px" }}>
                  <div style={{ color: cat.color, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 1.5, marginBottom: 12 }}>{cat.cat}</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {cat.items.map((item, j) => (
                      <div key={j} style={{ color: C.frost, fontSize: 11, display: "flex", alignItems: "center", gap: 6 }}>
                        <span style={{ color: cat.color, fontSize: 8 }}>●</span>{item}
                      </div>
                    ))}
                  </div>
                </GlowCard>
              </Reveal>
            ))}
          </div>
        </Reveal>

        {/* Output Format */}
        <Reveal delay={0.25}>
          <div style={{ color: C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>OUTPUT FORMAT</div>
          <GlowCard accent={C.teal} style={{ marginBottom: 32 }}>
            <div style={{ background: C.bg, border: `1px solid ${C.border}`, borderRadius: 6, padding: "20px", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, lineHeight: 1.7, color: C.frost, overflowX: "auto" }}>
              <div style={{ color: C.blue, marginBottom: 8 }}>ORACLE SENTINEL CODE REVIEW</div>
              <div style={{ color: C.slate, marginBottom: 16 }}>Repo: github.com/user/project | Python 92% | 12 files analyzed</div>
              <div style={{ color: C.red, marginBottom: 4 }}>CRITICAL ISSUES (2)</div>
              <div style={{ color: C.frost, marginBottom: 2 }}>1. SQL Injection Vulnerability</div>
              <div style={{ color: C.slate, marginBottom: 2 }}>   File: app/routes.py:47</div>
              <div style={{ color: C.slate, marginBottom: 2 }}>   Code: f"SELECT * FROM users WHERE id = &#123;user_input&#125;"</div>
              <div style={{ color: C.teal, marginBottom: 12 }}>   Fix: Use parameterized queries</div>
              <div style={{ color: C.amber, marginBottom: 4 }}>WARNINGS (4)</div>
              <div style={{ color: C.slate, marginBottom: 12 }}>   - No rate limiting on API endpoints (routes.py)</div>
              <div style={{ color: C.green, marginBottom: 4 }}>IMPROVEMENTS (5)</div>
              <div style={{ color: C.slate, marginBottom: 12 }}>   - Add type hints for better maintainability</div>
            </div>
          </GlowCard>
        </Reveal>

        {/* How to Use */}
        <Reveal delay={0.3}>
          <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>HOW TO USE</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <GlowCard accent={C.blue}>
              <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 12, fontWeight: 600, marginBottom: 12 }}>Web Interface</div>
              <div style={{ color: C.frost, fontSize: 13, lineHeight: 1.7, marginBottom: 16 }}>
                Visit oraclesentinel.xyz/code, paste any GitHub repository URL, and click Analyze. Results appear in 30-60 seconds.
              </div>
              <a href="/code" style={{
                display: "inline-block", background: `linear-gradient(135deg, ${C.blue}, ${C.blueMid})`,
                color: "#fff", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, fontWeight: 600,
                letterSpacing: 1, padding: "10px 16px", borderRadius: 4, textDecoration: "none",
              }}>OPEN CODE ANALYZER</a>
            </GlowCard>
            <GlowCard accent={C.teal}>
              <div style={{ color: C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 12, fontWeight: 600, marginBottom: 12 }}>API Endpoint</div>
              <div style={{ background: C.bg, border: `1px solid ${C.border}`, borderRadius: 4, padding: "12px", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: C.frost, marginBottom: 12 }}>
                POST /api/code/analyze<br/>
                &#123; "repo_url": "https://github.com/user/repo" &#125;
              </div>
              <div style={{ color: C.slate, fontSize: 11 }}>FREE for all users. No authentication required.</div>
            </GlowCard>
          </div>
        </Reveal>

        {/* Supported Languages */}
        <Reveal delay={0.35}>
          <div style={{ marginTop: 32, color: C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>SUPPORTED LANGUAGES</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            {["Python", "JavaScript", "TypeScript", "Rust", "Solidity", "Go", "Java", "C++", "C", "Ruby", "PHP", "React JSX", "React TSX", "Solana Programs", "Smart Contracts"].map((lang, i) => (
              <span key={i} style={{
                background: C.bgCard, border: `1px solid ${C.border}`, borderRadius: 4,
                padding: "6px 14px", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: C.frost,
              }}>{lang}</span>
            ))}
          </div>
        </Reveal>
      </Section>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* API REFERENCE */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Section id="api" style={{ borderTop: `1px solid ${C.border}` }}>
        <Reveal><SectionLabel text="API REFERENCE" sub="Integrate Oracle Sentinel data." /></Reveal>
        
        {/* Free Endpoints */}
        <Reveal delay={0.1}>
          <div style={{ marginBottom: 32 }}>
            <div style={{ color: C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>FREE ENDPOINTS</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {[
                { method: "GET", path: "/api/signals", desc: "Active BUY_YES and BUY_NO trading signals", res: '[ { question, signal_type, edge, confidence, ai_probability, ... } ]' },
                { method: "GET", path: "/api/markets", desc: "All monitored markets with current prices", res: '[ { question, yes_price, no_price, volume, liquidity, slug } ]' },
                { method: "GET", path: "/api/predictions", desc: "Tracked predictions with price snapshots", res: '[ { question, signal_type, edge_at_signal, price_after_1h, ... } ]' },
                { method: "GET", path: "/api/dashboard", desc: "Complete dashboard payload", res: '{ active_signals, markets, predictions, accuracy_stats, ... }' },
                { method: "GET", path: "/api/health", desc: "System health check", res: '{ status: "ok", markets: 79, server_time: "..." }' },
                { method: "POST", path: "/api/code/analyze", desc: "Analyze GitHub repository", res: '{ repo, files_analyzed, languages, analysis }' },
                { method: "GET", path: "/api/code/health", desc: "Code analyzer health check", res: '{ status: "ok", service: "sentinel-code" }' },
              ].map((ep, i) => (
                <GlowCard key={i} style={{ padding: "14px 20px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
                    <span style={{ color: C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, fontWeight: 700, background: `${C.teal}15`, padding: "3px 8px", borderRadius: 3 }}>{ep.method}</span>
                    <span style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 600 }}>{ep.path}</span>
                    <span style={{ color: C.slate, fontSize: 11, marginLeft: "auto" }}>{ep.desc}</span>
                  </div>
                  <div style={{ background: C.bg, border: `1px solid ${C.border}`, borderRadius: 4, padding: "6px 12px", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: C.frost, overflowX: "auto" }}>{ep.res}</div>
                </GlowCard>
              ))}
            </div>
          </div>
        </Reveal>

        {/* Protected Endpoints */}
        <Reveal delay={0.2}>
          <div style={{ marginBottom: 32 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
              <div style={{ color: C.amber, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2 }}>PROTECTED ENDPOINTS</div>
              <span style={{ color: C.slateD, fontSize: 10, fontFamily: "'JetBrains Mono', monospace" }}>x402 Payment Protocol</span>
            </div>
            <div style={{ background: C.bgCard, border: `1px solid ${C.border}`, borderRadius: 8, overflow: "hidden", marginBottom: 16 }}>
              <div style={{ display: "grid", gridTemplateColumns: "70px 220px 1fr 80px", gap: 12, padding: "12px 16px", borderBottom: `1px solid ${C.border}`, background: C.bgPanel }}>
                <span style={{ color: C.slate, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, letterSpacing: 1 }}>METHOD</span>
                <span style={{ color: C.slate, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, letterSpacing: 1 }}>ENDPOINT</span>
                <span style={{ color: C.slate, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, letterSpacing: 1 }}>DESCRIPTION</span>
                <span style={{ color: C.slate, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, letterSpacing: 1, textAlign: "right" }}>PRICE</span>
              </div>
              {[
                { m: "GET", p: "/api/v1/signal/{slug}", d: "Trading signal for specific market", price: "$0.01" },
                { m: "GET", p: "/api/v1/analysis/{slug}", d: "Full AI analysis with reasoning", price: "$0.03" },
                { m: "GET", p: "/api/v1/whale/{slug}", d: "Whale trading activity", price: "$0.02" },
                { m: "GET", p: "/api/v1/bulk", d: "Top 10 active signals", price: "$0.08" },
                { m: "POST", p: "/api/v1/analyze", d: "Analyze any Polymarket URL", price: "$0.05" },
              ].map((ep, i) => (
                <div key={i} style={{ display: "grid", gridTemplateColumns: "70px 220px 1fr 80px", gap: 12, padding: "12px 16px", borderBottom: i < 4 ? `1px solid ${C.border}` : "none" }}>
                  <span style={{ color: ep.m === "POST" ? C.amber : C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, fontWeight: 600 }}>{ep.m}</span>
                  <span style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>{ep.p}</span>
                  <span style={{ color: C.frost, fontSize: 11 }}>{ep.d}</span>
                  <span style={{ color: C.amber, fontFamily: "'JetBrains Mono', monospace", fontSize: 11, fontWeight: 600, textAlign: "right" }}>{ep.price}</span>
                </div>
              ))}
            </div>
            <div style={{ padding: "14px 18px", background: `${C.teal}08`, border: `1px solid ${C.teal}25`, borderRadius: 6 }}>
              <span style={{ color: C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>Hold 1,000+ $OSAI = FREE unlimited access to all protected endpoints</span>
            </div>
          </div>
        </Reveal>

        {/* Usage Example */}
        <Reveal delay={0.3}>
          <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 12 }}>USAGE EXAMPLE</div>
          <CodeBlock lang="python" code={`import requests

# Free endpoint
signals = requests.get("https://oraclesentinel.xyz/api/signals").json()

for signal in signals:
    print(f"[{signal['signal_type']}] {signal['question']}")
    print(f"  Edge: {signal['edge']}% | Confidence: {signal['confidence']}")`} />
        </Reveal>
      </Section>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* SDK */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Section id="sdk" style={{ borderTop: `1px solid ${C.border}` }}>
        <Reveal><SectionLabel text="PYTHON SDK" sub="Integrate in minutes." /></Reveal>
        
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32 }}>
          <Reveal delay={0.1}>
            <GlowCard accent={C.blue} style={{ height: "100%" }}>
              <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>INSTALLATION</div>
              <CodeBlock lang="bash" code={`# Basic installation
pip install oracle-sentinel

# With Solana support (for token gating)
pip install oracle-sentinel[solana]`} />
              <div style={{ marginTop: 20, display: "flex", gap: 12 }}>
                <a href="https://pypi.org/project/oracle-sentinel/" target="_blank" rel="noopener noreferrer" style={{
                  background: `linear-gradient(135deg, ${C.blue}, ${C.blueMid})`,
                  color: "#fff", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, fontWeight: 600,
                  letterSpacing: 1, padding: "10px 16px", borderRadius: 4, textDecoration: "none",
                }}>VIEW ON PYPI</a>
                <a href="https://github.com/oraclesentinel/oracle-sentinel-python" target="_blank" rel="noopener noreferrer" style={{
                  background: "transparent", border: `1px solid ${C.borderL}`,
                  color: C.frost, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, fontWeight: 500,
                  letterSpacing: 1, padding: "10px 16px", borderRadius: 4, textDecoration: "none",
                }}>GITHUB</a>
              </div>
            </GlowCard>
          </Reveal>

          <Reveal delay={0.15}>
            <GlowCard accent={C.teal} style={{ height: "100%" }}>
              <div style={{ color: C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>FEATURES</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {[
                  "Automatic signature verification for token gating",
                  "Built-in x402 micropayments",
                  "FREE access for 1000+ $OSAI holders",
                  "Async support & type hints",
                  "Comprehensive error handling",
                ].map((f, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ color: C.teal, fontSize: 12 }}>✓</span>
                    <span style={{ color: C.frost, fontSize: 12 }}>{f}</span>
                  </div>
                ))}
              </div>
            </GlowCard>
          </Reveal>
        </div>

        <Reveal delay={0.2}>
          <div style={{ marginTop: 32, color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 12 }}>QUICK START</div>
          <CodeBlock lang="python" code={`from oracle_sentinel import OracleSentinelClient

# Initialize with private key for FREE access (if holding 1000+ $OSAI)
client = OracleSentinelClient(
    private_key="YOUR_SOLANA_PRIVATE_KEY"
)

# Get bulk signals (FREE for holders, $0.08 otherwise)
result = client.get_bulk_signals()
for signal in result["signals"]:
    print(f"{signal['signal']}: {signal['question']}")
    print(f"  Edge: {signal['edge']}%")

# Analyze any Polymarket URL
analysis = client.analyze_url("https://polymarket.com/event/...")
print(analysis["recommendation"])`} />
        </Reveal>
      </Section>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* TOKEN */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Section id="token" style={{ borderTop: `1px solid ${C.border}` }}>
        <Reveal><SectionLabel text="$OSAI TOKEN" sub="Unlock free API access." /></Reveal>
        
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32 }}>
          <Reveal delay={0.1}>
            <GlowCard accent={C.amber} style={{ height: "100%" }}>
              <div style={{ color: C.amber, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>CONTRACT ADDRESS</div>
              <div style={{ 
                display: "flex", alignItems: "center", gap: 12, padding: "14px", 
                background: C.bg, border: `1px solid ${C.border}`, borderRadius: 6,
                cursor: "pointer", transition: "all 0.2s",
              }}
              onClick={() => navigator.clipboard.writeText("HuDBwWRsa4bu8ueaCb7PPgJrqBeZDkcyFqMW5bbXpump")}
              >
                <span style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, flex: 1, wordBreak: "break-all" }}>HuDBwWRsa4bu8ueaCb7PPgJrqBeZDkcyFqMW5bbXpump</span>
                <span style={{ color: C.amber, fontSize: 12, flexShrink: 0 }}>COPY</span>
              </div>
              <div style={{ color: C.slateD, fontSize: 10, marginTop: 8, fontFamily: "'JetBrains Mono', monospace" }}>Click to copy</div>
              
              <div style={{ marginTop: 20, display: "flex", gap: 12 }}>
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
            </GlowCard>
          </Reveal>

          <Reveal delay={0.15}>
            <GlowCard accent={C.teal} style={{ height: "100%" }}>
              <div style={{ color: C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>HOLDER BENEFITS</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                {[
                  { tier: "1,000+ $OSAI", benefit: "FREE unlimited API access", color: C.teal },
                  { tier: "10,000+ $OSAI", benefit: "Premium tier (coming soon)", color: C.blue },
                  { tier: "100,000+ $OSAI", benefit: "VIP tier (coming soon)", color: C.amber },
                ].map((t, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 14, padding: "12px 14px", background: C.bg, border: `1px solid ${C.border}`, borderRadius: 6 }}>
                    <span style={{ color: t.color, fontFamily: "'JetBrains Mono', monospace", fontSize: 11, fontWeight: 600, minWidth: 110 }}>{t.tier}</span>
                    <span style={{ color: C.frost, fontSize: 11 }}>{t.benefit}</span>
                  </div>
                ))}
              </div>
            </GlowCard>
          </Reveal>
        </div>

        <Reveal delay={0.2}>
          <div style={{ marginTop: 32 }}>
            <GlowCard accent={C.green}>
              <div style={{ color: C.green, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 12 }}>HOW TOKEN GATING WORKS</div>
              <div style={{ color: C.frost, fontSize: 13, lineHeight: 1.8 }}>
                When you use the SDK with your Solana private key, the system verifies your wallet signature and checks your $OSAI balance on-chain. 
                If you hold 1,000+ tokens, all protected API endpoints become FREE. No payment required, no rate limits. 
                The verification happens automatically on each request.
              </div>
            </GlowCard>
          </div>
        </Reveal>
      </Section>

      {/* OPENCLAW INTEGRATION */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Section id="openclaw" style={{ borderTop: `1px solid ${C.border}` }}>
        <Reveal><SectionLabel text="AI AGENT LAYER" sub="OpenClaw: The brain behind the bot." /></Reveal>
        
        <Reveal delay={0.1}>
          <GlowCard accent={C.teal} style={{ marginBottom: 32 }}>
            <div style={{ color: C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>WHAT IS OPENCLAW</div>
            <p style={{ color: C.frost, fontSize: 14, lineHeight: 1.8, marginBottom: 16 }}>
              OpenClaw is an autonomous AI agent gateway running Claude Sonnet 4.5 directly on the Oracle Sentinel server. It's not a simple chatbot — it's a full AI agent with access to execute commands, fetch web data, search the internet, read/write files, and control the entire system via natural language.
            </p>
            <p style={{ color: C.slate, fontSize: 13, lineHeight: 1.7 }}>
              When you send a message via Telegram, OpenClaw receives it, reads Oracle Sentinel's skill configuration, decides what actions to take, executes them autonomously, and returns formatted results — all without human intervention.
            </p>
          </GlowCard>
        </Reveal>

        {/* Architecture Flow */}
        <Reveal delay={0.15}>
          <div style={{ background: C.bgCard, border: `1px solid ${C.border}`, borderRadius: 8, padding: "36px 32px", marginBottom: 32 }}>
            <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 24 }}>MESSAGE FLOW</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
              {[
                { label: "USER", text: "Telegram Message", color: C.frost },
                { label: "GATEWAY", text: "OpenClaw (port 18789)", color: C.blue },
                { label: "AI MODEL", text: "Claude Sonnet 4.5 via OpenRouter", color: C.amber },
                { label: "SKILL", text: "Read SKILL.md → Understand Oracle Sentinel", color: C.teal },
                { label: "EXECUTE", text: "Run tools: exec, web_fetch, web_search, browser", color: C.green },
                { label: "RESPONSE", text: "Format results → Send back to Telegram", color: C.frost },
              ].map((step, i) => (
                <div key={i}>
                  <div style={{ display: "flex", alignItems: "center", gap: 16, padding: "10px 0" }}>
                    <span style={{
                      color: step.color, fontFamily: "'JetBrains Mono', monospace", fontSize: 9,
                      letterSpacing: 1.5, width: 80, textAlign: "right", flexShrink: 0, opacity: 0.7,
                    }}>{step.label}</span>
                    <div style={{ width: 8, height: 8, borderRadius: "50%", background: step.color, opacity: 0.6, flexShrink: 0 }} />
                    <span style={{ color: C.frost, fontFamily: "'JetBrains Mono', monospace", fontSize: 12 }}>{step.text}</span>
                  </div>
                  {i < 5 && <div style={{ marginLeft: 96, width: 1, height: 12, background: `${C.blue}30` }} />}
                </div>
              ))}
            </div>
          </div>
        </Reveal>

        {/* Tools Grid */}
        <Reveal delay={0.2}>
          <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>AVAILABLE TOOLS</div>
        </Reveal>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 14, marginBottom: 32 }}>
          {[
            { name: "exec", desc: "Execute bash commands on server" },
            { name: "web_fetch", desc: "Fetch & parse web pages" },
            { name: "web_search", desc: "Search internet for live info" },
            { name: "browser", desc: "Control headless browser" },
            { name: "read", desc: "Read files & directories" },
            { name: "write", desc: "Create & edit files" },
            { name: "cron", desc: "Schedule recurring tasks" },
            { name: "memory", desc: "Persist context across sessions" },
          ].map((tool, i) => (
            <Reveal key={i} delay={0.2 + i * 0.04}>
              <GlowCard style={{ padding: "18px 16px", textAlign: "center" }}>
                <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 16, fontWeight: 700, marginBottom: 8, opacity: 0.5 }}>{">"}</div>
                <div style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 600, marginBottom: 4 }}>{tool.name}</div>
                <div style={{ color: C.slateD, fontSize: 10, lineHeight: 1.5 }}>{tool.desc}</div>
              </GlowCard>
            </Reveal>
          ))}
        </div>

        {/* Telegram Commands */}
        <Reveal delay={0.25}>
          <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>TELEGRAM COMMANDS</div>
        </Reveal>
        <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 32 }}>
          {[
            { cmd: "Show active signals", desc: "Query API and display current BUY_YES/BUY_NO signals with edge, confidence, and reasoning", color: C.teal },
            { cmd: "Check accuracy", desc: "Pull prediction data, compute win rate by confidence level, and format detailed accuracy report", color: C.amber },
            { cmd: "Check health", desc: "Run system health check — database status, uptime, next scan time", color: C.green },
            { cmd: "Run a scan now", desc: "Trigger manual market scan — sync markets, fetch news, run AI analysis, send Telegram report", color: C.blue },
            { cmd: "Analyze this market: [URL]", desc: "Fetch Polymarket page, extract data, assess probability, provide recommendation with key factors", color: C.red },
          ].map((item, i) => (
            <Reveal key={i} delay={0.25 + i * 0.05}>
              <GlowCard style={{ padding: "16px 24px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span style={{
                    color: item.color, fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 600,
                    background: `${item.color}12`, padding: "4px 12px", borderRadius: 4, flexShrink: 0,
                  }}>"{item.cmd}"</span>
                  <span style={{ color: C.slate, fontSize: 12, lineHeight: 1.5 }}>{item.desc}</span>
                </div>
              </GlowCard>
            </Reveal>
          ))}
        </div>

        {/* Why Powerful */}
        <Reveal delay={0.3}>
          <GlowCard accent={C.blue}>
            <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>WHY THIS IS POWERFUL</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
              {[
                { title: "Not a Fixed Bot", desc: "Traditional bots execute pre-coded commands. OpenClaw thinks — if you ask something outside its skill definition, it figures out how to answer using available tools." },
                { title: "Full Server Access", desc: "Claude Sonnet 4.5 has direct access to execute commands on the VPS. It can query databases, read logs, run scripts, and modify configurations." },
                { title: "Context Aware", desc: "OpenClaw reads the Oracle Sentinel skill file to understand the entire system — project structure, API endpoints, database schema, and operational context." },
                { title: "Real-time Intelligence", desc: "Combines web search, page fetching, and local execution to provide analysis grounded in both live internet data and Oracle Sentinel's internal database." },
              ].map((item, i) => (
                <div key={i}>
                  <div style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 600, marginBottom: 6 }}>{item.title}</div>
                  <div style={{ color: C.slate, fontSize: 12, lineHeight: 1.7 }}>{item.desc}</div>
                </div>
              ))}
            </div>
          </GlowCard>
        </Reveal>
      </Section>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* FOR AI AGENTS */}
      {/* ═══════════════════════════════════════════════════════ */}
      <Section id="agents" style={{ borderTop: `1px solid ${C.border}` }}>
        <Reveal><SectionLabel text="FOR AI AGENTS" sub="Integrate with Oracle Sentinel." /></Reveal>
        
        <Reveal delay={0.1}>
          <GlowCard accent={C.teal} style={{ marginBottom: 24 }}>
            <div style={{ color: C.teal, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>SKILL FILE</div>
            <p style={{ color: C.frost, fontSize: 14, lineHeight: 1.8, marginBottom: 16 }}>
              AI agents can read Oracle Sentinel's skill file to understand how to interact with the system. The skill file contains API endpoints, usage examples, signal types, and integration instructions.
            </p>
            <CodeBlock lang="bash" code={`curl -s https://oraclesentinel.xyz/skill.md`} />
          </GlowCard>
        </Reveal>

        <Reveal delay={0.15}>
          <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>WHAT AGENTS CAN DO</div>
        </Reveal>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
          {[
            { title: "Fetch Trading Signals", desc: "Get active BUY_YES/BUY_NO signals with AI probability, edge calculation, and confidence level.", code: "curl -s https://oraclesentinel.xyz/api/signals" },
            { title: "Monitor Markets", desc: "Access 79+ monitored Polymarket markets with current prices, volume, and liquidity data.", code: "curl -s https://oraclesentinel.xyz/api/markets" },
            { title: "Track Predictions", desc: "View tracked predictions with price snapshots at 1h, 6h, 24h intervals for accuracy verification.", code: "curl -s https://oraclesentinel.xyz/api/predictions" },
            { title: "Interactive Analysis", desc: "Send Polymarket URLs to the Telegram bot for real-time AI analysis with resolution rules breakdown.", code: "Message @oraclesentinel_pm_bot" },
          ].map((item, i) => (
            <Reveal key={i} delay={0.15 + i * 0.05}>
              <GlowCard style={{ height: "100%" }}>
                <div style={{ color: C.ice, fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 600, marginBottom: 8 }}>{item.title}</div>
                <div style={{ color: C.slate, fontSize: 12, lineHeight: 1.6, marginBottom: 12 }}>{item.desc}</div>
                <div style={{
                  background: C.bg, border: `1px solid ${C.border}`, borderRadius: 4, padding: "8px 12px",
                  fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: C.teal,
                }}>{item.code}</div>
              </GlowCard>
            </Reveal>
          ))}
        </div>

        <Reveal delay={0.25}>
          <GlowCard accent={C.blue}>
            <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 16 }}>INTEGRATION EXAMPLE</div>
            <CodeBlock lang="python" code={`# AI Agent integration with Oracle Sentinel
import requests

# 1. Read the skill file to understand capabilities
skill = requests.get("https://oraclesentinel.xyz/skill.md").text

# 2. Fetch active signals
signals = requests.get("https://oraclesentinel.xyz/api/signals").json()

# 3. Filter high-confidence opportunities
for signal in signals:
    if signal["edge"] > 10 and signal["confidence"] == "HIGH":
        print(f"🎯 {signal['signal_type']}: {signal['question']}")
        print(f"   Edge: +{signal['edge']}%")
        print(f"   AI Probability: {signal['ai_probability']*100:.1f}%")
        print(f"   Market Price: {signal['market_price']*100:.1f}%")`} />
          </GlowCard>
        </Reveal>
      </Section>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* FOOTER */}
      {/* ═══════════════════════════════════════════════════════ */}
      <footer style={{
        borderTop: `1px solid ${C.border}`, padding: "48px 32px", textAlign: "center",
        position: "relative", zIndex: 1,
      }}>
        <div style={{ color: C.blue, fontFamily: "'JetBrains Mono', monospace", fontSize: 14, fontWeight: 700, letterSpacing: 4, marginBottom: 8 }}>ORACLE SENTINEL</div>
        <div style={{ color: C.slateD, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: 2, marginBottom: 24 }}>AUTONOMOUS PREDICTION INTELLIGENCE</div>
        <div style={{ display: "flex", justifyContent: "center", gap: 32, marginBottom: 24 }}>
          {[
            { l: "Dashboard", h: "/predict" },
            { l: "X", h: "https://x.com/oracle_sentinel" },
            { l: "GitHub", h: "https://github.com/oraclesentinel?tab=repositories" },
            { l: "Telegram", h: "https://t.me/oraclesentinelsignals" },
            { l: "$OSAI", h: "https://solscan.io/token/HuDBwWRsa4bu8ueaCb7PPgJrqBeZDkcyFqMW5bbXpump" },
          ].map((lnk, i) => (
            <a key={i} href={lnk.h} target="_blank" rel="noopener noreferrer" style={{
              color: C.frost, fontFamily: "'JetBrains Mono', monospace", fontSize: 11,
              textDecoration: "none", borderBottom: `1px solid ${C.border}`, paddingBottom: 2,
            }}>{lnk.l}</a>
          ))}
        </div>
        <div style={{ color: C.slateD, fontFamily: "'JetBrains Mono', monospace", fontSize: 9, letterSpacing: 1 }}>
          Built on Solana ecosystem principles · Powered by Anthropic Claude · © 2026
        </div>
      </footer>
    </div>
  );
}