import { useState, useEffect } from "react";

// ═══════════════════════════════════════════════════════════════
// ORACLE SENTINEL — DOCUMENTATION
// Clean Documentation Style (PayAI-inspired)
// ═══════════════════════════════════════════════════════════════

const C = {
  bg: "#0a0f16",
  bgSidebar: "#080c12",
  bgContent: "#0d1219",
  bgCard: "#111820",
  bgHover: "#151d28",
  blue: "#4da6ff",
  blueMid: "#2d7fd4",
  blueDim: "#1a5a9e",
  ice: "#e1eaf5",
  frost: "#a0b4c8",
  slate: "#6b7f92",
  slateD: "#4a5a6a",
  teal: "#4ecdc4",
  amber: "#d4a843",
  green: "#4ade80",
  red: "#e05565",
  border: "#1a2332",
  borderL: "#243040",
};

// Sidebar Navigation Structure
const NAV_STRUCTURE = [
  {
    category: "Oracle Sentinel",
    items: [
      { id: "introduction", label: "Introduction" },
      { id: "getting-started", label: "Getting Started" },
      { id: "architecture", label: "Architecture Overview" },
    ]
  },
  {
    category: "Sentinel Predict",
    items: [
      { id: "predict-overview", label: "Overview" },
      { id: "predict-how-it-works", label: "How It Works" },
      { id: "predict-dual-model", label: "Dual-Model AI System" },
      { id: "predict-market-analysis", label: "Market Analysis" },
      { id: "predict-signal-types", label: "Signal Types" },
      { id: "predict-accuracy", label: "Accuracy Tracking" },
      { id: "predict-whale-detection", label: "Whale Detection" },
    ]
  },
  {
    category: "Sentinel Code",
    items: [
      { id: "code-overview", label: "Overview" },
      { id: "code-how-it-works", label: "How It Works" },
      { id: "code-security-scanner", label: "Security Scanner" },
      { id: "code-bug-detection", label: "Bug Detection" },
      { id: "code-quality", label: "Code Quality Analysis" },
      { id: "code-languages", label: "Supported Languages" },
    ]
  },
  {
    category: "Sentinel Economic",
    items: [
      { id: "economic-overview", label: "Overview" },
      { id: "economic-how-it-works", label: "How It Works" },
      { id: "economic-negotiation", label: "AI Negotiation Engine" },
      { id: "economic-payments", label: "Payment Methods" },
      { id: "economic-marketplace", label: "Marketplace" },
      { id: "economic-api-key", label: "Using Your API Key" },
    ]
  },
  {
    category: "$OSAI Token",
    items: [
      { id: "token-overview", label: "Overview" },
      { id: "token-utility", label: "Token Utility" },
      { id: "token-benefits", label: "Holder Benefits" },
      { id: "token-how-to-buy", label: "How to Buy" },
    ]
  },
];

// ═══════════════════════════════════════════════════════════════
// STYLES
// ═══════════════════════════════════════════════════════════════
function Styles() {
  return (
    <style>{`
      * { box-sizing: border-box; margin: 0; padding: 0; }
      body { background: ${C.bg}; }
      
      .docs-container {
        display: flex;
        min-height: 100vh;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }
      
      /* Sidebar */
      .sidebar {
        width: 280px;
        background: ${C.bgSidebar};
        border-right: 1px solid ${C.border};
        position: fixed;
        top: 0;
        left: 0;
        height: 100vh;
        overflow-y: auto;
        padding: 24px 0;
      }
      
      .sidebar-logo {
        padding: 0 24px 24px;
        border-bottom: 1px solid ${C.border};
        margin-bottom: 16px;
      }
      
      .sidebar-category {
        padding: 16px 24px 8px;
        color: ${C.slate};
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
      }
      
      .sidebar-item {
        display: block;
        padding: 10px 24px 10px 32px;
        color: ${C.frost};
        font-size: 14px;
        text-decoration: none;
        transition: all 0.15s ease;
        cursor: pointer;
        border-left: 2px solid transparent;
      }
      
      .sidebar-item:hover {
        background: ${C.bgHover};
        color: ${C.ice};
      }
      
      .sidebar-item.active {
        background: ${C.blue}10;
        color: ${C.blue};
        border-left-color: ${C.blue};
      }
      
      /* Main Content */
      .main-content {
        margin-left: 280px;
        flex: 1;
        display: flex;
      }
      
      .content-area {
        flex: 1;
        max-width: 800px;
        padding: 48px 64px;
      }
      
      /* On This Page */
      .on-this-page {
        width: 220px;
        padding: 48px 24px;
        position: sticky;
        top: 0;
        height: 100vh;
        overflow-y: auto;
      }
      
      .on-this-page-title {
        color: ${C.slate};
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 16px;
      }
      
      .on-this-page-item {
        display: block;
        padding: 6px 0;
        color: ${C.frost};
        font-size: 13px;
        text-decoration: none;
        transition: color 0.15s ease;
        cursor: pointer;
      }
      
      .on-this-page-item:hover {
        color: ${C.blue};
      }
      
      /* Typography */
      .doc-title {
        color: ${C.ice};
        font-size: 36px;
        font-weight: 700;
        margin-bottom: 16px;
        line-height: 1.2;
      }
      
      .doc-subtitle {
        color: ${C.frost};
        font-size: 18px;
        line-height: 1.6;
        margin-bottom: 32px;
      }
      
      .doc-section {
        margin-bottom: 48px;
      }
      
      .doc-heading {
        color: ${C.ice};
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 16px;
        padding-top: 24px;
      }
      
      .doc-subheading {
        color: ${C.ice};
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 12px;
        padding-top: 16px;
      }
      
      .doc-text {
        color: ${C.frost};
        font-size: 15px;
        line-height: 1.7;
        margin-bottom: 16px;
      }
      
      .doc-list {
        color: ${C.frost};
        font-size: 15px;
        line-height: 1.8;
        margin-bottom: 16px;
        padding-left: 24px;
      }
      
      .doc-list li {
        margin-bottom: 8px;
      }
      
      /* Code Blocks */
      .code-block {
        background: ${C.bgCard};
        border: 1px solid ${C.border};
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        overflow-x: auto;
      }
      
      .code-block pre {
        color: ${C.ice};
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 13px;
        line-height: 1.6;
        margin: 0;
      }
      
      .code-inline {
        background: ${C.bgCard};
        color: ${C.teal};
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        padding: 2px 6px;
        border-radius: 4px;
      }
      
      /* Cards */
      .feature-card {
        background: ${C.bgCard};
        border: 1px solid ${C.border};
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 16px;
        transition: border-color 0.2s ease;
      }
      
      .feature-card:hover {
        border-color: ${C.borderL};
      }
      
      .feature-card-title {
        color: ${C.ice};
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 10px;
      }
      
      .feature-card-text {
        color: ${C.frost};
        font-size: 14px;
        line-height: 1.6;
      }
      
      /* API Endpoint */
      .api-endpoint {
        background: ${C.bgCard};
        border: 1px solid ${C.border};
        border-radius: 8px;
        margin-bottom: 16px;
        overflow: hidden;
      }
      
      .api-endpoint-header {
        padding: 16px 20px;
        border-bottom: 1px solid ${C.border};
        display: flex;
        align-items: center;
        gap: 12px;
      }
      
      .api-method {
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 4px;
      }
      
      .api-method.get { background: ${C.green}20; color: ${C.green}; }
      .api-method.post { background: ${C.amber}20; color: ${C.amber}; }
      .api-method.put { background: ${C.blue}20; color: ${C.blue}; }
      .api-method.delete { background: ${C.red}20; color: ${C.red}; }
      
      .api-path {
        color: ${C.ice};
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
      }
      
      .api-endpoint-body {
        padding: 20px;
      }
      
      .api-desc {
        color: ${C.frost};
        font-size: 14px;
        margin-bottom: 16px;
      }
      
      /* Table */
      .doc-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
      }
      
      .doc-table th {
        background: ${C.bgCard};
        color: ${C.slate};
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 12px 16px;
        text-align: left;
        border-bottom: 1px solid ${C.border};
      }
      
      .doc-table td {
        color: ${C.frost};
        font-size: 14px;
        padding: 12px 16px;
        border-bottom: 1px solid ${C.border};
      }
      
      .doc-table tr:last-child td {
        border-bottom: none;
      }
      
      /* Badge */
      .badge {
        display: inline-block;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      
      .badge-blue { background: ${C.blue}20; color: ${C.blue}; }
      .badge-teal { background: ${C.teal}20; color: ${C.teal}; }
      .badge-amber { background: ${C.amber}20; color: ${C.amber}; }
      .badge-green { background: ${C.green}20; color: ${C.green}; }
      
      /* Scrollbar */
      ::-webkit-scrollbar { width: 6px; }
      ::-webkit-scrollbar-track { background: ${C.bgSidebar}; }
      ::-webkit-scrollbar-thumb { background: ${C.border}; border-radius: 3px; }
      ::-webkit-scrollbar-thumb:hover { background: ${C.borderL}; }
      
      /* Responsive */
      @media (max-width: 1200px) {
        .on-this-page { display: none; }
      }
      
      @media (max-width: 900px) {
        .sidebar { width: 240px; }
        .main-content { margin-left: 240px; }
        .content-area { padding: 32px 40px; }
      }
    `}</style>
  );
}


