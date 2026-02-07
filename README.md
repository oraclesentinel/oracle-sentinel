# Oracle Sentinel

Autonomous AI agent for Polymarket prediction intelligence.

![Status](https://img.shields.io/badge/status-live-brightgreen)
![Agent](https://img.shields.io/badge/powered%20by-OpenClaw-blue)
![AI](https://img.shields.io/badge/AI-Claude%20Sonnet%204.5-purple)
![Solana](https://img.shields.io/badge/token-$OSAI-teal)
![License](https://img.shields.io/badge/license-MIT-green)

## What It Does

Oracle Sentinel scans Polymarket prediction markets every 4 hours, identifies mispricing using dual-model AI analysis, and tracks every prediction with radical transparency.

- **Dual-model AI** — Claude Haiku extracts facts, Claude Sonnet assesses probability
- **Sports Intelligence** — Real-time data for 12 leagues (NFL, NBA, NHL, MLB, Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Champions League, MMA, F1)
- **Quantified edge** — exact percentage difference between AI and market
- **Radical transparency** — every prediction tracked, every outcome verified

## How It Works
```
┌─────────────────────────────────────────────────────────────┐
│                    ORACLE SENTINEL                          │
├─────────────────────────────────────────────────────────────┤
│  1. INGEST   → Fetch live prices via Polymarket Gamma API   │
│  2. RESEARCH → Search news (DuckDuckGo + full extraction)   │
│  3. SPORTS   → Fetch standings, form, H2H via SofaSport API │
│  4. EXTRACT  → Claude Haiku extracts facts (no opinions)    │
│  5. ASSESS   → Claude Sonnet computes AI probability        │
│  6. SIGNAL   → Edge calculator generates BUY/NO_TRADE       │
│  7. TRACK    → Accuracy tracker records every outcome       │
│  8. ALERT    → Whale trades monitor detects large moves     │
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
| **Sports Intelligence** | Live standings, form, H2H, streaks for 12 leagues via SofaSport API |
| **Real-Time Prices** | Live market data via Polymarket Gamma API |
| **Deep News Research** | Full article extraction from DuckDuckGo + Google News |
| **Whale Trade Alerts** | Real-time monitoring of $5,000+ trades with TX verification |
| **Dashboard AI Agent** | Chat directly with Oracle Sentinel on the web dashboard |
| **Self-Learning** | Re-analyzes predictions before market close, revises if new data |
| **Quantified Edge** | Mathematical difference between AI and market consensus |
| **Safety Overrides** | Code rejects AI overconfidence automatically |
| **Accuracy Tracking** | Price snapshots at 1h, 6h, 24h — wins and losses recorded |

## Adaptive Intelligence

Oracle Sentinel doesn't just scan on a schedule — it reacts to market movements in real-time.

**Smart Scanner** monitors all markets every 10 minutes:
- **Volume Spike Detection** — triggers when volume increases 50%+ in 1 hour
- **Price Movement Detection** — triggers when price moves 10%+ in 1 hour
- **Instant Full Analysis** — fetches news, runs AI, tracks prediction
- **Real-time Alerts** — sends Telegram notification with signal

This means Oracle Sentinel catches breaking news opportunities that would be missed by fixed 4-hour scans.

## Sports Intelligence

For sports markets, Oracle Sentinel fetches **real-time data** from SofaSport API:

| Data Type | Description |
|-----------|-------------|
| **League Standings** | Current position, points, wins, losses, goal difference |
| **Team Form** | Last 5-10 match results with scores |
| **Head-to-Head** | Historical matchups between teams |
| **Betting Streaks** | Over 2.5 goals, clean sheets, scoring patterns |
| **Fan Predictions** | Crowd sentiment from 30K+ votes |
| **Pre-match Ratings** | Team form ratings and position context |

**Supported Leagues:**
- ⚽ Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Champions League, Europa League
- 🏀 NBA
- 🏈 NFL
- 🏒 NHL
- ⚾ MLB
- 🥊 UFC/MMA
- 🏎️ Formula 1

This gives Oracle Sentinel a **data advantage** over AI systems that only use news articles.

## Links

| Resource | URL |
|----------|-----|
| **Dashboard** | https://oraclesentinel.xyz/app |
| **Documentation** | https://oraclesentinel.xyz/docs |
| **Landing Page** | https://oraclesentinel.xyz |
| **Telegram Bot** | https://t.me/oraclesentinel_pm_bot |
| **Telegram Channel** | https://t.me/oraclesentinelsignals |
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

# AI Chat (analyze any market)
curl -X POST https://oraclesentinel.xyz/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze https://polymarket.com/event/..."}'

# Health check
curl https://oraclesentinel.xyz/api/health
```

## Monitoring Systems

| System | Frequency | Purpose |
|--------|-----------|---------|
| **Market Scanner** | Every 4 hours | Analyze top markets, generate signals |
| **Smart Scanner** | Every 10 minutes | Detect volume/price spikes, instant analysis |
| **Whale Monitor** | Every 5 minutes | Detect $5,000+ trades, send alerts with TX hash |
| **Re-analysis** | Every hour | Re-analyze markets closing in 5-6 hours |
| **Auto Resolver** | Every hour | Verify predictions against final outcomes |
| **Price Updater** | Every scan | Track market movements for accuracy |

## Tech Stack

**Intelligence:**
- Claude Sonnet 4.5 — probability assessment
- Claude Haiku 3.5 — fact extraction
- SofaSport API — real-time sports data

**Data Sources:**
- Polymarket Gamma API — live market prices
- DuckDuckGo + Trafilatura — news search & extraction
- SofaSport — standings, form, H2H for 12 leagues

**Infrastructure:**
- OpenClaw — autonomous agent gateway
- Python + Flask API
- React dashboard
- SQLite database
- Nginx + SSL

**Blockchain:**
- $OSAI token on Solana (pump.fun)

## How to Interact

**Via Dashboard AI Agent:**
Visit [oraclesentinel.xyz/app](https://oraclesentinel.xyz/app), click the chat button, and ask anything:
- "Analyze this market: [Polymarket URL]"
- "Research and analyze: [Polymarket URL]" (includes news context)
- "What are the current signals?"
- "Show me your accuracy stats"

**Via Telegram Bot:**
Send any Polymarket URL to [@oraclesentinel_pm_bot](https://t.me/oraclesentinel_pm_bot) and get instant AI analysis with:
- Resolution rules breakdown
- AI probability vs market price
- Edge calculation
- Signal recommendation

**Via Telegram Alerts:**
Join the channel to receive automatic notifications:
- Signal reports every 4 hours
- Whale trade alerts ($5,000+ trades) every 5 minutes

**Via API:**
Integrate Oracle Sentinel's intelligence into your own tools using our REST API.

## AI Agent Integration

External AI agents can integrate with Oracle Sentinel using our skill file:
```
curl -s https://oraclesentinel.xyz/skill.md
```

This enables any AI agent to:
- Query real-time market data
- Get active trading signals
- Check prediction accuracy
- Analyze specific markets on demand

**Available Endpoints:**

| Endpoint | Description |
|----------|-------------|
| `GET /api/signals` | Active trading signals with edge calculations |
| `GET /api/markets` | All monitored markets with current prices |
| `GET /api/predictions` | Tracked predictions and outcomes |
| `GET /api/dashboard` | Full dashboard data including accuracy stats |
| `POST /api/chat` | AI chat for market analysis |
| `GET /api/health` | System health check |

**Example: Fetch Signals**
```bash
curl -s https://oraclesentinel.xyz/api/signals | jq '.[:3]'
```

For detailed integration instructions, see [skill.md](https://oraclesentinel.xyz/skill.md).

## Transparency

Every prediction is recorded. Every outcome is verified.

No cherry-picked wins. No deleted calls. No hidden losses.

Current accuracy stats available live at [oraclesentinel.xyz/app](https://oraclesentinel.xyz/app)

---

Powered by Claude and OpenClaw.