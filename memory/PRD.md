# SwarmSim - Swarm Intelligence Prediction Engine

## Original Problem Statement
Build SwarmSim - a web application that allows users to upload documents, pose prediction questions, and utilizes AI agents to simulate social media discussions and generate structured prediction reports.

## Architecture
- **Frontend**: React with Tailwind CSS, dark theme (bg-gray-950)
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **LLM**: Anthropic Claude API (claude-sonnet-4-20250514) via Emergent LLM Key

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
7. Live Intelligence Mode - fetch real-time web data for topics without document upload

## What's Been Implemented

### Backend APIs (100% Complete)
- `POST /api/sessions` - Create session
- `GET /api/sessions/{id}` - Get session
- `POST /api/sessions/{id}/upload` - Upload document + extract knowledge graph
- `POST /api/sessions/{id}/fetch-live` - Live Intelligence: web scraping + intel brief
- `POST /api/sessions/{id}/refresh-intel` - Refresh live data for existing session
- `POST /api/sessions/{id}/generate-agents` - Generate AI agent personas
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
- 5-step wizard navigation with step indicators
- Mode toggle: Document Upload vs Live Intelligence
- Step 1 Upload: Drag-drop zone, prediction question input
- Step 1 Live: Topic input, prediction horizon selector, custom question (optional)
- Step 2: Agent count slider (10-50), agent cards grid with personality badges
- Step 3: Round slider, dual Twitter/Reddit feeds with real-time updates
- Step 4: Prediction report dashboard with confidence gauge, factions, risks
- Step 5: Chat interface with agent sidebar

### Features
- Dark theme with tsparticles background, glowing cards, skeleton loaders
- Interactive force-directed graph visualization (react-force-graph-2d)
- Personality color-coding (Skeptic, Optimist, Insider, etc.)
- Auto-scrolling feeds during simulation
- PDF report download (fpdf2)
- Intel brief display with key developments & data points for live mode

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
