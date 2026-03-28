# SwarmSim - Swarm Intelligence Prediction Engine

## Original Problem Statement
Build SwarmSim - a web application that allows users to upload documents, pose prediction questions, and utilizes AI agents to simulate social media discussions and generate structured prediction reports. Includes Live Intelligence Mode for real-time web data fetching.

## Architecture
- **Frontend**: React with Tailwind CSS, dark theme (bg-gray-950)
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **LLM**: Anthropic Claude API (claude-sonnet-4-20250514) via Emergent LLM Key
- **Financial Data**: yfinance (free, no API key) for real-time stock/index prices
- **News RSS**: Google News RSS via feedparser (free, no API key), Yahoo News RSS as fallback

## Core Requirements (Static)
1. Document upload (PDF, TXT, DOCX, MD, PNG, JPG, JPEG, WEBP, GIF) with 10MB limit
2. Knowledge graph extraction from documents
3. AI agent persona generation (10-50 agents)
4. Multi-round social media simulation (Twitter/Reddit feeds)
5. Prediction report with confidence scores, factions, risks
6. Interactive chat with agents and ReportAgent
7. Live Intelligence Mode - fetch real-time web data (news RSS + 8 web searches, background task, progress terminal)
8. Real-time financial data integration (yfinance) for accurate market prices

## What's Been Implemented - All Complete
- Full 5-step wizard (Upload/Live → Agents → Simulation → Report → Chat)
- Background task pattern for all long-running ops (live fetch, agents, simulation)
- News RSS headlines (Google News primary, Yahoo fallback) + 8 DuckDuckGo web searches
- Verified real-time financial data (yfinance) with 30+ ticker auto-detection
- Interactive force-directed knowledge graph
- PDF report download, tsparticles background, skeleton loaders

## Prioritized Backlog
### P1: Session history, graph zoom/pan
### P2: Entity search/filter, progress %, agent memory persistence
### P3: Custom agents, simulation templates, shareable links
