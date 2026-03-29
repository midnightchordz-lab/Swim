# SwarmSim - Product Requirements Document

## Original Problem Statement
Build **SwarmSim**, a highly advanced Swarm Intelligence Prediction Engine. The application allows users to run complex AI agent simulations to predict outcomes on various topics (financial, political, social). Core features include real-time web scraping, RSS news parsing, live financial data (`yfinance`), a 6-agent Orchestrator pipeline, advanced AI behaviors, a Three-Tier Population Scaling System, and a 3-Tier LLM Cost Reduction Routing Strategy.

## Architecture
- **Frontend**: React (monolithic App.js ~2600 lines) + Tailwind CSS + Shadcn/UI
- **Backend**: FastAPI + MongoDB + Background Tasks
- **LLM Integration**: Emergent Integrations Proxy (Claude Sonnet 4, Haiku 4.5, Gemini 2.5 Flash) + xAI Grok (grok-4-1-fast)
- **Data Sources**: yfinance, Google News RSS (feedparser), web scraping, **Grok X Search (real Twitter/X)**, **Grok Web Search**

## Core Features (All Implemented)
1. Document upload + Live Intelligence mode with real-time data fetching
2. Knowledge Graph extraction (entities + relationships)
3. AI Agent generation (10-300 personas with personalities, beliefs, influence)
4. Three-Tier Population Scaling (LLM agents, statistical clones, silent population)
5. Multi-round social media simulation with belief dynamics
6. Real Social Media Comment Seeding (Google News RSS + **Grok X Search**)
7. Comprehensive prediction report with factions, risks, confidence scores
8. PDF report download
9. Interactive chat with agents post-simulation
10. 3-Tier LLM Model Routing (Sonnet for premium, Haiku for fast, Gemini Flash for bulk)
11. 12-point Cost Reduction optimizations
12. **Grok (xAI) Integration** — Real Twitter/X data via x_search, Web intelligence via web_search

## UI Design System (Implemented Feb 2026)
- **Theme**: Dark cyberpunk (#06080f background, #00f5c4 cyan accent)
- **Fonts**: Space Mono (monospace), Space Grotesk (body), Syne (headings)
- **Effects**: Canvas particle background, grid overlay, glassmorphism (backdrop-blur)
- **Components**: Glass cards, steps bar, stats row, info sidebar, ticker bar, scan animations
- **Badges**: "Grok Active" (violet), "System Online" (cyan)

## Grok Integration (Feb 2026)
- **SDK**: xai-sdk v1.11.0, model grok-4-1-fast
- **XAI_API_KEY** stored in backend/.env
- **fetch_grok_twitter()**: Uses x_search tool for real tweets — no Twitter API needed
- **fetch_grok_web_intel()**: Uses web_search tool for real-time intelligence briefs
- **Fallback**: Gracefully falls back to Nitter/RSS + Claude if Grok is unavailable
- **Frontend**: "Grok Active" badge in header, "Powered by Grok X Search" in social seed, Grok X Intelligence Brief display

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
- [x] UI Redesign — Cyberpunk dark theme with glassmorphism (Feb 2026)
- [x] **Grok (xAI) Integration** — Real Twitter + Web Intel (Feb 2026)

## Backlog (Prioritized)
### P1 - Upcoming
- Session history to resume previous simulations
- Graph zoom/pan controls for knowledge graph

### P2 - Future
- Entity search/filter in knowledge graph
- Progress percentage during long operations
- Agent memory persistence across sessions
- Refactor App.js into separate components (~2600 lines)

### P3 - Nice to Have
- Custom agent creation
- Simulation templates
- Shareable links

## Known Issues
- LLM Budget Exhaustion: If Emergent Universal Key balance is low, simulations will fail with 400 errors. User needs to top up via Profile > Universal Key > Add Balance.

## Key API Endpoints
- GET /api/health — Returns grok_available, twitter_source
- POST /api/sessions — Create session
- POST /api/sessions/{id}/fetch-live — Fetch live data (+ Grok web intel + Grok Twitter seed)
- POST /api/sessions/{id}/fetch-social-seed — Fetch social seed data (Grok x_search first, fallback to Nitter)
- POST /api/sessions/{id}/generate-agents — Generate AI agents
- POST /api/sessions/{id}/configure-population — Configure population tiers
- POST /api/sessions/{id}/simulate — Run simulation
- POST /api/sessions/{id}/extend — Extend simulation rounds
- GET /api/sessions/{id}/report/pdf — Download PDF report

## 3rd Party Integrations
- Emergent Integrations Proxy: Claude Sonnet 4, Haiku 4.5, Gemini 2.5 Flash (via EMERGENT_LLM_KEY)
- xAI Grok: grok-4-1-fast (via XAI_API_KEY, xai-sdk)
- Google News RSS: feedparser (no key)
- yfinance: no key
