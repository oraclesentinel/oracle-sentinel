# Oracle Sentinel

Autonomous AI agent for Polymarket prediction intelligence.

![Status](https://img.shields.io/badge/status-live-brightgreen)
![Agent](https://img.shields.io/badge/powered%20by-OpenClaw-blue)
![AI](https://img.shields.io/badge/AI-Claude%20Sonnet%204.5-purple)
![Solana](https://img.shields.io/badge/token-$OSAI-teal)

## What It Does

Oracle Sentinel scans Polymarket prediction markets every 4 hours, identifies mispricing using dual-model AI analysis, and tracks every prediction with radical transparency.

- **79+ markets** monitored continuously
- **Dual-model AI** — Claude Haiku extracts facts, Claude Sonnet assesses probability
- **Quantified edge** — exact percentage difference between AI and market
- **Radical transparency** — every prediction tracked, every outcome verified

## How It Works
```
┌─────────────────────────────────────────────────────────────┐
│                    ORACLE SENTINEL                          │
├─────────────────────────────────────────────────────────────┤
│  1. INGEST   → Fetch market data + news from Polymarket     │
│  2. EXTRACT  → Claude Haiku extracts facts (no opinions)    │
│  3. ASSESS   → Claude Sonnet computes AI probability        │
│  4. SIGNAL   → Edge calculator generates BUY/NO_TRADE       │
│  5. TRACK    → Accuracy tracker records every outcome       │
└─────────────────────────────────────────────────────────────┘
```

## Powered by OpenClaw

Oracle Sentinel runs on [OpenClaw](https://openclaw.ai) — an AI agent gateway that gives Claude full server access.

**Not a chatbot. An autonomous system.**

What it can do:
- Execute bash commands on VPS
- Query databases in real-time
- Fetch and parse any web page
- Read Polymarket resolution rules
- Search the internet for live data
- Schedule tasks autonomously

Every 4 hours, OpenClaw triggers a full scan cycle. No human intervention.

## Features

| Feature | Description |
|---------|-------------|
| **Dual-Model AI** | Haiku extracts, Sonnet assesses — two models cross-validate |
| **Whale Detection** | Order book analysis for smart money signals |
| **Quantified Edge** | Mathematical difference between AI and market consensus |
| **Safety Overrides** | Code rejects AI overconfidence automatically |
| **Accuracy Tracking** | Price snapshots at 1h, 6h, 24h — wins and losses recorded |

## Links

| Resource | URL |
|----------|-----|
| **Dashboard** | https://oraclesentinel.xyz/app |
| **Documentation** | https://oraclesentinel.xyz/docs |
| **Landing Page** | https://oraclesentinel.xyz |
| **Telegram Bot** | https://t.me/OracleSentinelBot |
| **X (Twitter)** | https://x.com/oracle_sentinel |
| **Token ($OSAI)** | [Solscan](https://solscan.io/token/HuDBwWRsa4bu8ueaCb7PPgJrqBeZDkcyFqMW5bbXpump) |

## API Endpoints
```bash
# Get active signals
curl https://oraclesentinel.xyz/api/signals

# Get all markets
curl https://oraclesentinel.xyz/api/markets

# Get predictions
curl https://oraclesentinel.xyz/api/predictions

# Get dashboard data
curl https://oraclesentinel.xyz/api/dashboard

# Health check
curl https://oraclesentinel.xyz/api/health
```

## Tech Stack

**Intelligence:**
- Claude Sonnet 4.5 — probability assessment
- Claude Haiku 3.5 — fact extraction

**Infrastructure:**
- OpenClaw — autonomous agent gateway
- Python + Flask API
- React dashboard
- SQLite database
- Nginx + SSL

**Blockchain:**
- $OSAI token on Solana (pump.fun)

## How to Interact

**Via Telegram Bot:**
Send any Polymarket URL to [@OracleSentinelBot](https://t.me/OracleSentinelBot) and get instant AI analysis with:
- Resolution rules breakdown
- AI probability vs market price
- Edge calculation
- Signal recommendation

**Via API:**
Integrate Oracle Sentinel's intelligence into your own tools using our REST API.

## Transparency

Every prediction is recorded. Every outcome is verified.

No cherry-picked wins. No deleted calls. No hidden losses.

Current accuracy stats available live at [oraclesentinel.xyz/app](https://oraclesentinel.xyz/app)

---

**Built for the [Solana Agent Hackathon](https://colosseum.com/agent-hackathon)**

Powered by Claude and OpenClaw.
