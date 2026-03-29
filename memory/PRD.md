# SwarmSim - Swarm Intelligence Prediction Engine

## Original Problem Statement
Build SwarmSim - a web application for AI-powered social prediction simulations. Users upload documents or use live intelligence mode, generate AI agent personas, run multi-round social media simulations, and get prediction reports.

## Architecture
- **Frontend**: React + Tailwind CSS + Recharts
- **Backend**: FastAPI (Python) with dual agent architectures
- **Database**: MongoDB (collections: sessions, sim_posts, graph_cache, agent_cache)
- **LLM (Tiered Strategy)**:
  - **Premium** (deep reasoning): Claude Sonnet 4 — intel briefs, graph extraction, reports, agent generation
  - **Fast** (medium tasks): Claude Haiku 4.5 — critic checks, chat, agent rebalance
  - **Flash** (bulk generation): Gemini 2.5 Flash — simulation posts, replies, narratives, context compression
- **Financial Data**: yfinance (free, no API key)
- **News RSS**: Google News RSS via feedparser (free)

### Cost Optimization Architecture (12 Changes)
1. Three-tier model helpers (call_claude_premium / call_claude_fast / call_gemini_flash)
2. All LLM calls reassigned to correct cost tier
3. Batched reply generation (1 call per round, not 1 per reply)
4. Context compression after round 1 (15-word summary replaces full graph)
5. Skip narratives for rounds 1-2 (only generate for round >= 3)
6. MongoDB caching for graphs (24h TTL) and agents (12h TTL)
7. Static personality templates (reduce agent gen prompt tokens)
8. Progressive 2-phase report (Phase 1: Haiku fast core → Phase 2: Sonnet deep analysis)
9. Background critic check (non-blocking, runs 30s after report)
10. Simulation extend endpoint (add rounds without regenerating graph/agents)
11. Frontend: cost estimate display, extend button, quality score polling
12. Tightened defaults: 10 agents (was 20), 3 rounds (was 5), max 10 rounds (was 15)

**Estimated cost per simulation: ~$0.09 (was ~$0.40, ~78% reduction)**

### Agent Architectures
```
/app/backend/agents/           — AI Enhancement agents (pure Python)
  critic.py, belief_tracker.py, emotional_contagion.py, network.py, population.py

/app/backend/services/agents/  — Pipeline orchestration agents (LLM wrappers)
  orchestrator.py, intel_agent.py, graph_agent.py, persona_agent.py, sim_director.py, critic_agent.py, report_agent.py
```

### Key API Endpoints
- POST /api/sessions — Create session
- POST /api/sessions/{id}/fetch-live — Background live intel fetch (202)
- GET /api/sessions/{id}/live-status — Poll live fetch progress
- POST /api/sessions/{id}/generate-agents — Background agent generation (202)
- POST /api/sessions/{id}/configure-population — Three-tier population scaling
- POST /api/sessions/{id}/simulate — Background simulation (202)
- POST /api/sessions/{id}/extend — Add rounds to completed simulation (NEW)
- POST /api/sessions/{id}/generate-report — Progressive 2-phase report
- POST /api/sessions/{id}/chat — Chat with agents/report
- GET /api/sessions/{id}/simulation-status — Poll simulation progress

## What's Implemented (All Complete)
- Full 5-step wizard UI (Upload/Live Intel → Graph → Agents → Simulation → Report)
- Live Intelligence Mode (web searches + Google News RSS + yfinance)
- Background tasks + polling pattern for all long-running ops
- 6-agent Orchestrator pipeline
- AI Enhancements: Bayesian beliefs, emotional contagion, network topology, herd detection
- Three-Tier Population Scaling (LLM Agents → Clones → Silent Population)
- 12-point cost optimization (tiered models, caching, batching, compression)
- Extend simulation endpoint
- Frontend cost estimate display
- Progressive 2-phase report generation
- Background critic quality check

## Prioritized Backlog
### P1: Session history (resume previous simulations), graph zoom/pan controls
### P2: Entity search/filter, progress %, agent memory persistence
### P3: Custom agents, simulation templates, shareable links
### Refactoring: Split App.js (~2400 lines) into components; consolidate backend agent folders
