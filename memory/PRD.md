# SwarmSim - Swarm Intelligence Prediction Engine

## Original Problem Statement
Build SwarmSim - a web application for AI-powered social prediction simulations. Users upload documents or use live intelligence mode, generate AI agent personas, run multi-round social media simulations, and get prediction reports.

## Architecture
- **Frontend**: React + Tailwind CSS + Recharts
- **Backend**: FastAPI (Python) with dual agent architectures
- **Database**: MongoDB
- **LLM**: Anthropic Claude (claude-sonnet-4-20250514) via Emergent LLM Key
- **Financial Data**: yfinance (free)
- **News RSS**: Google News RSS via feedparser (free)

### Agent Architectures
```
/app/backend/agents/           — AI Enhancement agents (NEW)
  critic.py                     — Herd detection, diversity scoring, report quality
  belief_tracker.py             — Bayesian belief position tracking per agent
  emotional_contagion.py        — Emotion spread with personality susceptibility
  network.py                    — Hub/peripheral assignment, Pareto follower counts

/app/backend/services/agents/  — Pipeline orchestration agents
  orchestrator.py               — Coordinates Intel/Graph/Persona/Sim/Report pipeline
  intel_agent.py                — News synthesis + brief generation
  graph_agent.py                — Entity/relationship extraction
  persona_agent.py              — Diverse persona generation + rebalancing
  sim_director.py               — (Legacy) Multi-round simulation
  critic_agent.py               — (Legacy) LLM-based evaluation
  report_agent.py               — Prediction report with narrative arc
```

### Simulation Pipeline (New)
1. Network assignment (10% hubs, Pareto followers)
2. Belief + emotion initialisation
3. Per-round: batch post gen → belief update → emotion spread → herd check → narrative
4. Contrarian event injection when herd>0.7
5. Report generation → pure Python quality scoring

## What's Implemented (All Complete)
- Full 5-step wizard UI
- Live Intelligence Mode (8 web searches + Google News RSS + yfinance)
- Background tasks for all long-running ops (live-fetch, agents, simulation)
- Agent limit raised to 300
- Batch post generation (10 agents per Claude call)
- Belief tracking (position + certainty per agent, updated per round)
- Emotional contagion (valence/arousal, personality-based susceptibility)
- Network effects (hub/peripheral agents, Pareto follower distribution)
- Herd detection with automatic contrarian event injection
- Round narratives for temporal context
- Quality scoring (0-10) on reports with overconfidence flagging
- UI: EmotionalTemperatureGauge, SentimentChart, HUB badges, belief indicators, story arc

## Prioritized Backlog
### P1: Session history, graph zoom/pan
### P2: Entity search/filter, progress %, agent memory persistence
### P3: Custom agents, simulation templates, shareable links
