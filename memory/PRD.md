# SwarmSim - Swarm Intelligence Prediction Engine

## Original Problem Statement
Build SwarmSim - a web application that allows users to upload documents, pose prediction questions, and utilizes AI agents to simulate social media discussions and generate structured prediction reports.

## Architecture
- **Frontend**: React with Tailwind CSS, dark theme
- **Backend**: FastAPI (Python) with multi-agent architecture
- **Database**: MongoDB
- **LLM**: Anthropic Claude (claude-sonnet-4-20250514) via Emergent LLM Key
- **Financial Data**: yfinance (free)
- **News RSS**: Google News RSS via feedparser (free)

### Multi-Agent Architecture
```
/app/backend/services/agents/
  orchestrator.py   — Coordinates full pipeline, validates output, retries
  intel_agent.py    — Intelligence gathering, news synthesis, brief generation
  graph_agent.py    — Entity/relationship extraction, min-entity validation
  persona_agent.py  — Diverse persona generation, diversity scoring, rebalancing
  sim_director.py   — Multi-round simulation, round narratives, herd detection
  critic_agent.py   — Bias check, diversity score, herd detection, report quality
  report_agent.py   — Prediction report with narrative arc context
  common.py         — Shared utilities (JSON cleaning)
```

### Pipeline Flow
1. Intel Agent → Critic bias check (rewrite if bias>7) → Graph Agent
2. Persona Agent → Critic diversity score (rebalance if <0.6)
3. SimDirector (per-round: narratives, Critic herd check, contrarian injection if herd>0.7)
4. Report Agent → Critic quality score (0-10) + overconfidence flag

## What's Implemented (All Complete)
- Full 5-step wizard UI (Upload/Live → Agents → Simulation → Report → Chat)
- Background task pattern for all long-running ops
- 8 DuckDuckGo web searches + Google News RSS headlines
- Verified real-time financial data (yfinance, 30+ tickers)
- Interactive force-directed knowledge graph
- PDF report download
- Simulation Quality badge (Excellent/Good/Fair/Low)
- Herd detection + contrarian event injection
- Round narratives for temporal context

## Prioritized Backlog
### P1: Session history, graph zoom/pan
### P2: Entity search/filter, progress %, agent memory persistence
### P3: Custom agents, simulation templates, shareable links
