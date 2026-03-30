# SwarmSim - Product Requirements Document

## Original Problem Statement
Build **SwarmSim**, a highly advanced Swarm Intelligence Prediction Engine. The application allows users to run complex AI agent simulations to predict outcomes on various topics (financial, political, social). Core features include real-time web scraping, RSS news parsing, live financial data (`yfinance`), a 6-agent Orchestrator pipeline, advanced AI behaviors, a Three-Tier Population Scaling System, and a 3-Tier LLM Cost Reduction Routing Strategy.

## Architecture
- **Frontend**: React (monolithic App.js ~2960 lines) + Tailwind CSS + Shadcn/UI
- **Backend**: FastAPI + MongoDB + Background Tasks + APScheduler
- **LLM Integration**: Emergent Integrations Proxy (Claude Sonnet 4, Haiku 4.5, Gemini 2.5 Flash) + xAI Grok (grok-4-1-fast)
- **Data Sources**: yfinance, Google News RSS (feedparser), web scraping, Grok X Search, Grok Web Search

## Core Features (All Implemented)
1. Document upload + Live Intelligence mode with real-time data fetching
2. Knowledge Graph extraction — **Enhanced with GraphRAG L1+L2**
3. AI Agent generation — **Enhanced with GraphRAG context**
4. Three-Tier Population Scaling (LLM agents, statistical clones, silent population)
5. Multi-round social media simulation — **Enhanced with per-agent GraphRAG retrieval**
6. Real Social Media Comment Seeding (Google News RSS + Grok X Search)
7. Comprehensive prediction report — **Enhanced with full graph context**
8. PDF report download
9. Interactive chat with agents post-simulation
10. 3-Tier LLM Model Routing (Sonnet for premium, Haiku for fast, Gemini Flash for bulk + graph)
11. 12-point Cost Reduction optimizations
12. Grok (xAI) Integration — Real Twitter/X data via x_search, Web intelligence via web_search
13. **Prediction Tracking System** — Auto-freeze predictions, background scoring, accuracy dashboard

## GraphRAG Level 1 + Level 2 (Implemented Feb 2026)
### Level 1: Enhanced Graph Extraction
- Uncapped entity extraction (20-120+ entities depending on document size)
- Expanded entity types: Person, Organization, Country, Company, Policy, Law, Metric, Event, Concept, Asset, Instrument, Location
- Importance levels: High, Medium, Low (used for node sizing in visualization)
- Key tensions with entities_involved and stakes
- Prediction hooks (falsifiable questions)
- Agent diversity hints (viewpoints to ensure diverse agents)
- Post-processing: entity_index, adjacency_map for O(1) lookups
- Runtime indices stripped before MongoDB storage, rebuilt on load

### Level 2: Per-Agent GraphRAG Retrieval
- `retrieve_graph_context()`: Selects entities relevant to each agent
- `build_agent_generation_context()`: Graph themes/tensions for richer personas
- `generate_report_context()`: Full graph for deeper reports
- Graph extraction uses Gemini Flash (fast, avoids Sonnet timeouts)

## Prediction Tracking System (Implemented Feb 2026)
### Backend
- **freeze_prediction()**: Called after report generation. Extracts direction (UP/DOWN/FLAT), confidence, tickers, baseline prices, horizon, and agent belief positions. Saves to `prediction_records` collection.
- **score_pending_predictions()**: APScheduler job (every 30 min). Finds due predictions, fetches actual outcomes via yfinance (market) or Grok (political), calculates composite score (70% direction + 30% level accuracy).
- **score_single_prediction()**: Scores one prediction, updates agent_accuracy, accuracy_summary.
- **New MongoDB collections**: `prediction_records`, `agent_accuracy`, `accuracy_summary`

### API Endpoints
- `GET /api/predictions/accuracy` — Global stats, domain breakdown, top agents, calibration, recent predictions
- `GET /api/sessions/{id}/prediction-outcome` — Outcome for a specific session
- `POST /api/predictions/score-now/{id}` — Manual scoring trigger (for testing)

### Frontend
- **AccuracyDashboard**: Win rate, domain breakdown bars, calibration chart, top agents leaderboard, recent predictions
- **PredictionOutcomeBadge**: Shows CORRECT/INCORRECT badge with score on report view, or "pending" pulse
- **Accuracy button** in header — opens dashboard from anywhere

## UI Design System
- **Theme**: Dark cyberpunk (#06080f background, #00f5c4 cyan accent)
- **Fonts**: Space Mono (monospace), Space Grotesk (body), Syne (headings)
- **Effects**: Canvas particle background, grid overlay, glassmorphism
- **Graph viz**: Node sizing by importance, entity type breakdown, HIGH badges

## Completed Tasks
- [x] Core backend pipeline (6 agents + orchestrator)
- [x] Document upload + graph extraction
- [x] Live Intelligence mode (yfinance + web scraping)
- [x] Agent generation with personality types
- [x] Population scaling (3-tier)
- [x] Multi-round simulation
- [x] Real Social Media Comment Seeding
- [x] Prediction reports + PDF download
- [x] Interactive agent chat
- [x] 3-Tier LLM Cost Reduction (Sonnet/Haiku/Gemini)
- [x] 12-point cost optimization spec
- [x] UI Redesign — Cyberpunk dark theme (Feb 2026)
- [x] Grok (xAI) Integration (Feb 2026)
- [x] GraphRAG Level 1 + Level 2 Upgrade (Feb 2026)
- [x] Prediction Tracking System (Feb 2026)

## Backlog (Prioritized)
### P1 - Upcoming
- Session history to resume previous simulations
- Graph zoom/pan controls for knowledge graph

### P2 - Future
- Entity search/filter in knowledge graph
- Progress percentage during long operations
- Agent memory persistence across sessions
- Refactor App.js into separate components (~2960 lines)

### P3 - Nice to Have
- Custom agent creation
- Simulation templates
- Shareable links

## Key API Endpoints
- GET /api/health
- POST /api/sessions
- POST /api/sessions/{id}/fetch-live
- POST /api/sessions/{id}/fetch-social-seed
- POST /api/sessions/{id}/generate-agents
- POST /api/sessions/{id}/configure-population
- POST /api/sessions/{id}/simulate
- POST /api/sessions/{id}/extend
- GET /api/sessions/{id}/report/pdf
- GET /api/predictions/accuracy
- GET /api/sessions/{id}/prediction-outcome
- POST /api/predictions/score-now/{id}

## 3rd Party Integrations
- Emergent Integrations Proxy: Claude Sonnet 4, Haiku 4.5, Gemini 2.5 Flash (via EMERGENT_LLM_KEY)
- xAI Grok: grok-4-1-fast (via XAI_API_KEY, xai-sdk)
- Google News RSS: feedparser (no key)
- yfinance: no key
- APScheduler: background job scheduling (no key)
