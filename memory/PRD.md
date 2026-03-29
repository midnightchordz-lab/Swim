# SwarmSim - Swarm Intelligence Prediction Engine

## Original Problem Statement
Build SwarmSim - a web application for AI-powered social prediction simulations. Users upload documents or use live intelligence mode, generate AI agent personas, run multi-round social media simulations, and get prediction reports.

## Architecture
- **Frontend**: React + Tailwind CSS + Recharts
- **Backend**: FastAPI (Python) with dual agent architectures
- **Database**: MongoDB
- **LLM (Tiered Strategy)**:
  - **Premium** (deep reasoning): Claude Sonnet 4 (`claude-sonnet-4-20250514`) — intel briefs, graph extraction, reports, agent generation
  - **Fast** (medium tasks): Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) — critic checks, chat, agent rebalance
  - **Flash** (bulk generation): Gemini 2.5 Flash (`gemini-2.5-flash`) — simulation posts, replies, narratives
- **Financial Data**: yfinance (free)
- **News RSS**: Google News RSS via feedparser (free)

### Agent Architectures
```
/app/backend/agents/           — AI Enhancement agents
  critic.py                     — Herd detection, diversity scoring, report quality
  belief_tracker.py             — Bayesian belief position tracking per agent
  emotional_contagion.py        — Emotion spread with personality susceptibility
  network.py                    — Hub/peripheral assignment, Pareto follower counts
  population.py                 — Three-tier population scaling (clones, silent pop)

/app/backend/services/agents/  — Pipeline orchestration agents
  orchestrator.py               — Coordinates Intel/Graph/Persona/Sim/Report pipeline (accepts call_fns dict)
  intel_agent.py                — News synthesis + brief generation (max_tokens=800)
  graph_agent.py                — Entity/relationship extraction (max_tokens=1500)
  persona_agent.py              — Diverse persona generation (max_tokens=2000) + rebalancing (max_tokens=1000)
  sim_director.py               — Multi-round simulation (max_tokens=80-150)
  critic_agent.py               — LLM-based evaluation (max_tokens=200)
  report_agent.py               — Prediction report with narrative arc (max_tokens=1500)
```

### Simulation Pipeline
1. Network assignment (10% hubs, Pareto followers)
2. Belief + emotion initialisation
3. Per-round: batch post gen (Gemini Flash) → batched replies → belief update → emotion spread → herd check → narrative
4. Contrarian event injection when herd>0.7
5. Report generation (Sonnet 4) → pure Python quality scoring

### Cost Optimization (Tiered LLM Strategy)
- **Before**: All calls used Claude Sonnet 4 (~$0.40/simulation)
- **After**: Tiered model routing (~$0.09/simulation, ~78% cost reduction)
- Reply generation batched: 1 LLM call for all replies per round (was N individual calls)
- max_tokens slashed across all agents

## What's Implemented (All Complete)
- Full 5-step wizard UI
- Live Intelligence Mode (8 web searches + Google News RSS + yfinance)
- Background tasks for all long-running ops (live-fetch, agents, simulation)
- Agent limit raised to 300
- Batch post generation (10 agents per call, using Gemini Flash)
- Batched reply generation (all replies per round in 1 call)
- Belief tracking (position + certainty per agent, updated per round)
- Emotional contagion (valence/arousal, personality-based susceptibility)
- Network effects (hub/peripheral agents, Pareto follower distribution)
- Herd detection with automatic contrarian event injection
- Round narratives for temporal context
- Quality scoring (0-10) on reports with overconfidence flagging
- UI: EmotionalTemperatureGauge, SentimentChart, HUB badges, belief indicators, story arc
- Three-Tier Population Scaling System (Tier 1: LLM Agents, Tier 2: Clones, Tier 3: Silent Population)
- Tiered LLM Model Strategy (Premium/Fast/Flash)

## Prioritized Backlog
### P1: Session history, graph zoom/pan
### P2: Entity search/filter, progress %, agent memory persistence
### P3: Custom agents, simulation templates, shareable links
