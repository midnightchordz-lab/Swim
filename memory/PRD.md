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

## What's Been Implemented (Jan 2026)

### Backend APIs (100% Complete)
- `POST /api/sessions` - Create session
- `GET /api/sessions/{id}` - Get session
- `POST /api/sessions/{id}/upload` - Upload document + extract knowledge graph
- `POST /api/sessions/{id}/generate-agents` - Generate AI agent personas
- `POST /api/sessions/{id}/simulate` - Start simulation (background task)
- `GET /api/sessions/{id}/simulation-status` - Poll simulation status
- `GET /api/sessions/{id}/posts` - Get all simulation posts
- `POST /api/sessions/{id}/generate-report` - Generate prediction report
- `GET /api/sessions/{id}/report` - Get stored report
- `POST /api/sessions/{id}/chat` - Chat with agent/ReportAgent
- `GET /api/sessions/{id}/chat-history` - Get chat history

### Frontend (100% Complete)
- 5-step wizard navigation with step indicators
- Step 1: Upload zone (drag-drop), prediction question input
- Step 2: Agent count slider (10-50), agent cards grid with personality badges
- Step 3: Round slider, dual Twitter/Reddit feeds with real-time updates
- Step 4: Prediction report dashboard with confidence gauge, factions, risks
- Step 5: Chat interface with agent sidebar

### Features
- Dark theme with custom scrollbars
- Personality color-coding (Skeptic, Optimist, Insider, etc.)
- Auto-scrolling feeds during simulation
- Progress bar for simulation rounds
- Responsive design

## Prioritized Backlog

### P0 (Critical) - None remaining

### P1 (High Priority)
- [ ] Session persistence (save/load sessions)
- [ ] Export report as PDF
- [ ] Agent memory persistence across simulation rounds

### P2 (Medium Priority)
- [ ] Knowledge graph visualization
- [ ] Agent relationship graph
- [ ] Simulation replay feature
- [ ] Multiple document upload support

### P3 (Low Priority)
- [ ] Custom agent creation
- [ ] Simulation templates
- [ ] Shareable report links
- [ ] Email notifications when simulation completes

## Next Tasks
1. Test full end-to-end flow with various document types
2. Add session list/history page
3. Implement report PDF export
