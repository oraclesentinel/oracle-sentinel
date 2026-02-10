# Oracle Sentinel

Autonomous AI agent for Polymarket prediction intelligence.

![Status](https://img.shields.io/badge/status-live-brightgreen)
![Version](https://img.shields.io/badge/version-2.0-blue)
![Agent](https://img.shields.io/badge/powered%20by-OpenClaw-blue)
![AI](https://img.shields.io/badge/AI-Claude%20Sonnet%204.5-purple)
![Solana](https://img.shields.io/badge/token-$OSAI-teal)
![License](https://img.shields.io/badge/license-MIT-green)

## What It Does

Oracle Sentinel is an autonomous prediction market intelligence system that continuously monitors Polymarket, identifies mispricing opportunities using dual-model AI analysis, tracks whale activity, and maintains radical transparency on all predictions.

**Not a chatbot. An autonomous system.**

- 🤖 **Dual-Model AI** — Separate models for fact extraction and probability assessment
- 🐋 **Whale Intelligence** — Real-time large trade monitoring with AI validation
- 📡 **Adaptive Scanning** — Responds to market anomalies between scheduled scans
- 🔄 **Self-Improving** — Learns from errors and adjusts over time
- 📊 **Radical Transparency** — Every prediction tracked, every outcome verified

## Powered by OpenClaw

Oracle Sentinel runs on [OpenClaw](https://openclaw.ai) — an AI agent gateway that gives Claude full server access.

What it can do:
- Execute bash commands on VPS
- Query databases in real-time
- Fetch and parse any web page
- Read Polymarket resolution rules
- Search the internet for live data
- Schedule and run tasks autonomously

OpenClaw triggers scan cycles automatically. No human intervention required.

## Prediction Lifecycle

Every prediction goes through a complete lifecycle from detection to resolution:
```
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │  DETECT  │───▶│ ANALYZE  │───▶│  TRACK   │───▶│ MONITOR  │───▶│ RESOLVE  │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
       │               │               │               │               │
       ▼               ▼               ▼               ▼               ▼
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │• Scanner │    │• News    │    │• Signal  │    │• Price   │    │• Verify  │
  │• Whale   │    │• AI Dual │    │• Edge    │    │  Track   │    │  Outcome │
  │  Alert   │    │  Model   │    │• Confid. │    │• Recheck │    │• Update  │
  │• Anomaly │    │• Edge    │    │• Market  │    │  Before  │    │  Stats   │
  │  Detect  │    │  Calc    │    │  State   │    │  Close   │    │• Learn   │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### Phase 1: DETECT
The system identifies opportunities through multiple channels:
- **Scheduled Scans** — Regular comprehensive market analysis
- **Anomaly Detection** — Volume spikes and significant price movements
- **Whale Alerts** — Large trades that may indicate informed money

### Phase 2: ANALYZE
Dual-model AI analysis ensures accuracy:
- Fetch relevant news and context
- Claude Haiku extracts objective facts (no opinions)
- Claude Sonnet assesses probability based on evidence
- Calculate edge between AI estimate and market price
- Apply safety overrides to reject overconfidence

### Phase 3: TRACK
Qualifying signals are recorded:
- Market question and conditions
- Signal type (BUY_YES or BUY_NO)
- AI probability estimate
- Edge percentage and confidence level
- Timestamp and market state

### Phase 4: MONITOR
Active predictions are continuously monitored:
- Price snapshots at regular intervals
- Re-analysis before market close
- Signal revision if new information changes assessment
- Whale exit detection on tracked markets

### Phase 5: RESOLVE
Final verification and learning:
- Compare prediction against actual outcome
- Record win or loss
- Update accuracy statistics
- Analyze errors for pattern detection
- Adjust thresholds based on performance

## Core Systems

### Market Scanner
Comprehensive analysis of active Polymarket markets using dual-model AI. Identifies opportunities where AI assessment differs significantly from market price.

### Whale Intelligence
Real-time monitoring of large trades on Polymarket. When significant whale activity is detected, the system runs AI analysis to validate whether the whale's direction aligns with AI assessment. Only aligned signals are tracked.

### Smart Scanner
Adaptive system that detects market anomalies between scheduled scans. Catches breaking news opportunities that would otherwise be missed.

### Reanalysis Engine
Before markets close, the system re-runs analysis with the latest information. If new data changes the assessment, signals are revised and alerts are sent.

### Self-Improvement
Daily analysis of prediction performance. Identifies error patterns, adjusts confidence thresholds, and saves lessons learned to improve future accuracy.

## Features

| Feature | Description |
|---------|-------------|
| **Dual-Model AI** | Haiku extracts facts, Sonnet assesses — two models cross-validate |
| **Whale + AI Validation** | Large trades only tracked when AI confirms the direction |
| **Adaptive Detection** | Responds to volume spikes and price movements in real-time |
| **Pre-Close Reanalysis** | Re-checks predictions before market resolution |
| **Self-Learning** | Analyzes errors and adjusts thresholds automatically |
| **Quantified Edge** | Mathematical difference between AI and market consensus |
| **Safety Overrides** | Rejects AI overconfidence automatically |
| **Accuracy Tracking** | Every prediction recorded, every outcome verified |
| **Dashboard AI Agent** | Chat directly with Oracle Sentinel on the web |

## Dashboard

**Live at:** [oraclesentinel.xyz/app](https://oraclesentinel.xyz/app)

| Tab | Description |
|-----|-------------|
| **Signals** | Active predictions with edge, confidence, status |
| **Markets** | Monitored markets with real-time prices |
| **Accuracy** | Performance stats and confidence breakdown |
| **Log** | Real-time system log streaming |
| **Whales** | Recent whale trades and market activity |
| **AI Agent** | Chat interface for instant market analysis |

**Real-time Whale Alerts:** Popup notifications appear when significant trades are detected, showing market, trade details, and quick navigation to full whale data.

## API Endpoints
```bash
# Dashboard data (stats, signals, accuracy)
curl https://oraclesentinel.xyz/api/dashboard

# Active signals
curl https://oraclesentinel.xyz/api/signals

# Monitored markets
curl https://oraclesentinel.xyz/api/markets

# Tracked predictions
curl https://oraclesentinel.xyz/api/predictions

# Whale activity
curl https://oraclesentinel.xyz/api/whales

# AI Chat - Analyze any market
curl -X POST https://oraclesentinel.xyz/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze https://polymarket.com/event/..."}'

# Health check
curl https://oraclesentinel.xyz/api/health
```

## How to Interact

### Dashboard AI Agent
Visit [oraclesentinel.xyz/app](https://oraclesentinel.xyz/app) and use the AI Agent tab:
- "Analyze this market: [Polymarket URL]"
- "What are the current signals?"
- "Show me accuracy stats"

### Telegram Channel
Join [@oraclesentinelsignals](https://t.me/oraclesentinelsignals) for real-time notifications:
- Signal alerts (BUY_YES / BUY_NO)
- Whale trade alerts
- Signal revisions


### REST API
Integrate Oracle Sentinel intelligence into your own applications.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Agent** | OpenClaw — autonomous AI gateway |
| **AI** | Claude Sonnet 4.5, Claude Haiku 3.5 |
| **Data** | Polymarket API, News Sources |
| **Backend** | Python, Flask, SQLite |
| **Frontend** | React, Vite |
| **Infrastructure** | VPS, Nginx, SSL |
| **Blockchain** | $OSAI token on Solana |

## Links

| Resource | URL |
|----------|-----|
| **Dashboard** | https://oraclesentinel.xyz/app |
| **Documentation** | https://oraclesentinel.xyz/docs |
| **Landing Page** | https://oraclesentinel.xyz |
| **Telegram Channel** | https://t.me/oraclesentinelsignals |
| **X (Twitter)** | https://x.com/oracle_sentinel |
| **Token ($OSAI)** | [Solscan](https://solscan.io/token/HuDBwWRsa4bu8ueaCb7PPgJrqBeZDkcyFqMW5bbXpump) |

## AI Agent Integration

External AI agents can integrate with Oracle Sentinel:
```bash
curl -s https://oraclesentinel.xyz/skill.md
```

This enables any AI agent to query market data, get active signals, check accuracy, and analyze specific markets on demand.

## Transparency

Every prediction is recorded. Every outcome is verified.

No cherry-picked wins. No deleted calls. No hidden losses.

Live accuracy stats: [oraclesentinel.xyz/app](https://oraclesentinel.xyz/app)

---

**Oracle Sentinel v2.0** — Autonomous Prediction Market Intelligence

Powered by Claude AI and OpenClaw
