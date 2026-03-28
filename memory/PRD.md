# SwarmSim - Swarm Intelligence Prediction Engine

## Original Problem Statement
Build SwarmSim - a web application that allows users to upload documents, pose prediction questions, and utilizes AI agents to simulate social media discussions and generate structured prediction reports. Includes Live Intelligence Mode for real-time web data fetching.

## Architecture
- **Frontend**: React with Tailwind CSS, dark theme (bg-gray-950)
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **LLM**: Anthropic Claude API (claude-sonnet-4-20250514) via Emergent LLM Key
- **Financial Data**: yfinance (free, no API key) for real-time stock/index prices

## User Personas
1. **Analyst**: Wants to understand public sentiment on policies/events
2. **Researcher**: Studies opinion dynamics and social behavior
3. **Decision Maker**: Needs prediction insights for strategic planning

## Core Requirements (Static)
1. Document upload (PDF, TXT, DOCX, MD, PNG, JPG, JPEG, WEBP, GIF) with 10MB limit
2. Knowledge graph extraction from documents
3. AI agent persona generation (10-50 agents)
4. Multi-round social media simulation (Twitter/Reddit feeds)
5. Prediction report with confidence scores, factions, risks
6. Interactive chat with agents and ReportAgent
7. Live Intelligence Mode - fetch real-time web data (8 searches, background task, progress terminal)
8. Real-time financial data integration (yfinance) for accurate market prices

## What's Been Implemented

### Backend APIs (100% Complete)
- `POST /api/sessions` - Create session
- `GET /api/sessions/{id}` - Get session
- `POST /api/sessions/{id}/upload` - Upload document + extract knowledge graph
- `POST /api/sessions/{id}/fetch-live` - **202 background task**: real-time market data + 8 web searches + Claude intel brief
- `GET /api/sessions/{id}/live-status` - Poll live fetch progress (step/total/message)
- `POST /api/sessions/{id}/refresh-intel` - Refresh live data (background task)
- `POST /api/sessions/{id}/generate-agents` - Background task agent generation
- `GET /api/sessions/{id}/agent-status` - Poll agent generation status
- `POST /api/sessions/{id}/simulate` - Start simulation (background task)
- `GET /api/sessions/{id}/simulation-status` - Poll simulation status
- `GET /api/sessions/{id}/posts` - Get all simulation posts
- `POST /api/sessions/{id}/generate-report` - Generate prediction report
- `GET /api/sessions/{id}/report` - Get stored report
- `GET /api/sessions/{id}/report/pdf` - Download PDF report
- `POST /api/sessions/{id}/chat` - Chat with agent/ReportAgent
- `GET /api/sessions/{id}/chat-history` - Get chat history
- `GET /api/prediction-horizons` - Get prediction horizon options

### Frontend (100% Complete)
- 5-step wizard with step indicators
- Mode toggle: Document Upload vs Live Intelligence
- Step 1 Upload: Drag-drop zone, prediction question input
- Step 1 Live: Topic input, prediction horizon, custom question, real-time progress terminal
- **Verified Real-Time Data card** with green badge showing actual market prices + % change
- Step 2: Agent count slider (10-50), agent cards grid (polling-based)
- Step 3: Round slider, dual Twitter/Reddit feeds
- Step 4: Prediction report dashboard with confidence gauge
- Step 5: Chat interface with agent sidebar

### Supported Financial Tickers (auto-detected from topic)
- Indian: Bank Nifty (^NSEBANK), NIFTY 50 (^NSEI), Sensex (^BSESN), Reliance, TCS, Infosys, HDFC Bank, ICICI Bank, SBI
- US: S&P 500, Dow Jones, Nasdaq, Tesla, Apple, Google, Microsoft, Amazon, Nvidia, Meta
- Crypto: Bitcoin (BTC-USD), Ethereum (ETH-USD)
- Commodities: Gold, Silver, Crude Oil

## Prioritized Backlog

### P1 (High Priority)
- [ ] Session history to resume previous simulations
- [ ] Graph zoom/pan controls

### P2 (Medium Priority)
- [ ] Entity search/filter in the graph
- [ ] Progress percentage during long operations
- [ ] Agent memory persistence across simulation rounds

### P3 (Low Priority)
- [ ] Custom agent creation
- [ ] Simulation templates
- [ ] Shareable report links

## Next Tasks
1. Session history page (save/load sessions)
2. Graph zoom/pan controls