// ═══════════════════════════════════════════════════════════════
// SIDEBAR COMPONENT
// ═══════════════════════════════════════════════════════════════
function Sidebar({ activeSection, onNavigate }) {
  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <a href="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 10 }}>
          <img src="/logo.png" alt="Oracle Sentinel" style={{ width: 32, height: 32, borderRadius: 6 }} />
          <span style={{ color: C.ice, fontWeight: 700, fontSize: 16 }}>Oracle Sentinel</span>
        </a>
      </div>
      
      {NAV_STRUCTURE.map((section, idx) => (
        <div key={idx}>
          <div className="sidebar-category">{section.category}</div>
          {section.items.map(item => (
            <div
              key={item.id}
              className={`sidebar-item ${activeSection === item.id ? 'active' : ''}`}
              onClick={() => onNavigate(item.id)}
            >
              {item.label}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// CONTENT SECTIONS
// ═══════════════════════════════════════════════════════════════

// Introduction
function IntroductionContent() {
  return (
    <>
      <h1 className="doc-title">Introduction</h1>
      <p className="doc-subtitle">
        Welcome to Oracle Sentinel — an autonomous intelligence layer built on Solana for prediction markets, code analysis, and AI agent economy.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="welcome">Welcome to Oracle Sentinel</h2>
        <p className="doc-text">
          Oracle Sentinel is a suite of AI-powered tools designed to provide actionable intelligence for traders, developers, and AI agents. Our platform combines advanced machine learning with blockchain technology to deliver real-time insights and autonomous services.
        </p>
        <p className="doc-text">
          Our open-source technologies empower developers to create, monetize, and integrate AI agents and services seamlessly.
        </p>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="modules">Intelligence Modules</h2>
        <div className="feature-card">
          <div className="feature-card-title">
            <span className="badge badge-blue">PREDICT</span>
            Sentinel Predict
          </div>
          <p className="feature-card-text">
            AI-powered prediction market intelligence. Dual-model analysis of Jupiter prediction markets with 57% historical accuracy, whale detection, and real-time trading signals.
          </p>
        </div>
        
        <div className="feature-card">
          <div className="feature-card-title">
            <span className="badge badge-teal">CODE</span>
            Sentinel Code
          </div>
          <p className="feature-card-text">
            GitHub repository analyzer for security vulnerabilities, bugs, and code quality. Supports 15+ programming languages with AI-powered fix suggestions.
          </p>
        </div>
        
        <div className="feature-card">
          <div className="feature-card-title">
            <span className="badge badge-amber">ECONOMIC</span>
            Sentinel Economic
          </div>
          <p className="feature-card-text">
            Decentralized marketplace for AI services. Buy, sell, and negotiate API access with AI-powered pricing, USDC payments, and $OSAI token gating.
          </p>
        </div>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="quick-links">Quick Links</h2>
        <table className="doc-table">
          <thead>
            <tr>
              <th>Module</th>
              <th>Dashboard</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Sentinel Predict</td>
              <td><a href="https://predict.oraclesentinel.xyz" target="_blank" rel="noopener noreferrer" style={{ color: C.blue }}>predict.oraclesentinel.xyz</a></td>
              <td><span className="badge badge-green">LIVE</span></td>
            </tr>
            <tr>
              <td>Sentinel Code</td>
              <td><a href="https://code.oraclesentinel.xyz" target="_blank" rel="noopener noreferrer" style={{ color: C.teal }}>code.oraclesentinel.xyz</a></td>
              <td><span className="badge badge-green">LIVE</span></td>
            </tr>
            <tr>
              <td>Sentinel Economic</td>
              <td><a href="https://economic.oraclesentinel.xyz" target="_blank" rel="noopener noreferrer" style={{ color: C.amber }}>economic.oraclesentinel.xyz</a></td>
              <td><span className="badge badge-green">LIVE</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </>
  );
}

// Getting Started
function GettingStartedContent() {
  return (
    <>
      <h1 className="doc-title">Getting Started</h1>
      <p className="doc-subtitle">
        Get up and running with Oracle Sentinel in minutes.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="prerequisites">Prerequisites</h2>
        <p className="doc-text">To use Oracle Sentinel services, you need:</p>
        <ul className="doc-list">
          <li>A Solana wallet (Phantom, Solflare, or any compatible wallet)</li>
          <li>USDC for paid API access, or</li>
          <li>1,000+ $OSAI tokens for free unlimited access</li>
        </ul>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="connect-wallet">Step 1: Connect Your Wallet</h2>
        <p className="doc-text">
          Visit any Oracle Sentinel dashboard and click "Connect Wallet" in the top right corner. We support Phantom, Solflare, Coinbase Wallet, and Ledger.
        </p>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="get-api-key">Step 2: Get Your API Key</h2>
        <p className="doc-text">There are two ways to get an API key:</p>
        
        <h3 className="doc-subheading">Option A: Purchase Access</h3>
        <p className="doc-text">
          Go to <a href="https://economic.oraclesentinel.xyz" target="_blank" rel="noopener noreferrer" style={{ color: C.amber }}>Sentinel Economic</a>, browse available services, and purchase access using USDC. You can also negotiate prices with our AI agent.
        </p>
        
        <h3 className="doc-subheading">Option B: Token Holder (Free)</h3>
        <p className="doc-text">
          If you hold 1,000+ $OSAI tokens, you get free unlimited API access. Simply connect your wallet and claim your VIP access from the dashboard.
        </p>
      </div>

      <div className="doc-section">
        <h2 className="doc-heading" id="explore-modules">Step 3: Explore the Modules</h2>
        <p className="doc-text">Now that you have access, explore each module to get started:</p>
        
        <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "16px" }}>
          <a href="https://predict.oraclesentinel.xyz" target="_blank" rel="noopener noreferrer" style={{ display: "block", padding: "16px", background: "#0f172a", borderRadius: "8px", border: "1px solid #1e3a5f", textDecoration: "none" }}>
            <div style={{ color: "#60a5fa", fontWeight: 600, marginBottom: "4px" }}>Sentinel Predict</div>
            <div style={{ color: "#94a3b8", fontSize: "13px" }}>AI-powered prediction market intelligence with real-time signals and whale detection.</div>
          </a>
          <a href="https://code.oraclesentinel.xyz" target="_blank" rel="noopener noreferrer" style={{ display: "block", padding: "16px", background: "#0f172a", borderRadius: "8px", border: "1px solid #1e3a5f", textDecoration: "none" }}>
            <div style={{ color: "#2dd4bf", fontWeight: 600, marginBottom: "4px" }}>Sentinel Code</div>
            <div style={{ color: "#94a3b8", fontSize: "13px" }}>GitHub repository analyzer for security vulnerabilities, bugs, and code quality.</div>
          </a>
          <a href="https://economic.oraclesentinel.xyz" target="_blank" rel="noopener noreferrer" style={{ display: "block", padding: "16px", background: "#0f172a", borderRadius: "8px", border: "1px solid #1e3a5f", textDecoration: "none" }}>
            <div style={{ color: "#fbbf24", fontWeight: 600, marginBottom: "4px" }}>Sentinel Economic</div>
            <div style={{ color: "#94a3b8", fontSize: "13px" }}>Marketplace to buy, sell, and negotiate API access with USDC payments.</div>
          </a>
        </div>
      </div>
    </>
  );
}

// Architecture
function ArchitectureContent() {
  return (
    <>
      <h1 className="doc-title">Architecture Overview</h1>
      <p className="doc-subtitle">
        Understanding how Oracle Sentinel's components work together.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="system-design">System Design</h2>
        <p className="doc-text">
          Oracle Sentinel is built as a modular system with three main intelligence modules, each operating independently but sharing common infrastructure for authentication, payments, and data.
        </p>

        <div style={{ textAlign: "center", padding: "20px 0" }}>
          <img 
            src="/images/oracle-sentinel-system.png" 
            alt="Oracle Sentinel System Architecture" 
            style={{ maxWidth: "100%", height: "auto", borderRadius: "8px" }}
          />
        </div>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="tech-stack">Technology Stack</h2>
        <table className="doc-table">
          <thead>
            <tr>
              <th>Layer</th>
              <th>Technology</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>Frontend</td><td>React, Vite</td></tr>
            <tr><td>Backend</td><td>Python, Flask</td></tr>
            <tr><td>AI Models</td><td>Claude Haiku, Claude Sonnet (Anthropic)</td></tr>
            <tr><td>Blockchain</td><td>Solana</td></tr>
            <tr><td>Payments</td><td>USDC (SPL Token)</td></tr>
            <tr><td>Database</td><td>SQLite, PostgreSQL</td></tr>
          </tbody>
        </table>
      </div>
    </>
  );
}


// ═══════════════════════════════════════════════════════════════
// SENTINEL PREDICT CONTENT
// ═══════════════════════════════════════════════════════════════

function PredictOverviewContent() {
  return (
    <>
      <h1 className="doc-title">Sentinel Predict</h1>
      <p className="doc-subtitle">
        AI-powered prediction market intelligence with 57% historical accuracy.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="what-is-predict">What is Sentinel Predict?</h2>
        <p className="doc-text">
          Sentinel Predict is an autonomous AI system that scans prediction markets (Jupiter Prediction Market) every 4 hours to identify mispriced opportunities. It uses a dual-model AI architecture to analyze market data, news, and sentiment to generate actionable trading signals.
        </p>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="key-features">Key Features</h2>
        <div className="feature-card">
          <div className="feature-card-title">Dual-Model AI Analysis</div>
          <p className="feature-card-text">Claude Haiku extracts facts, Claude Sonnet assesses probabilities. Two models cross-validate to eliminate hallucinations.</p>
        </div>
        <div className="feature-card">
          <div className="feature-card-title">Whale Detection</div>
          <p className="feature-card-text">Real-time monitoring of large trades ($10K+) to identify smart money movements.</p>
        </div>
        <div className="feature-card">
          <div className="feature-card-title">Edge Calculator</div>
          <p className="feature-card-text">Quantified edge percentage showing the mathematical difference between AI probability and market consensus.</p>
        </div>
        <div className="feature-card">
          <div className="feature-card-title">Accuracy Tracking</div>
          <p className="feature-card-text">Transparent performance metrics with historical accuracy of 57.1%.</p>
        </div>
      </div>
    </>
  );
}

function PredictHowItWorksContent() {
  return (
    <>
      <h1 className="doc-title">How It Works</h1>
      <p className="doc-subtitle">
        The complete pipeline from data collection to signal generation.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="pipeline">Analysis Pipeline</h2>
        <p className="doc-text">Every 4 hours, Sentinel Predict executes the following pipeline:</p>
        <ul className="doc-list">
          <li><strong>Data Collection:</strong> Fetch active markets from Jupiter API, current prices, volumes, and metadata</li>
          <li><strong>Market Filtering:</strong> Apply filters for liquidity, time to resolution, and market type</li>
          <li><strong>AI Analysis (Haiku):</strong> Extract factual information about each market question</li>
          <li><strong>AI Analysis (Sonnet):</strong> Generate probability estimates based on extracted facts</li>
          <li><strong>Edge Calculation:</strong> Compare AI probability vs market price to find mispriced opportunities</li>
          <li><strong>Signal Generation:</strong> Generate BUY_YES, BUY_NO, or NO_TRADE signals</li>
          <li><strong>Whale Monitoring:</strong> Track large trades for confirmation or divergence</li>
        </ul>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="scan-interval">Scan Interval</h2>
        <p className="doc-text">
          The system runs automatically every 4 hours (6 times per day). This interval balances freshness with API costs and prevents over-trading on volatile short-term movements.
        </p>
      </div>
    </>
  );
}

function PredictDualModelContent() {
  return (
    <>
      <h1 className="doc-title">Dual-Model AI System</h1>
      <p className="doc-subtitle">
        How two AI models work together to eliminate hallucinations.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="why-dual-model">Why Two Models?</h2>
        <p className="doc-text">
          Single-model AI systems are prone to hallucinations and overconfidence. By using two different models with different strengths, we achieve cross-validation that significantly improves reliability.
        </p>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="model-roles">Model Roles</h2>
        <table className="doc-table">
          <thead>
            <tr>
              <th>Model</th>
              <th>Role</th>
              <th>Strength</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><span className="badge badge-blue">Claude Haiku</span></td>
              <td>Fact Extraction</td>
              <td>Fast, efficient, good at structured data extraction</td>
            </tr>
            <tr>
              <td><span className="badge badge-teal">Claude Sonnet</span></td>
              <td>Probability Assessment</td>
              <td>Better reasoning, nuanced analysis, calibrated confidence</td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="cross-validation">Cross-Validation Process</h2>
        <p className="doc-text">
          If the two models disagree significantly (>15% probability difference), the system flags the market for manual review or reduces confidence in the signal. This prevents acting on hallucinated information.
        </p>
      </div>
    </>
  );
}

function PredictMarketAnalysisContent() {
  return (
    <>
      <h1 className="doc-title">Market Analysis</h1>
      <p className="doc-subtitle">
        How Sentinel Predict analyzes prediction markets.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="market-selection">Market Selection Criteria</h2>
        <p className="doc-text">Not all markets are suitable for analysis. We filter for:</p>
        <ul className="doc-list">
          <li><strong>Liquidity:</strong> Minimum $10,000 in trading volume</li>
          <li><strong>Time to Resolution:</strong> Between 24 hours and 90 days</li>
          <li><strong>Market Type:</strong> Binary outcomes (Yes/No) preferred</li>
          <li><strong>Verifiability:</strong> Clear resolution criteria</li>
        </ul>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="analysis-factors">Analysis Factors</h2>
        <p className="doc-text">Each market is analyzed across multiple dimensions:</p>
        <ul className="doc-list">
          <li>Historical data and base rates</li>
          <li>Recent news and developments</li>
          <li>Market sentiment and trading patterns</li>
          <li>Expert opinions and forecasts</li>
          <li>Statistical models where applicable</li>
        </ul>
      </div>
    </>
  );
}

function PredictSignalTypesContent() {
  return (
    <>
      <h1 className="doc-title">Signal Types</h1>
      <p className="doc-subtitle">
        Understanding the different trading signals.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="signal-types">Signal Types</h2>
        <table className="doc-table">
          <thead>
            <tr>
              <th>Signal</th>
              <th>Meaning</th>
              <th>When Generated</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><span style={{ color: C.green, fontWeight: 600 }}>BUY_YES</span></td>
              <td>AI believes YES is underpriced</td>
              <td>AI probability > Market price + Edge threshold</td>
            </tr>
            <tr>
              <td><span style={{ color: C.red, fontWeight: 600 }}>BUY_NO</span></td>
              <td>AI believes NO is underpriced</td>
              <td>AI probability &lt; Market price - Edge threshold</td>
            </tr>
            <tr>
              <td><span style={{ color: C.slate, fontWeight: 600 }}>NO_TRADE</span></td>
              <td>No significant edge detected</td>
              <td>AI probability ≈ Market price (within threshold)</td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="edge-threshold">Edge Threshold</h2>
        <p className="doc-text">
          The default edge threshold is 5%. This means a signal is only generated when the AI's probability estimate differs from the market price by more than 5 percentage points. This reduces noise and focuses on higher-confidence opportunities.
        </p>
      </div>
    </>
  );
}

function PredictAccuracyContent() {
  return (
    <>
      <h1 className="doc-title">Accuracy Tracking</h1>
      <p className="doc-subtitle">
        Transparent performance metrics and historical accuracy.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="current-accuracy">Current Accuracy</h2>
        <div className="feature-card" style={{ borderColor: C.green + '40' }}>
          <div className="feature-card-title" style={{ fontSize: 32, color: C.green }}>57.1%</div>
          <p className="feature-card-text">Historical accuracy across all resolved predictions</p>
        </div>
        <p className="doc-text">
          This accuracy rate is calculated based on all predictions where the market has resolved. A 57% accuracy with proper position sizing and bankroll management can generate positive returns over time.
        </p>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="accuracy-methodology">Methodology</h2>
        <p className="doc-text">Accuracy is calculated as:</p>
        <div className="code-block">
          <pre>{`Accuracy = Correct Predictions / Total Resolved Predictions × 100%

Where:
- Correct BUY_YES = Market resolved YES
- Correct BUY_NO = Market resolved NO
- NO_TRADE signals are excluded from accuracy calculation`}</pre>
        </div>
      </div>
    </>
  );
}

function PredictWhaleDetectionContent() {
  return (
    <>
      <h1 className="doc-title">Whale Detection</h1>
      <p className="doc-subtitle">
        Tracking large trades to identify smart money movements.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="what-is-whale">What is a Whale?</h2>
        <p className="doc-text">
          In prediction markets, a "whale" is a trader who places large bets (typically $5,000+). These traders often have better information or more sophisticated analysis, so tracking their movements can provide valuable signals.
        </p>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="detection-method">Detection Method</h2>
        <p className="doc-text">Sentinel Predict monitors:</p>
        <ul className="doc-list">
          <li>Single trades above $5,000</li>
          <li>Rapid accumulation patterns ($5,000+ within 1 hour)</li>
          <li>Unusual volume spikes compared to 7-day average</li>
          <li>New wallet addresses placing large initial trades</li>
        </ul>
      </div>
      

      <div className="doc-section">
        <h2 className="doc-heading" id="whale-alerts">Whale Alerts</h2>
        <p className="doc-text">
          Sentinel Predict has two levels of whale alerts:
        </p>
        <div className="feature-card" style={{ marginTop: "12px" }}>
          <div className="feature-card-title">🐋 Standard Whale Alert</div>
          <p className="feature-card-text">Trades between $5,000 - $19,999. Flagged in the dashboard to confirm or contradict AI signals.</p>
        </div>
        <div className="feature-card" style={{ marginTop: "12px" }}>
          <div className="feature-card-title">🔥 Mega Whale Alert</div>
          <p className="feature-card-text">Trades of $20,000 or more. These high-conviction moves are automatically added to the Signals feed as they often indicate significant market-moving information.</p>
        </div>
      </div>
    </>
  );
}


// ═══════════════════════════════════════════════════════════════
// SENTINEL CODE CONTENT
// ═══════════════════════════════════════════════════════════════

function CodeOverviewContent() {
  return (
    <>
      <h1 className="doc-title">Sentinel Code</h1>
      <p className="doc-subtitle">
        AI-powered GitHub repository analyzer for security and code quality.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="what-is-code">What is Sentinel Code?</h2>
        <p className="doc-text">
          Sentinel Code is an AI-powered tool that analyzes GitHub repositories to identify security vulnerabilities, bugs, and code quality issues. Perfect for developers auditing their own code or investors evaluating crypto projects.
        </p>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="key-features">Key Features</h2>
        <div className="feature-card">
          <div className="feature-card-title">Security Scanning</div>
          <p className="feature-card-text">Detect SQL injection, XSS, hardcoded secrets, insecure dependencies, and more.</p>
        </div>
        <div className="feature-card">
          <div className="feature-card-title">Bug Detection</div>
          <p className="feature-card-text">Find logic errors, null pointer exceptions, race conditions, and potential crashes.</p>
        </div>
        <div className="feature-card">
          <div className="feature-card-title">Code Quality</div>
          <p className="feature-card-text">Analyze code complexity, maintainability, test coverage, and best practices.</p>
        </div>
        <div className="feature-card">
          <div className="feature-card-title">Auto-Fix Suggestions</div>
          <p className="feature-card-text">Get AI-generated fix suggestions with exact file and line references.</p>
        </div>
      </div>
    </>
  );
}

function CodeHowItWorksContent() {
  return (
    <>
      <h1 className="doc-title">How It Works</h1>
      <p className="doc-subtitle">
        The analysis pipeline from repository input to report generation.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="analysis-pipeline">Analysis Pipeline</h2>
        <ul className="doc-list">
          <li><strong>Repository Fetch:</strong> Clone or fetch the repository from GitHub</li>
          <li><strong>Language Detection:</strong> Identify programming languages and frameworks</li>
          <li><strong>File Parsing:</strong> Parse source files into abstract syntax trees</li>
          <li><strong>Pattern Matching:</strong> Run security and bug detection patterns</li>
          <li><strong>AI Analysis:</strong> Deep analysis using Claude for complex issues</li>
          <li><strong>Report Generation:</strong> Compile findings with severity ratings and fix suggestions</li>
        </ul>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="analysis-time">Analysis Time</h2>
        <p className="doc-text">
          Typical analysis takes 30-60 seconds depending on repository size. Large repositories (1000+ files) may take up to 2 minutes.
        </p>
      </div>
    </>
  );
}

function CodeSecurityScannerContent() {
  return (
    <>
      <h1 className="doc-title">Security Scanner</h1>
      <p className="doc-subtitle">
        Comprehensive security vulnerability detection.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="vulnerability-types">Vulnerability Types Detected</h2>
        <table className="doc-table">
          <thead>
            <tr>
              <th>Category</th>
              <th>Examples</th>
              <th>Severity</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Injection</td>
              <td>SQL injection, Command injection, LDAP injection</td>
              <td><span className="badge badge-amber">HIGH</span></td>
            </tr>
            <tr>
              <td>XSS</td>
              <td>Reflected XSS, Stored XSS, DOM-based XSS</td>
              <td><span className="badge badge-amber">HIGH</span></td>
            </tr>
            <tr>
              <td>Secrets</td>
              <td>Hardcoded API keys, passwords, private keys</td>
              <td><span className="badge badge-amber">CRITICAL</span></td>
            </tr>
            <tr>
              <td>Dependencies</td>
              <td>Known vulnerable packages, outdated libraries</td>
              <td><span className="badge badge-blue">MEDIUM</span></td>
            </tr>
            <tr>
              <td>Authentication</td>
              <td>Weak passwords, missing auth checks, session issues</td>
              <td><span className="badge badge-amber">HIGH</span></td>
            </tr>
            <tr>
              <td>Cryptography</td>
              <td>Weak algorithms, improper key management</td>
              <td><span className="badge badge-blue">MEDIUM</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </>
  );
}

function CodeBugDetectionContent() {
  return (
    <>
      <h1 className="doc-title">Bug Detection</h1>
      <p className="doc-subtitle">
        Finding bugs before they reach production.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="bug-categories">Bug Categories</h2>
        <ul className="doc-list">
          <li><strong>Null/Undefined Errors:</strong> Accessing properties on null objects</li>
          <li><strong>Type Errors:</strong> Incorrect type usage, missing type checks</li>
          <li><strong>Logic Errors:</strong> Incorrect conditionals, off-by-one errors</li>
          <li><strong>Race Conditions:</strong> Async issues, deadlocks, data races</li>
          <li><strong>Memory Leaks:</strong> Unreleased resources, circular references</li>
          <li><strong>Error Handling:</strong> Missing try/catch, swallowed exceptions</li>
        </ul>
      </div>
    </>
  );
}

function CodeQualityContent() {
  return (
    <>
      <h1 className="doc-title">Code Quality Analysis</h1>
      <p className="doc-subtitle">
        Measuring maintainability and best practices.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="quality-metrics">Quality Metrics</h2>
        <table className="doc-table">
          <thead>
            <tr>
              <th>Metric</th>
              <th>Description</th>
              <th>Good Range</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Complexity Score</td>
              <td>Cyclomatic complexity of functions</td>
              <td>1-10 per function</td>
            </tr>
            <tr>
              <td>Duplication</td>
              <td>Percentage of duplicated code</td>
              <td>&lt; 5%</td>
            </tr>
            <tr>
              <td>Documentation</td>
              <td>Comment coverage and quality</td>
              <td>&gt; 20%</td>
            </tr>
            <tr>
              <td>Test Coverage</td>
              <td>Percentage of code covered by tests</td>
              <td>&gt; 70%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </>
  );
}

function CodeLanguagesContent() {
  return (
    <>
      <h1 className="doc-title">Supported Languages</h1>
      <p className="doc-subtitle">
        15+ programming languages supported.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="languages">Languages</h2>
        <table className="doc-table">
          <thead>
            <tr>
              <th>Language</th>
              <th>Security Scan</th>
              <th>Bug Detection</th>
              <th>Quality Analysis</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>JavaScript/TypeScript</td><td>✓</td><td>✓</td><td>✓</td></tr>
            <tr><td>Python</td><td>✓</td><td>✓</td><td>✓</td></tr>
            <tr><td>Rust</td><td>✓</td><td>✓</td><td>✓</td></tr>
            <tr><td>Solidity</td><td>✓</td><td>✓</td><td>✓</td></tr>
            <tr><td>Go</td><td>✓</td><td>✓</td><td>✓</td></tr>
            <tr><td>Java</td><td>✓</td><td>✓</td><td>✓</td></tr>
            <tr><td>C/C++</td><td>✓</td><td>✓</td><td>✓</td></tr>
            <tr><td>Ruby</td><td>✓</td><td>✓</td><td>✓</td></tr>
            <tr><td>PHP</td><td>✓</td><td>✓</td><td>✓</td></tr>
            <tr><td>Swift</td><td>✓</td><td>✓</td><td>✓</td></tr>
            <tr><td>Kotlin</td><td>✓</td><td>✓</td><td>✓</td></tr>
            <tr><td>Scala</td><td>✓</td><td>✓</td><td>✓</td></tr>
            <tr><td>C#</td><td>✓</td><td>✓</td><td>✓</td></tr>
            <tr><td>Dart</td><td>✓</td><td>✓</td><td>✓</td></tr>
            <tr><td>Shell/Bash</td><td>✓</td><td>✓</td><td>-</td></tr>
          </tbody>
        </table>
      </div>
    </>
  );
}



// ═══════════════════════════════════════════════════════════════
// SENTINEL ECONOMIC CONTENT
// ═══════════════════════════════════════════════════════════════

function EconomicOverviewContent() {
  return (
    <>
      <h1 className="doc-title">Sentinel Economic</h1>
      <p className="doc-subtitle">
        Decentralized marketplace for AI services with AI-powered price negotiation.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="what-is-economic">What is Sentinel Economic?</h2>
        <p className="doc-text">
          Sentinel Economic is a decentralized marketplace that enables AI agents and humans to buy, sell, and negotiate access to AI-powered services. Built on Solana with USDC payments and $OSAI token gating for free access.
        </p>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="key-features">Key Features</h2>
        <div className="feature-card">
          <div className="feature-card-title">AI-Powered Negotiation</div>
          <p className="feature-card-text">Negotiate prices with our AI agent. The AI uses behavioral analysis and market data to find fair prices.</p>
        </div>
        <div className="feature-card">
          <div className="feature-card-title">USDC Payments</div>
          <p className="feature-card-text">Stable, accurate pricing with USDC on Solana. No gas fee surprises.</p>
        </div>
        <div className="feature-card">
          <div className="feature-card-title">Token Gating</div>
          <p className="feature-card-text">Hold 1,000+ $OSAI tokens to get free unlimited API access to all services.</p>
        </div>
        <div className="feature-card">
          <div className="feature-card-title">Seller Dashboard</div>
          <p className="feature-card-text">List your own AI services, set pricing tiers, and earn from API access sales.</p>
        </div>
      </div>
    </>
  );
}

function EconomicHowItWorksContent() {
  return (
    <>
      <h1 className="doc-title">How It Works</h1>
      <p className="doc-subtitle">
        The complete flow from browsing to API access.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="buyer-flow">Buyer Flow</h2>
        <ul className="doc-list">
          <li><strong>1. Connect Wallet:</strong> Connect your Solana wallet (Phantom, Solflare, etc.)</li>
          <li><strong>2. Browse Services:</strong> Explore available AI services in the marketplace</li>
          <li><strong>3. Choose Access Type:</strong> Select per-request, daily, weekly, or monthly access</li>
          <li><strong>4. Negotiate (Optional):</strong> Start a negotiation with the AI to get a better price</li>
          <li><strong>5. Pay with USDC:</strong> Complete payment using USDC on Solana</li>
          <li><strong>6. Get API Key:</strong> Receive your API key instantly after payment confirmation</li>
        </ul>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="seller-flow">Seller Flow</h2>
        <ul className="doc-list">
          <li><strong>1. Register as Seller:</strong> Switch to seller mode in the dashboard</li>
          <li><strong>2. Add Service:</strong> Provide service details, endpoints, and pricing</li>
          <li><strong>3. Set Pricing Tiers:</strong> Configure per-request, daily, weekly, monthly prices</li>
          <li><strong>4. Enable AI Negotiation:</strong> Let our AI handle price negotiations for you</li>
          <li><strong>5. Earn Revenue:</strong> Receive USDC payments directly to your wallet</li>
        </ul>
      </div>
    </>
  );
}

function EconomicNegotiationContent() {
  return (
    <>
      <h1 className="doc-title">AI Negotiation Engine</h1>
      <p className="doc-subtitle">
        How our AI negotiates prices on behalf of sellers.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="negotiation-process">Negotiation Process</h2>
        <p className="doc-text">
          When a buyer starts a negotiation, our AI agent evaluates the offer and responds with either acceptance, counter-offer, or rejection based on multiple factors.
        </p>
        <div className="code-block">
          <pre>{`Buyer offers: $0.005
     ↓
AI evaluates offer against:
  • Base price: $0.01
  • Buyer history: New buyer
  • Market conditions: Normal demand
     ↓
AI responds: Counter-offer $0.0075
     ↓
Buyer accepts or counters again
     ↓
Final price locked, ready for payment`}</pre>
        </div>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="strategies">AI Strategies</h2>
        <table className="doc-table">
          <thead>
            <tr>
              <th>Strategy</th>
              <th>When Used</th>
              <th>Behavior</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><span className="badge badge-blue">Anchor High</span></td>
              <td>New buyers, low-ball offers</td>
              <td>Counter at 85-90% of asking price</td>
            </tr>
            <tr>
              <td><span className="badge badge-teal">Meet Halfway</span></td>
              <td>Returning buyers, reasonable offers</td>
              <td>Split the difference between offer and asking</td>
            </tr>
            <tr>
              <td><span className="badge badge-amber">Firm Stance</span></td>
              <td>Very low offers (&lt;50% of asking)</td>
              <td>Minimal movement, emphasize value</td>
            </tr>
            <tr>
              <td><span className="badge badge-green">Generous</span></td>
              <td>High-value buyers, bulk purchases</td>
              <td>Quick acceptance, loyalty discount</td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="buyer-profiling">Buyer Profiling</h2>
        <p className="doc-text">The AI builds a profile of each buyer based on:</p>
        <ul className="doc-list">
          <li><strong>Transaction History:</strong> Number of past purchases, total spent</li>
          <li><strong>Offer Patterns:</strong> Average offer-to-ask ratio</li>
          <li><strong>Acceptance Rate:</strong> How often they accept counter-offers</li>
          <li><strong>Negotiation Rounds:</strong> Average rounds before agreement</li>
        </ul>
      </div>
    </>
  );
}

function EconomicPaymentsContent() {
  return (
    <>
      <h1 className="doc-title">Payment Methods</h1>
      <p className="doc-subtitle">
        How to pay for API access.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="usdc-payments">USDC Payments</h2>
        <p className="doc-text">
          The primary payment method is USDC on Solana. USDC is a stablecoin pegged 1:1 to the US Dollar, providing stable and predictable pricing.
        </p>
        <div className="feature-card">
          <div className="feature-card-title">Payment Flow</div>
          <p className="feature-card-text">
            1. Select service and access type → 2. Review price → 3. Click "Pay with USDC" → 4. Approve transaction in wallet → 5. API key issued instantly
          </p>
        </div>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="token-gating">Token Gating (Free Access)</h2>
        <p className="doc-text">
          Hold $OSAI tokens to get free API access without paying per-request.
        </p>
        <table className="doc-table">
          <thead>
            <tr>
              <th>Tier</th>
              <th>Tokens Required</th>
              <th>Benefit</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><span className="badge badge-teal">VIP</span></td>
              <td>1,000+ $OSAI</td>
              <td>FREE unlimited API access to all services</td>
            </tr>
            <tr>
              <td><span className="badge badge-blue">Premium</span></td>
              <td>100+ $OSAI</td>
              <td>20% discount on all purchases</td>
            </tr>
            <tr>
              <td><span className="badge badge-green">Holder</span></td>
              <td>1+ $OSAI</td>
              <td>10% discount on all purchases</td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="claim-access">How to Claim Free Access</h2>
        <ul className="doc-list">
          <li>Connect your wallet with 1,000+ $OSAI tokens</li>
          <li>Go to any service in the marketplace</li>
          <li>Click "Claim Free (VIP)" button</li>
          <li>Your API key will be generated instantly</li>
        </ul>
      </div>
    </>
  );
}

function EconomicMarketplaceContent() {
  return (
    <>
      <h1 className="doc-title">Marketplace</h1>
      <p className="doc-subtitle">
        Buying and selling AI services.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="buying">Buying Services</h2>
        <p className="doc-text">
          Browse the marketplace to find AI services. Each service shows:
        </p>
        <ul className="doc-list">
          <li><strong>Service Name & Description:</strong> What the service does</li>
          <li><strong>Endpoints:</strong> Available API endpoints and their purposes</li>
          <li><strong>Pricing Tiers:</strong> Per-request, daily, weekly, monthly options</li>
          <li><strong>Seller Info:</strong> Who provides the service</li>
          <li><strong>AI Negotiation:</strong> Whether price negotiation is enabled</li>
        </ul>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="selling">Selling Services</h2>
        <p className="doc-text">To list your own service:</p>
        <ul className="doc-list">
          <li><strong>1. Register as Seller:</strong> Click "Switch to Seller" in the dashboard</li>
          <li><strong>2. Add Service:</strong> Provide name, description, base URL</li>
          <li><strong>3. Configure Endpoints:</strong> Add API endpoints with methods and paths</li>
          <li><strong>4. Set Pricing:</strong> Configure pricing for each access tier</li>
          <li><strong>5. Submit for Review:</strong> Admin will approve your service</li>
        </ul>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="pricing-tiers">Pricing Tiers</h2>
        <table className="doc-table">
          <thead>
            <tr>
              <th>Tier</th>
              <th>Description</th>
              <th>Best For</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Per-Request</td>
              <td>Pay for each API call</td>
              <td>Testing, low-volume usage</td>
            </tr>
            <tr>
              <td>Daily</td>
              <td>Unlimited calls for 24 hours</td>
              <td>Short-term projects</td>
            </tr>
            <tr>
              <td>Weekly</td>
              <td>Unlimited calls for 7 days</td>
              <td>Medium-term projects</td>
            </tr>
            <tr>
              <td>Monthly</td>
              <td>Unlimited calls for 30 days</td>
              <td>Production applications</td>
            </tr>
          </tbody>
        </table>
      </div>
    </>
  );
}

function EconomicAPIKeyContent() {
  return (
    <>
      <h1 className="doc-title">Using Your API Key</h1>
      <p className="doc-subtitle">
        How to authenticate and make API requests after purchasing access.
      </p>

      <div className="doc-section">
        <h2 className="doc-heading" id="getting-api-key">Getting Your API Key</h2>
        <p className="doc-text">
          After purchasing access to a service on Sentinel Economic, you'll receive an API key starting with <code style={{ background: "#1e293b", padding: "2px 6px", borderRadius: "3px" }}>se_</code>. You can find your API keys in the <strong>MY ACCESS</strong> tab.
        </p>
      </div>

      <div className="doc-section">
        <h2 className="doc-heading" id="authentication">Authentication</h2>
        <p className="doc-text">
          Include your API key in the Authorization header for all requests:
        </p>
        <div className="code-block">
          <pre>{`Authorization: Bearer se_your_api_key_here`}</pre>
        </div>
      </div>

      <div className="doc-section">
        <h2 className="doc-heading" id="example-curl">cURL Example</h2>
        <div className="code-block">
          <pre>{`curl -X GET "https://[service-url]/api/endpoint" \\
  -H "Authorization: Bearer se_your_api_key_here"`}</pre>
        </div>
      </div>

      <div className="doc-section">
        <h2 className="doc-heading" id="example-python">Python Example</h2>
        <div className="code-block">
          <pre>{`import requests

API_KEY = "se_your_api_key_here"
SERVICE_URL = "https://[service-url]"  # URL from purchased service

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

response = requests.get(f"{SERVICE_URL}/api/endpoint", headers=headers)
data = response.json()
print(data)`}</pre>
        </div>
      </div>

      <div className="doc-section">
        <h2 className="doc-heading" id="example-javascript">JavaScript Example</h2>
        <div className="code-block">
          <pre>{`const API_KEY = "se_your_api_key_here";
const SERVICE_URL = "https://[service-url]";  // URL from purchased service

const response = await fetch(\`\${SERVICE_URL}/api/endpoint\`, {
  headers: {
    "Authorization": \`Bearer \${API_KEY}\`
  }
});

const data = await response.json();
console.log(data);`}</pre>
        </div>
      </div>

      <div className="doc-section">
        <h2 className="doc-heading" id="error-codes">Error Codes</h2>
        <table className="doc-table">
          <thead>
            <tr>
              <th>Status Code</th>
              <th>Description</th>
              <th>Solution</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>200</td>
              <td>Success</td>
              <td>-</td>
            </tr>
            <tr>
              <td>401</td>
              <td>Invalid or missing API key</td>
              <td>Check your API key format (must start with se_)</td>
            </tr>
            <tr>
              <td>403</td>
              <td>Access denied or expired</td>
              <td>Purchase new access on Sentinel Economic</td>
            </tr>
            <tr>
              <td>429</td>
              <td>Rate limit exceeded</td>
              <td>Wait before making more requests</td>
            </tr>
            <tr>
              <td>500</td>
              <td>Server error</td>
              <td>Retry later or contact the service provider</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="doc-section">
        <h2 className="doc-heading" id="tips">Tips</h2>
        <ul className="doc-list">
          <li>Keep your API key secure - never share it publicly</li>
          <li>Each service has its own endpoint URL - check the service details</li>
          <li>Monitor your usage in the MY ACCESS tab</li>
          <li>Contact the service provider for API-specific documentation</li>
        </ul>
      </div>
    </>
  );
}



// ═══════════════════════════════════════════════════════════════
// $OSAI TOKEN CONTENT
// ═══════════════════════════════════════════════════════════════

function TokenOverviewContent() {
  return (
    <>
      <h1 className="doc-title">$OSAI Token</h1>
      <p className="doc-subtitle">
        The utility token powering the Oracle Sentinel ecosystem.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="what-is-osai">What is $OSAI?</h2>
        <p className="doc-text">
          $OSAI is the native utility token of Oracle Sentinel. It provides holders with free API access, governance rights, and exclusive benefits across all Sentinel modules.
        </p>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="token-info">Token Information</h2>
        <table className="doc-table">
          <thead>
            <tr>
              <th>Property</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>Name</td><td>Oracle Sentinel AI</td></tr>
            <tr><td>Symbol</td><td>$OSAI</td></tr>
            <tr><td>Blockchain</td><td>Solana</td></tr>
            <tr><td>Token Standard</td><td>SPL Token</td></tr>
            <tr>
              <td>Contract Address</td>
              <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12 }}>
                <a href="https://solscan.io/token/HuDBwWRsa4bu8ueaCb7PPgJrqBeZDkcyFqMW5bbXpump" target="_blank" rel="noopener noreferrer" style={{ color: C.blue }}>
                  HuDBwWRsa4bu8ueaCb7PPgJrqBeZDkcyFqMW5bbXpump
                </a>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </>
  );
}

function TokenUtilityContent() {
  return (
    <>
      <h1 className="doc-title">Token Utility</h1>
      <p className="doc-subtitle">
        How $OSAI provides value in the ecosystem.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="utilities">Utilities</h2>
        <div className="feature-card">
          <div className="feature-card-title">
            <span className="badge badge-teal">ACCESS</span>
            Free API Access
          </div>
          <p className="feature-card-text">
            Hold 1,000+ $OSAI to get free unlimited access to all Sentinel APIs (Predict, Code, Economic). No per-request fees, no subscriptions needed.
          </p>
        </div>
        
        <div className="feature-card">
          <div className="feature-card-title">
            <span className="badge badge-blue">DISCOUNT</span>
            Purchase Discounts
          </div>
          <p className="feature-card-text">
            Holders with 1-999 tokens receive 10-20% discount on all API purchases in Sentinel Economic.
          </p>
        </div>
        
        <div className="feature-card">
          <div className="feature-card-title">
            <span className="badge badge-amber">GOVERNANCE</span>
            Governance Rights
          </div>
          <p className="feature-card-text">
            Vote on protocol decisions, new features, and fee structures. (Coming soon)
          </p>
        </div>
        
        <div className="feature-card">
          <div className="feature-card-title">
            <span className="badge badge-green">REVENUE</span>
            Revenue Sharing
          </div>
          <p className="feature-card-text">
            Earn a share of protocol revenue based on token holdings. (Coming soon)
          </p>
        </div>
      </div>
    </>
  );
}

function TokenBenefitsContent() {
  return (
    <>
      <h1 className="doc-title">Holder Benefits</h1>
      <p className="doc-subtitle">
        Benefits by token holding tier.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="tiers">Holder Tiers</h2>
        
        <div className="feature-card" style={{ borderColor: C.teal + '40' }}>
          <div className="feature-card-title">
            <span className="badge badge-teal">VIP TIER</span>
            1,000+ $OSAI
          </div>
          <ul className="doc-list" style={{ marginTop: 12 }}>
            <li>FREE unlimited API access to Sentinel Predict</li>
            <li>FREE unlimited API access to Sentinel Code</li>
            <li>FREE unlimited API access to Sentinel Economic</li>
            <li>Priority support</li>
            <li>Early access to new features</li>
            <li>Governance voting rights</li>
          </ul>
        </div>
        
        <div className="feature-card" style={{ borderColor: C.blue + '40' }}>
          <div className="feature-card-title">
            <span className="badge badge-blue">PREMIUM TIER</span>
            100+ $OSAI
          </div>
          <ul className="doc-list" style={{ marginTop: 12 }}>
            <li>20% discount on all API purchases</li>
            <li>Extended API rate limits</li>
            <li>Governance voting rights</li>
          </ul>
        </div>
        
        <div className="feature-card" style={{ borderColor: C.green + '40' }}>
          <div className="feature-card-title">
            <span className="badge badge-green">HOLDER TIER</span>
            1+ $OSAI
          </div>
          <ul className="doc-list" style={{ marginTop: 12 }}>
            <li>10% discount on all API purchases</li>
            <li>Access to holder-only channels</li>
          </ul>
        </div>
      </div>
    </>
  );
}

function TokenHowToBuyContent() {
  return (
    <>
      <h1 className="doc-title">How to Buy $OSAI</h1>
      <p className="doc-subtitle">
        Step-by-step guide to purchasing $OSAI tokens.
      </p>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="step-1">Step 1: Get a Solana Wallet</h2>
        <p className="doc-text">
          Download and set up a Solana wallet. We recommend:
        </p>
        <ul className="doc-list">
          <li><strong>Phantom</strong> - Most popular, easy to use</li>
          <li><strong>Solflare</strong> - Feature-rich, mobile friendly</li>
          <li><strong>Backpack</strong> - Multi-chain support</li>
        </ul>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="step-2">Step 2: Get SOL</h2>
        <p className="doc-text">
          You need SOL to pay for transaction fees and to swap for $OSAI. Buy SOL from any major exchange (Coinbase, Binance, Kraken) and send it to your wallet.
        </p>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="step-3">Step 3: Swap for $OSAI</h2>
        <p className="doc-text">
          Use a Solana DEX to swap SOL for $OSAI:
        </p>
        <ul className="doc-list">
          <li><strong>Jupiter:</strong> <a href="https://jup.ag" target="_blank" rel="noopener noreferrer" style={{ color: C.blue }}>jup.ag</a> - Best rates, aggregates all DEXs</li>
          <li><strong>Raydium:</strong> <a href="https://raydium.io" target="_blank" rel="noopener noreferrer" style={{ color: C.blue }}>raydium.io</a></li>
        </ul>
        <p className="doc-text" style={{ marginTop: 16 }}>
          Token address to search:
        </p>
        <div className="code-block">
          <pre>HuDBwWRsa4bu8ueaCb7PPgJrqBeZDkcyFqMW5bbXpump</pre>
        </div>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="step-4">Step 4: Verify & Connect</h2>
        <p className="doc-text">
          After purchasing, connect your wallet to Oracle Sentinel dashboard. If you hold 1,000+ tokens, you'll automatically see the VIP badge and can claim free API access.
        </p>
      </div>
      
      <div className="doc-section">
        <h2 className="doc-heading" id="social-media">Social Media</h2>
        <p className="doc-text">Stay connected with Oracle Sentinel:</p>
        <table className="doc-table">
          <tbody>
            <tr>
              <td style={{ fontWeight: 600 }}>Website</td>
              <td><a href="https://oraclesentinel.xyz" target="_blank" rel="noopener noreferrer" style={{ color: C.blue }}>oraclesentinel.xyz</a></td>
            </tr>
            <tr>
              <td style={{ fontWeight: 600 }}>X</td>
              <td><a href="https://x.com/oracle_sentinel" target="_blank" rel="noopener noreferrer" style={{ color: C.blue }}>@oracle_sentinel</a></td>
            </tr>
            <tr>
              <td style={{ fontWeight: 600 }}>Telegram</td>
              <td><a href="https://t.me/oraclesentinelsignals" target="_blank" rel="noopener noreferrer" style={{ color: C.blue }}>@oraclesentinelsignals</a></td>
            </tr>
            <tr>
              <td style={{ fontWeight: 600 }}>GitHub</td>
              <td><a href="https://github.com/oraclesentinel" target="_blank" rel="noopener noreferrer" style={{ color: C.blue }}>github.com/oraclesentinel</a></td>
            </tr>
          </tbody>
        </table>
      </div>
    </>
  );
}

// ═══════════════════════════════════════════════════════════════
// CONTENT ROUTER
// ═══════════════════════════════════════════════════════════════

function ContentRouter({ section }) {
  const contentMap = {
    // Introduction
    'introduction': <IntroductionContent />,
    'getting-started': <GettingStartedContent />,
    'architecture': <ArchitectureContent />,
    
    // Predict
    'predict-overview': <PredictOverviewContent />,
    'predict-how-it-works': <PredictHowItWorksContent />,
    'predict-dual-model': <PredictDualModelContent />,
    'predict-market-analysis': <PredictMarketAnalysisContent />,
    'predict-signal-types': <PredictSignalTypesContent />,
    'predict-accuracy': <PredictAccuracyContent />,
    'predict-whale-detection': <PredictWhaleDetectionContent />,
    
    // Code
    'code-overview': <CodeOverviewContent />,
    'code-how-it-works': <CodeHowItWorksContent />,
    'code-security-scanner': <CodeSecurityScannerContent />,
    'code-bug-detection': <CodeBugDetectionContent />,
    'code-quality': <CodeQualityContent />,
    'code-languages': <CodeLanguagesContent />,
    
    // Economic
    'economic-overview': <EconomicOverviewContent />,
    'economic-how-it-works': <EconomicHowItWorksContent />,
    'economic-negotiation': <EconomicNegotiationContent />,
    'economic-payments': <EconomicPaymentsContent />,
    'economic-marketplace': <EconomicMarketplaceContent />,
    'economic-api-key': <EconomicAPIKeyContent />,
    
    // Token
    'token-overview': <TokenOverviewContent />,
    'token-utility': <TokenUtilityContent />,
    'token-benefits': <TokenBenefitsContent />,
    'token-how-to-buy': <TokenHowToBuyContent />,
  };
  
  return contentMap[section] || <IntroductionContent />;
}

// ═══════════════════════════════════════════════════════════════
// ON THIS PAGE COMPONENT
// ═══════════════════════════════════════════════════════════════

function OnThisPage({ section }) {
  const [headings, setHeadings] = useState([]);
  
  useEffect(() => {
    // Get all h2 headings from the content area
    setTimeout(() => {
      const h2Elements = document.querySelectorAll('.doc-heading');
      const items = Array.from(h2Elements).map(el => ({
        id: el.id,
        text: el.textContent
      }));
      setHeadings(items);
    }, 100);
  }, [section]);
  
  if (headings.length === 0) return null;
  
  return (
    <div className="on-this-page">
      <div className="on-this-page-title">On this page</div>
      {headings.map((h, i) => (
        
        <a
          key={i}
          className="on-this-page-item"
          onClick={() => {
            const el = document.getElementById(h.id);
            if (el) el.scrollIntoView({ behavior: 'smooth' });
          }}
        >
          {h.text}
        </a>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════

export default function OracleSentinelDocs() {
  const [activeSection, setActiveSection] = useState('introduction');
  
  const handleNavigate = (sectionId) => {
    setActiveSection(sectionId);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  
  return (
    <>
      <Styles />
      <div className="docs-container">
        <Sidebar activeSection={activeSection} onNavigate={handleNavigate} />
        <div className="main-content">
          <div className="content-area">
            <ContentRouter section={activeSection} />
          </div>
          <OnThisPage section={activeSection} />
        </div>
      </div>
    </>
  );
}
