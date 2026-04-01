# SwarmSim - Product Requirements Document

## Original Problem Statement
Build **SwarmSim**, a Swarm Intelligence Prediction Engine. Users run AI agent simulations to predict outcomes on any topic.

## Architecture
- Frontend: React + Tailwind + Shadcn/UI | Backend: FastAPI + MongoDB + APScheduler
- LLM: Emergent Proxy (Sonnet 4, Haiku 4.5, Gemini Flash) + xAI Grok

## Completed Features
- [x] Core 6-agent orchestrator pipeline
- [x] Document upload + Live Intelligence mode
- [x] GraphRAG L1+L2 (importance, tensions, per-agent retrieval)
- [x] Graph Chunking helpers (chunk_content, merge_graph_sources, extract_from_social)
- [x] **Universal Domain Classifier** — 16 domains, keyword + LLM fallback
- [x] **Domain-aware agent archetypes** — occupations per domain
- [x] **Wikipedia + HN context** — free background data enrichment
- [x] **Non-financial scoring** — Claude-based prediction scoring for all domains
- [x] **Diverse example topics** — 8 examples across sports, politics, crypto, tech, entertainment
- [x] **Domain badge** — shows classified domain next to LIVE badge
- [x] Three-Tier Population Scaling
- [x] Multi-round simulation with per-agent GraphRAG context
- [x] Real Social Media Seeding (Google News RSS + Grok X Search)
- [x] Prediction reports + PDF + interactive chat
- [x] 3-Tier LLM Cost Reduction + 12-point optimizations
- [x] Prediction Tracking System (freeze, APScheduler scoring, accuracy dashboard)
- [x] Cyberpunk dark theme UI
- [x] **Universal Prediction Model** — 3-type scoring (DIRECTIONAL/OUTCOME/SENTIMENT)
- [x] **Bug Fix: Auto-question wrapping** — build_prediction_question() respects user input
- [x] **Bug Fix: NIFTY 50 classification** — Enhanced KEYWORD_MAP + ticker-based DIRECTIONAL override
- [x] **Bug Fix: Wrong direction labels** — Type-aware labels (YES/NO for OUTCOME, POSITIVE/NEGATIVE for SENTIMENT)

## Prediction Type Mapping
- DIRECTIONAL: financial, crypto, macro, real_estate (UP/DOWN/FLAT)
- OUTCOME: political, sports, business, science, legal, health, general (YES/NO/PARTIAL)
- SENTIMENT: technology, entertainment, geopolitical, social, media (POSITIVE/NEGATIVE/MIXED)

## Speed Optimizations
- Intel Agent: Haiku (was Sonnet) — 10s vs 30s
- Graph Agent: Haiku single-pass — 12s vs 60s+ timeouts
- Agent Generation: Haiku (was Sonnet) — faster persona creation
- Report Generation: Sonnet (kept for quality)
- Total pipeline: ~30-35s (was 60-90s)

## Backlog
### P1
- Session history to resume previous simulations
- Graph zoom/pan controls

### P2
- Entity search/filter, progress %, App.js refactor, agent memory persistence

### P3
- Custom agent creation, simulation templates, shareable links

## Known Constraints
- OOM: Do NOT re-enable chunk_and_extract concurrency
- Timeout: Do NOT revert Graph/Intel agents to Sonnet 4
- Indian indices: yfinance requires multiple ticker variant fallbacks
- Legacy predictions in DB have old domain/direction values (pre-bugfix)

## 3rd Party Integrations
- Emergent Proxy (EMERGENT_LLM_KEY), xAI Grok (XAI_API_KEY), yfinance, feedparser, APScheduler
