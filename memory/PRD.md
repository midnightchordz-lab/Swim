# SwarmSim - Product Requirements Document

## Original Problem Statement
Build **SwarmSim**, a highly advanced Swarm Intelligence Prediction Engine. Users run complex AI agent simulations to predict outcomes on various topics (financial, political, social).

## Architecture
- **Frontend**: React (App.js ~2990 lines) + Tailwind CSS + Shadcn/UI
- **Backend**: FastAPI + MongoDB + APScheduler + Background Tasks
- **LLM**: Emergent Integrations Proxy (Sonnet 4, Haiku 4.5, Gemini 2.5 Flash) + xAI Grok
- **Data**: yfinance, Google News RSS, web scraping, Grok X Search, Grok Web Search

## Completed Features
- [x] Core 6-agent orchestrator pipeline
- [x] Document upload + Live Intelligence mode
- [x] GraphRAG L1+L2 (importance, tensions, per-agent retrieval)
- [x] **Graph Chunking** — Multi-chunk extraction + multi-source merge (brief+Twitter+Reddit)
- [x] Three-Tier Population Scaling
- [x] Multi-round simulation with per-agent GraphRAG context
- [x] Real Social Media Seeding (Google News RSS + Grok X Search)
- [x] Prediction reports + PDF download
- [x] Interactive agent chat
- [x] 3-Tier LLM Cost Reduction (Sonnet/Haiku/Gemini)
- [x] Grok (xAI) Integration
- [x] **Prediction Tracking System** — Auto-freeze, background scoring, accuracy dashboard
- [x] Cyberpunk dark theme UI

## Graph Chunking (Implemented Feb 2026)
- `chunk_content()`: Splits text into overlapping chunks (2500 chars, 300 overlap)
- `chunk_and_extract()`: Multi-pass extraction per chunk, merged via `merge_graph_sources()`
- `extract_from_social()`: Extracts entities from Twitter/Reddit posts
- `merge_graph_sources()`: Deduplicates entities by name, preserves highest importance
- Multi-source pipeline: intel brief + Grok X posts + Reddit → unified graph
- Live progress updates via MongoDB polling

## Prediction Tracking System (Implemented Feb 2026)
- `freeze_prediction()`: After report gen, saves prediction record
- `score_pending_predictions()`: APScheduler every 30min, scores via yfinance/Grok
- AccuracyDashboard: Win rate, domain breakdown, calibration, top agents
- PredictionOutcomeBadge: CORRECT/INCORRECT/pending on report view

## Key API Endpoints
- POST /api/sessions/{id}/fetch-live
- POST /api/sessions/{id}/generate-agents
- POST /api/sessions/{id}/simulate
- GET /api/sessions/{id}/report/pdf
- GET /api/predictions/accuracy
- GET /api/sessions/{id}/prediction-outcome
- POST /api/predictions/score-now/{id}

## Backlog
### P1
- Session history to resume previous simulations
- Graph zoom/pan controls

### P2
- Entity search/filter in knowledge graph
- Progress percentage during long operations
- Refactor App.js into separate components
- Agent memory persistence across sessions

### P3
- Custom agent creation, simulation templates, shareable links

## 3rd Party Integrations
- Emergent Integrations Proxy (EMERGENT_LLM_KEY)
- xAI Grok grok-4-1-fast (XAI_API_KEY)
- yfinance, feedparser, APScheduler (no keys)
