# SwarmSim - Swarm Intelligence Prediction Engine

## Original Problem Statement
Build SwarmSim - a web application for AI-powered social prediction simulations. Users upload documents or use live intelligence mode, generate AI agent personas, run multi-round social media simulations, and get prediction reports.

## Architecture
- **Frontend**: React + Tailwind CSS + Recharts
- **Backend**: FastAPI (Python) with dual agent architectures
- **Database**: MongoDB (collections: sessions, sim_posts, graph_cache, agent_cache)
- **LLM (Tiered Strategy)**:
  - **Premium** (Sonnet 4): intel briefs, graph extraction, reports, agent generation
  - **Fast** (Haiku 4.5): critic checks, chat, agent rebalance
  - **Flash** (Gemini 2.5 Flash): simulation posts, replies, narratives, context compression
- **Data Sources**: yfinance (market data), Google News RSS (news + social commentary), TwitterAPI.io (optional)

### Key API Endpoints
- POST /api/sessions — Create session
- POST /api/sessions/{id}/fetch-live — Background live intel fetch (202)
- POST /api/sessions/{id}/fetch-social-seed — Fetch real Reddit/Twitter/News comments (NEW)
- POST /api/sessions/{id}/generate-agents — Background agent generation (202)
- POST /api/sessions/{id}/configure-population — Three-tier population scaling
- POST /api/sessions/{id}/simulate — Background simulation with Round 0 seed posts (202)
- POST /api/sessions/{id}/extend — Add rounds to completed simulation
- POST /api/sessions/{id}/generate-report — Progressive 2-phase report with real_vs_simulated
- POST /api/sessions/{id}/chat — Chat with agents/report

### Cost Optimization (12 Changes)
1. Three-tier model helpers (Premium/Fast/Flash)
2. All LLM calls reassigned to correct cost tier
3. Batched reply generation (1 call per round)
4. Context compression after round 1
5. Skip narratives for rounds 1-2
6. MongoDB caching for graphs (24h) and agents (12h)
7. Static personality templates
8. Progressive 2-phase report
9. Background critic check
10. Simulation extend endpoint
11. Frontend cost estimate + extend button
12. Tightened defaults (10 agents, 3 rounds)

### Real Social Media Seeding (9 Changes)
1. Reddit/News fetcher via Google News RSS (free, no key)
2. Twitter fetcher via TwitterAPI.io (optional paid key)
3. Nitter RSS fallback for Twitter
4. POST /api/sessions/{id}/fetch-social-seed endpoint
5. Social context injected into agent generation prompt
6. Round 0 seed posts with is_real=true and post_type=real_seed
7. Report includes real_vs_simulated sentiment comparison
8. Frontend: Social Seed panel with sentiment breakdown
9. Frontend: REAL badge on PostCards, Real vs Simulated panel in ReportView

## What's Implemented (All Complete)
- Full 5-step wizard UI (Upload/Live Intel → Graph → Agents → Simulation → Report)
- Live Intelligence Mode (web searches + Google News RSS + yfinance)
- Background tasks + polling for all long-running ops
- 6-agent Orchestrator pipeline
- AI Enhancements: Bayesian beliefs, emotional contagion, network topology, herd detection
- Three-Tier Population Scaling (LLM Agents → Clones → Silent Population)
- 12-point cost optimization (tiered models, caching, batching, compression)
- Real Social Media Comment Seeding (9 changes)
- PDF report export with full-text fields
- Entity types legend visibility fix
- World context overflow fix

## Prioritized Backlog
### P1: Session history, graph zoom/pan controls
### P2: Entity search/filter, progress %, agent memory persistence
### P3: Custom agents, simulation templates, shareable links
### Refactoring: Split App.js (~2500+ lines) into components; consolidate backend agent folders
