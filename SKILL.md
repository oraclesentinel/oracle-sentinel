---
name: oracle-sentinel
version: 1.0.0
description: Autonomous AI agent for Polymarket prediction intelligence. Dual-model analysis, quantified edge, radical transparency.
homepage: https://oraclesentinel.xyz
metadata: {"category":"ai-agents","api_base":"https://oraclesentinel.xyz/api","token":"$OSAI"}
---

# Oracle Sentinel

Autonomous AI agent for Polymarket prediction intelligence.

**Scans 79+ markets every 4 hours.** Identifies mispricing using dual-model AI. Tracks every prediction with radical transparency.

## Quick Start
```bash
# Get active trading signals
curl -s https://oraclesentinel.xyz/api/signals

# Get all monitored markets  
curl -s https://oraclesentinel.xyz/api/markets

# Get prediction tracking data
curl -s https://oraclesentinel.xyz/api/predictions

# Get full dashboard data
curl -s https://oraclesentinel.xyz/api/dashboard

# Check system health
curl -s https://oraclesentinel.xyz/api/health
```

## Telegram Bot

For interactive market analysis, message: **@oraclesentinel_pm_bot**

Send any Polymarket URL and the bot will:
1. Fetch the market page
2. Read resolution rules carefully
3. Check for loopholes in criteria
4. Search for relevant news
5. Calculate AI probability
6. Compare vs market price
7. Return signal with full reasoning

### Example
```
Analyze this market: https://polymarket.com/event/presidential-election-2024
```

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

## API Reference

**Base URL:** `https://oraclesentinel.xyz/api`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/signals` | Active trading signals with AI analysis |
| GET | `/markets` | All monitored Polymarket markets |
| GET | `/predictions` | Tracked predictions with accuracy data |
| GET | `/dashboard` | Complete dashboard data |
| GET | `/health` | System health status |

### Response: /api/signals
```json
[
  {
    "question": "Will X happen by Y date?",
    "signal_type": "BUY_YES",
    "ai_probability": 0.75,
    "market_price": 0.60,
    "edge": 15.0,
    "confidence": "HIGH",
    "reasoning": "AI explanation..."
  }
]
```

## Signal Types

| Signal | Meaning |
|--------|---------|
| `BUY_YES` | AI probability > market price by 3%+ |
| `BUY_NO` | AI probability < market price by 3%+ |
| `NO_TRADE` | Edge too small or low confidence |
| `SKIP` | Insufficient data |

## Confidence Levels

| Level | Description |
|-------|-------------|
| `HIGH` | Strong data support, clear reasoning |
| `MEDIUM` | Moderate data, some uncertainty |
| `LOW` | Limited data, high uncertainty |

## Safety Overrides

Oracle Sentinel has hardcoded safety rules:
- High edge + medium confidence = NO_TRADE
- Market >97% or <3% = automatic skip
- Low confidence = never generates signal

The system rejects its own overconfidence.

## Example: Fetch and Filter Signals
```python
import requests

signals = requests.get("https://oraclesentinel.xyz/api/signals").json()

for s in signals:
    if s["edge"] > 10 and s["confidence"] == "HIGH":
        print(f"{s['signal_type']}: {s['question']}")
        print(f"  Edge: +{s['edge']}%")
        print(f"  AI: {s['ai_probability']*100:.1f}%")
        print(f"  Market: {s['market_price']*100:.1f}%")
```

## Links

| Resource | URL |
|----------|-----|
| Dashboard | https://oraclesentinel.xyz/app |
| Documentation | https://oraclesentinel.xyz/docs |
| API Base | https://oraclesentinel.xyz/api |
| Telegram Bot | https://t.me/oraclesentinel_pm_bot |
| X (Twitter) | https://x.com/oracle_sentinel |
| GitHub | https://github.com/oraclesentinel/oracle-sentinel |
| Token ($OSAI) | https://solscan.io/token/HuDBwWRsa4bu8ueaCb7PPgJrqBeZDkcyFqMW5bbXpump |

## Powered By

- **Claude Sonnet 4.5** — Probability assessment
- **Claude Haiku 3.5** — Fact extraction
- **OpenClaw** — Autonomous agent gateway

## About

Oracle Sentinel runs autonomously 24/7. Every 4 hours, OpenClaw triggers a full scan cycle — no human intervention required.

Every signal has a number. Every prediction is recorded. Every outcome is verified.
