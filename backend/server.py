from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import json
import re
import random
import math
import asyncio
import io
import hashlib

import base64
import httpx

from agents import (
    check_herd, score_diversity, get_missing_personalities,
    initialise_beliefs, update_beliefs, get_belief_summary,
    assign_network_properties, get_visible_posts, get_network_stats,
    initialise_emotions, spread_emotions,
    get_emotional_temperature, get_emotion_label,
    generate_clones, generate_silent_population,
    generate_clone_posts, calculate_silent_reactions,
    get_agent_feed, get_demographic_breakdown,
)

# Load environment variables first
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import LLM integration
from emergentintegrations.llm.chat import LlmChat, UserMessage

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
TEXT_TRUNCATE_LIMIT = 12000
TRANSCRIPT_CAP = 8000

# Models
class SessionCreate(BaseModel):
    pass

class SessionResponse(BaseModel):
    session_id: str

class GenerateAgentsRequest(BaseModel):
    num_agents: int = Field(default=10, ge=10, le=300)

class SimulateRequest(BaseModel):
    num_rounds: int = Field(default=3, ge=3, le=10)

class ChatRequest(BaseModel):
    target_type: str  # "agent" or "report"
    target_id: str  # agent_id or "report_agent"
    message: str

class FetchLiveRequest(BaseModel):
    topic: str
    horizon: str = "Next month"
    prediction_query: Optional[str] = ""

class ConfigurePopulationRequest(BaseModel):
    tier1_agents: int = Field(default=50, ge=10, le=100)
    clone_multiplier: int = Field(default=10, ge=1, le=20)
    silent_population: int = Field(default=5000, ge=0, le=100000)

class InjectVariableRequest(BaseModel):
    variable: str
    num_new_rounds: int = Field(default=2, ge=1, le=5)

class ExtendSimulationRequest(BaseModel):
    additional_rounds: int = Field(default=3, ge=1, le=10)

# Prediction horizons
PREDICTION_HORIZONS = [
    "Next 24 hours",
    "Next week", 
    "Next month",
    "Next 3 months",
    "Next 6 months",
    "Long term (1+ year)"
]

# Topic categories for agent customization
TOPIC_CATEGORIES = {
    "financial": ["stock", "market", "crypto", "bitcoin", "trading", "investment", "economy", "fed", "interest rate", "inflation"],
    "political": ["election", "vote", "congress", "senate", "president", "policy", "law", "democrat", "republican", "legislation"],
    "geopolitical": ["war", "conflict", "military", "treaty", "sanctions", "diplomacy", "nato", "un", "border"],
    "sports": ["game", "match", "championship", "player", "team", "league", "score", "tournament", "coach"],
    "tech": ["ai", "startup", "tech", "software", "app", "launch", "product", "innovation", "company"],
    "social_cultural": ["trend", "viral", "culture", "social", "celebrity", "movement", "protest"]
}

def detect_topic_category(topic: str) -> str:
    """Detect the category of a topic for agent customization"""
    topic_lower = topic.lower()
    for category, keywords in TOPIC_CATEGORIES.items():
        if any(kw in topic_lower for kw in keywords):
            return category
    return "general"


# Personality templates — reduce LLM token usage for agent generation
PERSONALITY_TEMPLATES = {
    "Skeptic":     {"style": "analytical, questioning, demands evidence", "platform": "Reddit"},
    "Optimist":    {"style": "hopeful, solution-focused, encouraging",    "platform": "Twitter"},
    "Insider":     {"style": "authoritative, uses jargon, drops hints",   "platform": "Twitter"},
    "Contrarian":  {"style": "provocative, finds counterarguments",       "platform": "Twitter"},
    "Expert":      {"style": "precise, cites data, acknowledges limits",  "platform": "Reddit"},
    "Neutral":     {"style": "balanced, presents both sides",             "platform": "Reddit"},
    "Activist":    {"style": "passionate, calls to action, systemic lens","platform": "Twitter"},
    "Pragmatist":  {"style": "practical, action-oriented, avoids ideology","platform": "Reddit"},
}


# Financial ticker mapping for real-time price data
TICKER_MAP = {
    # Indian indices
    "bank nifty": "^NSEBANK",
    "banknifty": "^NSEBANK",
    "nifty bank": "^NSEBANK",
    "nifty 50": "^NSEI",
    "nifty50": "^NSEI",
    "nifty": "^NSEI",
    "sensex": "^BSESN",
    # US indices
    "s&p 500": "^GSPC",
    "s&p500": "^GSPC",
    "dow jones": "^DJI",
    "nasdaq": "^IXIC",
    # Crypto
    "bitcoin": "BTC-USD",
    "btc": "BTC-USD",
    "ethereum": "ETH-USD",
    "eth": "ETH-USD",
    # Major stocks
    "tesla": "TSLA",
    "apple": "AAPL",
    "google": "GOOGL",
    "microsoft": "MSFT",
    "amazon": "AMZN",
    "nvidia": "NVDA",
    "meta": "META",
    # Indian stocks
    "reliance": "RELIANCE.NS",
    "tcs": "TCS.NS",
    "infosys": "INFY.NS",
    "hdfc bank": "HDFCBANK.NS",
    "hdfc": "HDFCBANK.NS",
    "icici bank": "ICICIBANK.NS",
    "icici": "ICICIBANK.NS",
    "sbi": "SBIN.NS",
    "state bank": "SBIN.NS",
    # Commodities
    "gold": "GC=F",
    "silver": "SI=F",
    "crude oil": "CL=F",
    "oil": "CL=F",
}


def detect_tickers(topic: str) -> list:
    """Detect relevant financial tickers from a topic string"""
    topic_lower = topic.lower()
    found = []
    # Sort by key length descending to match longer phrases first
    for keyword, ticker in sorted(TICKER_MAP.items(), key=lambda x: -len(x[0])):
        if keyword in topic_lower and ticker not in found:
            found.append(ticker)
    return found[:5]  # Max 5 tickers


async def fetch_financial_data(topic: str) -> dict:
    """Fetch real-time financial data using yfinance for detected tickers"""
    import yfinance as yf
    
    tickers = detect_tickers(topic)
    if not tickers:
        return {"has_data": False, "tickers": [], "data": []}
    
    results = []
    for ticker_symbol in tickers:
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            price = info.get("regularMarketPrice") or info.get("currentPrice")
            prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose")
            
            if not price:
                # Try getting from history as fallback
                hist = ticker.history(period="5d")
                if not hist.empty:
                    price = float(hist["Close"].iloc[-1])
                    if len(hist) > 1:
                        prev_close = float(hist["Close"].iloc[-2])
            
            if price:
                change = None
                change_pct = None
                if prev_close and prev_close > 0:
                    change = round(price - prev_close, 2)
                    change_pct = round((change / prev_close) * 100, 2)
                
                result = {
                    "symbol": ticker_symbol,
                    "name": info.get("shortName") or info.get("longName") or ticker_symbol,
                    "price": round(price, 2),
                    "currency": info.get("currency", "USD"),
                    "change": change,
                    "change_pct": change_pct,
                    "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
                    "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
                    "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                    "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                    "volume": info.get("volume") or info.get("regularMarketVolume"),
                    "market_cap": info.get("marketCap"),
                    "prev_close": prev_close,
                }
                results.append(result)
                logger.info(f"Fetched financial data for {ticker_symbol}: {price}")
        except Exception as e:
            logger.warning(f"Failed to fetch financial data for {ticker_symbol}: {e}")
            continue
    
    return {
        "has_data": len(results) > 0,
        "tickers": tickers,
        "data": results,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }


def clean_json_response(text: str) -> str:
    """Strip markdown code fences and think tags from Claude responses"""
    # Remove think tags
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # Remove markdown code fences
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    return text.strip()


async def fetch_web_data(topic: str, horizon: str, session_id: str = None) -> dict:
    """Fetch live web data for a topic using DuckDuckGo search (5-8 queries covering multiple angles)"""
    import urllib.parse
    
    # 5-8 searches covering: latest news, expert analysis, data/statistics, sentiment signals
    search_queries = [
        f"{topic} latest news today {horizon}",
        f"{topic} breaking news last 48 hours",
        f"{topic} expert analysis opinion forecast",
        f"{topic} statistics data numbers 2025 2026",
        f"{topic} public sentiment reaction social media",
        f"{topic} key stakeholders positions decisions",
        f"{topic} risks challenges outlook",
        f"{topic} market impact economic implications",
    ]
    
    progress_steps = [
        "Searching latest news...",
        "Searching breaking developments...",
        "Pulling expert analysis...",
        "Pulling data & statistics...",
        "Scanning sentiment signals...",
        "Identifying key stakeholders...",
        "Assessing risks & challenges...",
        "Gathering market implications...",
    ]
    
    all_results = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for idx, query in enumerate(search_queries):
            # Update progress in DB if session_id provided
            if session_id:
                step_msg = progress_steps[idx] if idx < len(progress_steps) else f"Search {idx+1}..."
                await db.sessions.update_one(
                    {"id": session_id},
                    {"$set": {"live_progress": step_msg, "live_progress_step": idx + 1, "live_progress_total": len(search_queries)}}
                )
            
            try:
                encoded_query = urllib.parse.quote(query)
                url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
                
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                
                if response.status_code == 200:
                    html = response.text
                    snippets = re.findall(r'class="result__snippet"[^>]*>([^<]+)', html)
                    titles = re.findall(r'class="result__a"[^>]*>([^<]+)', html)
                    
                    for title, snippet in zip(titles[:4], snippets[:4]):
                        all_results.append({
                            "query": query,
                            "title": title.strip(),
                            "snippet": snippet.strip()
                        })
                        
            except Exception as e:
                logger.warning(f"Search failed for query '{query}': {e}")
                continue
            
            await asyncio.sleep(0.4)  # Rate limiting
    
    return {
        "results": all_results,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "query_count": len(search_queries)
    }


def fetch_yahoo_news(topic: str) -> str:
    """Fetch latest headlines from news RSS feeds (no API key needed)"""
    import feedparser
    from urllib.parse import quote
    
    headlines = []
    
    # Primary: Google News RSS
    try:
        url = f"https://news.google.com/rss/search?q={quote(topic)}&hl=en&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")[:150]
            published = entry.get("published", "")
            source = entry.get("source", {}).get("title", "Google News")
            headlines.append(f"[{source}] {title} — {summary} ({published})")
    except Exception as e:
        logger.warning(f"Google News RSS failed: {e}")
    
    # Fallback: Yahoo News RSS
    if not headlines:
        try:
            url = f"https://news.search.yahoo.com/rss?p={quote(topic)}&count=10"
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")[:150]
                published = entry.get("published", "")
                source = entry.get("source", {}).get("title", "Yahoo News")
                headlines.append(f"[{source}] {title} — {summary} ({published})")
        except Exception as e:
            logger.warning(f"Yahoo News RSS failed: {e}")
    
    return "\n".join(headlines)


async def _llm_call(provider: str, model: str, system_prompt: str, user_prompt: str, max_tokens: int, retries: int = 3) -> str:
    """Generic LLM call with retry logic for any provider/model."""
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="EMERGENT_LLM_KEY not configured")

    last_error = None
    for attempt in range(retries):
        try:
            chat = LlmChat(
                api_key=api_key,
                session_id=str(uuid.uuid4()),
                system_message=system_prompt
            )
            chat.with_model(provider, model)
            response = await chat.send_message(UserMessage(text=user_prompt))
            return response
        except Exception as e:
            last_error = e
            logger.warning(f"LLM ({model}) attempt {attempt + 1}/{retries} failed: {str(e)[:100]}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            raise
    raise last_error


async def call_claude_premium(system_prompt: str, user_prompt: str, max_tokens: int = 1500) -> str:
    """Sonnet 4 — deep reasoning only: graph extraction, agent generation, final report."""
    return await _llm_call("anthropic", "claude-sonnet-4-20250514", system_prompt, user_prompt, max_tokens)


async def call_claude_fast(system_prompt: str, user_prompt: str, max_tokens: int = 400) -> str:
    """Haiku 4.5 — medium tasks: chat, critic checks, auto-questions, agent rebalance."""
    return await _llm_call("anthropic", "claude-haiku-4-5-20251001", system_prompt, user_prompt, max_tokens)


async def call_gemini_flash(system_prompt: str, user_prompt: str, max_tokens: int = 400) -> str:
    """Gemini Flash — cheapest, bulk generation (posts, replies, narratives)."""
    return await _llm_call("gemini", "gemini-2.5-flash", system_prompt, user_prompt, max_tokens)


# Alias for backward compat (image uploads still use call_claude)
call_claude_premium_ref = call_claude_premium


async def call_claude(system_prompt: str, user_prompt: str, max_tokens: int = 1500, image_data: dict = None, retries: int = 3) -> str:
    """Legacy wrapper — routes to call_claude_premium for text, litellm for images."""
    if not image_data:
        return await call_claude_premium(system_prompt, user_prompt, max_tokens)

    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="EMERGENT_LLM_KEY not configured")

    last_error = None
    for attempt in range(retries):
        try:
            import litellm
            from emergentintegrations.llm.chat import get_integration_proxy_url
            proxy_url = get_integration_proxy_url()
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{image_data['media_type']};base64,{image_data['base64']}"}},
                        {"type": "text", "text": user_prompt}
                    ]
                }
            ]
            response = litellm.completion(
                model="claude-sonnet-4-20250514",
                messages=messages,
                api_key=api_key,
                api_base=proxy_url + "/llm",
                custom_llm_provider="openai",
                max_tokens=max_tokens,
                timeout=90
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            logger.warning(f"Claude vision attempt {attempt + 1}/{retries} failed: {str(e)[:100]}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            raise
    raise last_error


# ─── Caching functions ───────────────────────────────────────────────
async def get_cached_graph(topic: str, prediction_query: str) -> dict | None:
    """Return cached graph if same topic queried in last 24 hours."""
    cache_key = hashlib.md5(
        f"{topic.lower().strip()}{prediction_query[:50].lower()}".encode()
    ).hexdigest()
    cached = await db.graph_cache.find_one({
        "hash": cache_key,
        "created_at": {"$gt": (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()}
    })
    return json.loads(cached["graph_json"]) if cached else None

async def save_graph_cache(topic: str, prediction_query: str, graph: dict):
    cache_key = hashlib.md5(
        f"{topic.lower().strip()}{prediction_query[:50].lower()}".encode()
    ).hexdigest()
    await db.graph_cache.replace_one(
        {"hash": cache_key},
        {
            "hash": cache_key,
            "graph_json": json.dumps(graph),
            "topic": topic,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        upsert=True
    )

async def get_cached_agents(graph_hash: str, num_agents: int) -> list | None:
    """Return cached agents if same graph + count used in last 12 hours."""
    cache_key = f"{graph_hash}_{num_agents}"
    cached = await db.agent_cache.find_one({
        "hash": cache_key,
        "created_at": {"$gt": (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()}
    })
    return json.loads(cached["agents_json"]) if cached else None

async def save_agent_cache(graph_hash: str, num_agents: int, agents: list):
    cache_key = f"{graph_hash}_{num_agents}"
    await db.agent_cache.replace_one(
        {"hash": cache_key},
        {
            "hash": cache_key,
            "agents_json": json.dumps(agents),
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        upsert=True
    )


async def parse_document(file: UploadFile) -> tuple[str, dict]:
    """Parse uploaded document to plain text. Returns (text, image_data) where image_data is None for non-image files."""
    content = await file.read()
    filename = file.filename.lower()
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 10MB limit")
    
    # Check if it's an image file
    image_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.gif')
    if any(filename.endswith(ext) for ext in image_extensions):
        # Return image data for Claude vision
        media_type = file.content_type or "image/png"
        if filename.endswith('.jpg') or filename.endswith('.jpeg'):
            media_type = "image/jpeg"
        elif filename.endswith('.png'):
            media_type = "image/png"
        elif filename.endswith('.webp'):
            media_type = "image/webp"
        elif filename.endswith('.gif'):
            media_type = "image/gif"
        
        image_data = {
            "media_type": media_type,
            "base64": base64.b64encode(content).decode('utf-8')
        }
        return "", image_data
    
    try:
        if filename.endswith('.pdf'):
            import pdfplumber
            import io
            text_parts = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            return '\n'.join(text_parts), None
        
        elif filename.endswith('.docx'):
            from docx import Document
            import io
            doc = Document(io.BytesIO(content))
            return '\n'.join([para.text for para in doc.paragraphs]), None
        
        else:  # .txt, .md, or fallback
            return content.decode('utf-8', errors='ignore'), None
    
    except Exception as e:
        logger.error(f"Error parsing document: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse document: {str(e)}")


# API Endpoints
@api_router.get("/health")
async def health_check():
    return {"status": "ok"}


@api_router.post("/sessions", response_model=SessionResponse)
async def create_session():
    """Create a new SwarmSim session"""
    session_id = str(uuid.uuid4())
    session = {
        "id": session_id,
        "status": "created",
        "graph_json": None,
        "agents_json": None,
        "report_json": None,
        "prediction_query": None,
        "data_mode": "upload",  # 'upload' or 'live'
        "topic": None,
        "intel_brief": None,
        "fetched_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.sessions.insert_one(session)
    return {"session_id": session_id}


@api_router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session status and metadata"""
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@api_router.post("/sessions/{session_id}/upload")
async def upload_document(
    session_id: str,
    file: UploadFile = File(...),
    prediction_query: str = Form(...)
):
    """Upload document and extract knowledge graph via Graph Agent"""
    from services.agents import graph_agent as graph_agent_module
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Parse document
    text, image_data = await parse_document(file)
    
    try:
        graph = await graph_agent_module.run_from_document(
            text, prediction_query, call_claude, image_data=image_data
        )
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse knowledge graph from AI response")
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")
    
    # Update session
    await db.sessions.update_one(
        {"id": session_id},
        {
            "$set": {
                "status": "graph_ready",
                "graph_json": json.dumps(graph),
                "prediction_query": prediction_query,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"status": "graph_ready", "graph": graph}


async def run_live_fetch(session_id: str, topic: str, horizon: str, prediction_query: str):
    """Background task: orchestrator runs Intel + Graph pipeline."""
    from services.agents import orchestrator
    try:
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {"live_progress": "Initializing web search...", "live_progress_step": 0, "live_progress_total": 9}}
        )

        # Fetch real-time financial data
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {"live_progress": "Fetching real-time market data...", "live_progress_step": 0}}
        )
        financial_data = await fetch_financial_data(topic)

        # Fetch news headlines
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {"live_progress": "Fetching latest news headlines...", "live_progress_step": 1}}
        )
        yahoo_headlines = fetch_yahoo_news(topic)
        logger.info(f"News headlines fetched: {len(yahoo_headlines.splitlines())} items")

        # Fetch web search data (8 queries with progress tracking)
        web_data = await fetch_web_data(topic, horizon, session_id=session_id)

        if not web_data.get("results") and not financial_data.get("has_data"):
            await db.sessions.update_one(
                {"id": session_id},
                {"$set": {"live_fetch_status": "failed", "live_fetch_error": "Could not fetch live data. Please try a different topic."}}
            )
            return

        # Build contexts for the orchestrator
        context_parts = [f"- {r['title']}: {r['snippet']}" for r in web_data["results"][:20]]
        web_context = "\n".join(context_parts)

        financial_context = ""
        if financial_data.get("has_data"):
            fin_parts = ["\n=== VERIFIED REAL-TIME MARKET DATA (use these exact numbers) ==="]
            for fd in financial_data["data"]:
                line = f"- {fd['name']} ({fd['symbol']}): {fd['currency']} {fd['price']}"
                if fd.get("change") is not None:
                    direction = "up" if fd["change"] > 0 else "down"
                    line += f" | Change: {fd['change']:+.2f} ({fd['change_pct']:+.2f}%) [{direction}]"
                if fd.get("prev_close"):
                    line += f" | Previous Close: {fd['prev_close']}"
                if fd.get("day_high") and fd.get("day_low"):
                    line += f" | Day Range: {fd['day_low']}-{fd['day_high']}"
                if fd.get("fifty_two_week_low") and fd.get("fifty_two_week_high"):
                    line += f" | 52-Week Range: {fd['fifty_two_week_low']}-{fd['fifty_two_week_high']}"
                if fd.get("volume"):
                    line += f" | Volume: {fd['volume']:,}"
                fin_parts.append(line)
            fin_parts.append("=== END VERIFIED MARKET DATA ===\n")
            financial_context = "\n".join(fin_parts)

        # Check graph cache first
        cached_graph = await get_cached_graph(topic, prediction_query)
        if cached_graph:
            logger.info(f"[Cache] Graph cache hit for topic: {topic}")
            # Still need intel brief from orchestrator, but skip graph extraction
            call_fns = {"premium": call_claude_premium, "fast": call_claude_fast, "flash": call_gemini_flash}
            state = await orchestrator.run_live_intel_pipeline(
                session_id, topic, horizon, prediction_query,
                web_context, yahoo_headlines, financial_context,
                financial_data, call_fns, db
            )
            intel_brief = state["intel_brief"]
            graph = cached_graph
        else:
            # Run orchestrator Intel + Graph pipeline
            call_fns = {"premium": call_claude_premium, "fast": call_claude_fast, "flash": call_gemini_flash}
            state = await orchestrator.run_live_intel_pipeline(
                session_id, topic, horizon, prediction_query,
                web_context, yahoo_headlines, financial_context,
                financial_data, call_fns, db
            )
            intel_brief = state["intel_brief"]
            graph = state["graph"]
            await save_graph_cache(topic, prediction_query, graph)

        await db.sessions.update_one(
            {"id": session_id},
            {
                "$set": {
                    "status": "graph_ready",
                    "data_mode": "live",
                    "topic": topic,
                    "prediction_query": prediction_query,
                    "graph_json": json.dumps(graph),
                    "intel_brief": json.dumps(intel_brief),
                    "fetched_at": web_data["fetched_at"],
                    "live_fetch_status": "completed",
                    "live_progress": "Complete!",
                    "brief_critique": json.dumps(state.get("brief_critique", {})),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        logger.info(f"Live fetch completed for session {session_id}: {len(graph.get('entities', []))} entities")

    except Exception as e:
        logger.error(f"Live fetch failed for session {session_id}: {e}")
        await db.sessions.update_one(
            {"id": session_id},
            {
                "$set": {
                    "live_fetch_status": "failed",
                    "live_fetch_error": str(e)[:200],
                    "live_progress": "Failed",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )


@api_router.post("/sessions/{session_id}/fetch-live")
async def fetch_live_data(session_id: str, request: FetchLiveRequest):
    """Kick off live web data fetching as a background task (returns 202 immediately)"""
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    topic = request.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty")
    horizon = request.horizon
    prediction_query = request.prediction_query or f"What will happen with {topic} in the {horizon.lower()}?"
    
    # Mark as fetching
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {
            "live_fetch_status": "fetching",
            "live_fetch_error": None,
            "live_progress": "Starting...",
            "live_progress_step": 0,
            "live_progress_total": 8,
            "topic": topic,
            "data_mode": "live",
        }}
    )
    
    asyncio.create_task(run_live_fetch(session_id, topic, horizon, prediction_query))
    return JSONResponse(status_code=202, content={"status": "fetching", "message": "Live intelligence fetch started"})


@api_router.get("/sessions/{session_id}/live-status")
async def get_live_status(session_id: str):
    """Poll live intelligence fetch status and progress"""
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    status = session.get("live_fetch_status", "idle")
    result = {
        "status": status,
        "progress": session.get("live_progress", ""),
        "progress_step": session.get("live_progress_step", 0),
        "progress_total": session.get("live_progress_total", 8),
    }
    
    if status == "completed":
        graph = json.loads(session["graph_json"]) if session.get("graph_json") else None
        intel_brief = json.loads(session["intel_brief"]) if session.get("intel_brief") else None
        result.update({
            "graph": graph,
            "intel_brief": intel_brief,
            "sources_count": len(intel_brief.get("entities", [])) if intel_brief else 0,
            "fetched_at": session.get("fetched_at"),
        })
    elif status == "failed":
        result["error"] = session.get("live_fetch_error", "Unknown error")
    
    return result


@api_router.post("/sessions/{session_id}/refresh-intel")
async def refresh_intel(session_id: str):
    """Refresh live intelligence data for an existing session"""
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("data_mode") != "live":
        raise HTTPException(status_code=400, detail="Session is not in Live Intelligence mode")
    
    topic = session.get("topic")
    if not topic:
        raise HTTPException(status_code=400, detail="No topic found in session")
    
    horizon = session.get("horizon", "Next month")
    prediction_query = session.get("prediction_query", "")
    
    # Mark as fetching and kick off background task
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {"live_fetch_status": "fetching", "live_fetch_error": None, "live_progress": "Refreshing..."}}
    )
    asyncio.create_task(run_live_fetch(session_id, topic, horizon, prediction_query))
    return JSONResponse(status_code=202, content={"status": "fetching", "message": "Refresh started"})


@api_router.post("/sessions/{session_id}/inject-variable")
async def inject_variable(session_id: str, request: InjectVariableRequest):
    """Inject a new variable/event mid-simulation and run additional rounds"""
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("status") not in ["simulation_done", "complete"]:
        raise HTTPException(status_code=400, detail="Simulation must be complete before injecting variables")
    
    agents = json.loads(session["agents_json"])
    graph = json.loads(session["graph_json"])
    query = session["prediction_query"]
    variable = request.variable
    num_rounds = request.num_new_rounds
    
    # Get current max round
    max_round_doc = await db.sim_posts.find_one(
        {"session_id": session_id},
        sort=[("round", -1)]
    )
    start_round = (max_round_doc["round"] if max_round_doc else 0) + 1
    
    # Update session status
    await db.sessions.update_one(
        {"id": session_id},
        {
            "$set": {
                "status": "simulating",
                "injected_variable": variable,
                "current_round": start_round,
                "total_rounds": start_round + num_rounds - 1,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Run additional rounds with the new variable
    for round_num in range(start_round, start_round + num_rounds):
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {"current_round": round_num}}
        )
        
        # Select agents to respond
        active_agents = random.sample(agents, k=max(3, int(len(agents) * random.uniform(0.6, 0.8))))
        
        # Get recent posts for context
        recent_posts = await db.sim_posts.find(
            {"session_id": session_id}
        ).sort("_id", -1).limit(10).to_list(10)
        
        recent_context = "\n".join([
            f"{p['platform']}: {p['agent_name']}: {p['content']}"
            for p in reversed(recent_posts)
        ]) if recent_posts else ""
        
        for agent in active_agents:
            platform = agent.get("platform_preference", random.choice(["Twitter", "Reddit"]))
            
            system_prompt = f"""You are playing the role of {agent['name']}. A NEW DEVELOPMENT has just occurred: "{variable}". React to this breaking news while staying in character."""
            
            platform_instruction = "Keep under 280 characters." if platform == "Twitter" else "Write 2-4 sentences."
            
            user_prompt = f"""You are: {agent['name']} ({agent['occupation']})
Personality: {agent['personality_type']}
Your previous stance: {agent['initial_stance']}
Topic: {query}

BREAKING NEWS: {variable}

Recent discussion:
{recent_context}

Platform: {platform}
{platform_instruction}

React to this new development as {agent['name']}. Output ONLY your post."""

            try:
                response = await call_gemini_flash(system_prompt, user_prompt, max_tokens=200)
                content = response.strip()
                
                post = {
                    "session_id": session_id,
                    "round": round_num,
                    "agent_id": agent["id"],
                    "agent_name": agent["name"],
                    "agent_emoji": agent.get("avatar_emoji", "🧑"),
                    "platform": platform,
                    "content": content,
                    "post_type": "reaction",
                    "injected_variable": variable,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.sim_posts.insert_one(post)
                
            except Exception as e:
                logger.error(f"Error generating reaction for {agent['name']}: {e}")
                continue
            
            await asyncio.sleep(0.5)
    
    # Update session status
    await db.sessions.update_one(
        {"id": session_id},
        {
            "$set": {
                "status": "simulation_done",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Get updated post count
    post_count = await db.sim_posts.count_documents({"session_id": session_id})
    
    return {
        "status": "simulation_done",
        "injected_variable": variable,
        "new_rounds": num_rounds,
        "total_posts": post_count
    }


@api_router.get("/prediction-horizons")
async def get_prediction_horizons():
    """Get available prediction horizons"""
    return {"horizons": PREDICTION_HORIZONS}


async def run_agent_generation(session_id: str, num_agents: int):
    """Background task: orchestrator runs Persona Agent pipeline with caching."""
    from services.agents import orchestrator
    try:
        session = await db.sessions.find_one({"id": session_id})
        if not session:
            return

        # Check agent cache
        graph_hash = hashlib.md5(session.get("graph_json", "").encode()).hexdigest()
        cached_agents = await get_cached_agents(graph_hash, num_agents)

        if cached_agents:
            logger.info(f"[Cache] Agent cache hit: {len(cached_agents)} agents")
            agents = cached_agents
            # Enrich with templates
            for agent in agents:
                ptype = agent.get("personality_type", "Neutral")
                template = PERSONALITY_TEMPLATES.get(ptype, PERSONALITY_TEMPLATES["Neutral"])
                agent.setdefault("communication_style", template["style"])
                agent.setdefault("platform_preference", template["platform"])
                agent.setdefault("memories", [])
            diversity_score = 0.7
        else:
            call_fns = {"premium": call_claude_premium, "fast": call_claude_fast, "flash": call_gemini_flash}
            result = await orchestrator.run_agent_generation_pipeline(
                session_id, num_agents, call_fns, db
            )
            if not result:
                return

            agents = result["agents"]
            diversity_score = result["diversity_score"]

            # Enrich with personality templates (Change 7)
            for agent in agents:
                ptype = agent.get("personality_type", "Neutral")
                template = PERSONALITY_TEMPLATES.get(ptype, PERSONALITY_TEMPLATES["Neutral"])
                agent.setdefault("communication_style", template["style"])
                agent.setdefault("platform_preference", template["platform"])
                agent.setdefault("memories", [])

            await save_agent_cache(graph_hash, num_agents, agents)

        await db.sessions.update_one(
            {"id": session_id},
            {
                "$set": {
                    "status": "agents_ready",
                    "agents_json": json.dumps(agents),
                    "agent_gen_status": "completed",
                    "diversity_score": diversity_score,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        logger.info(f"Agent generation completed: {len(agents)} agents, diversity={diversity_score}")

    except Exception as e:
        logger.error(f"Agent generation failed for session {session_id}: {e}")
        await db.sessions.update_one(
            {"id": session_id},
            {
                "$set": {
                    "agent_gen_status": "failed",
                    "agent_gen_error": str(e)[:200],
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )


@api_router.post("/sessions/{session_id}/generate-agents")
async def generate_agents(session_id: str, request: GenerateAgentsRequest):
    """Kick off agent generation as a background task"""
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("status") not in ["graph_ready", "agents_ready"]:
        raise HTTPException(status_code=400, detail="Knowledge graph not ready")
    
    # Mark as generating
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {"agent_gen_status": "generating", "agent_gen_error": None}}
    )
    
    asyncio.create_task(run_agent_generation(session_id, request.num_agents))
    return {"status": "generating", "message": "Agent generation started"}


@api_router.get("/sessions/{session_id}/agent-status")
async def get_agent_status(session_id: str):
    """Poll agent generation status"""
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    status = session.get("agent_gen_status", "idle")
    
    if status == "completed" and session.get("agents_json"):
        agents = json.loads(session["agents_json"])
        return {"status": "completed", "agents": agents, "count": len(agents)}
    elif status == "failed":
        return {"status": "failed", "error": session.get("agent_gen_error", "Unknown error")}
    else:
        return {"status": status}


@api_router.post("/sessions/{session_id}/configure-population")
async def configure_population(session_id: str, request: ConfigurePopulationRequest):
    """Configure three-tier population scaling for a session."""
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("status") not in ["agents_ready", "graph_ready"]:
        raise HTTPException(status_code=400, detail="Agents must be generated first")

    tier1 = request.tier1_agents
    multiplier = request.clone_multiplier
    silent = request.silent_population
    tier2 = tier1 * multiplier
    total = tier1 + tier2 + silent
    llm_calls = math.ceil(tier1 / 10)

    # Generate clones if agents exist
    agents = json.loads(session["agents_json"]) if session.get("agents_json") else []
    topic = session.get("topic", session.get("prediction_query", ""))

    clones = generate_clones(agents[:tier1], multiplier) if agents else []
    silent_pop = generate_silent_population(silent, topic) if silent > 0 else {"total": 0, "segments": []}

    tier_breakdown = {"tier1": min(tier1, len(agents)), "tier2": len(clones), "tier3": silent_pop.get("total", 0)}

    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {
            "population_config": {
                "tier1_agents": tier1,
                "clone_multiplier": multiplier,
                "silent_population": silent,
            },
            "clones_json": json.dumps(clones),
            "silent_population": silent_pop,
            "population_size": total,
            "tier_breakdown": tier_breakdown,
        }}
    )

    return {
        "total_simulated": total,
        "tier_breakdown": tier_breakdown,
        "llm_calls_per_round": llm_calls,
        "estimated_time_per_round": f"~{max(15, llm_calls * 8)} seconds",
        "cost_equivalent": f"same as {tier1}-agent simulation",
        "demographics": silent_pop.get("demographics", "global"),
        "demographic_segments": len(silent_pop.get("segments", [])),
    }


async def run_simulation(session_id: str, num_rounds: int):
    try:
        session = await db.sessions.find_one({"id": session_id})
        if not session:
            return

        agents = json.loads(session["agents_json"])
        graph = json.loads(session["graph_json"])
        query = session["prediction_query"]

        # Initialise AI enhancements
        agents = assign_network_properties(agents, seed=42)
        agents = initialise_beliefs(agents)
        agents = initialise_emotions(agents)
        network_stats = get_network_stats(agents)
        hub_ids = set(network_stats.get("hub_ids", []))

        # Load population tiers
        clones = json.loads(session["clones_json"]) if session.get("clones_json") else []
        silent_pop = session.get("silent_population", {"total": 0, "segments": []})
        tier_breakdown = session.get("tier_breakdown", {"tier1": len(agents), "tier2": len(clones), "tier3": silent_pop.get("total", 0)})
        total_pop = tier_breakdown.get("tier1", 0) + tier_breakdown.get("tier2", 0) + tier_breakdown.get("tier3", 0)

        logger.info(f"[Sim] {session_id[:8]} — T1:{len(agents)} T2:{len(clones)} T3:{silent_pop.get('total',0)} hubs:{network_stats['hub_count']}")

        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {"current_round": 0, "total_rounds": num_rounds,
                      "network_stats": network_stats,
                      "population_size": total_pop or len(agents),
                      "tier_breakdown": tier_breakdown}}
        )

        all_posts = []
        round_narratives = []
        BATCH_SIZE = 10
        compressed_context = None

        for round_num in range(1, num_rounds + 1):
            await db.sessions.update_one(
                {"id": session_id},
                {"$set": {"current_round": round_num}}
            )

            # Change 4: Compress context after round 1
            if round_num == 2 and not compressed_context:
                try:
                    compressed_context = await call_gemini_flash(
                        "Summarise in 15 words max. Be specific with key facts/numbers.",
                        f"Summarise: {graph.get('summary', '')}"
                    )
                    compressed_context = compressed_context.strip()
                except Exception:
                    compressed_context = graph.get('summary', '')[:100]

            world_context = compressed_context if (round_num > 1 and compressed_context) else graph.get('summary', '')

            hub_agents = [a for a in agents if a["id"] in hub_ids]
            non_hub = [a for a in agents if a["id"] not in hub_ids]
            active_non_hub = random.sample(non_hub, k=max(3, int(len(non_hub)*random.uniform(0.55,0.75))))
            active_agents = hub_agents + active_non_hub

            # Use feed algorithm with compressed context
            if all_posts and active_agents:
                sample_agent = active_agents[0]
                feed_posts = get_agent_feed(sample_agent, all_posts, round_num)
                recent_context = "\n".join([
                    f"{p['agent_name'][:12]}: {p['content'][:55]}"
                    for p in (feed_posts or all_posts[-6:])
                ]) if feed_posts else "No previous posts yet."
            else:
                recent_context = "\n".join([
                    f"{p['agent_name'][:12]}: {p['content'][:55]}"
                    for p in all_posts[-6:]
                ]) if all_posts else "No previous posts yet."

            director_context = f"\nPrevious round summary: {round_narratives[-1]}" if round_narratives else ""

            emo_temp = get_emotional_temperature(agents)
            emotional_context = (
                f"\nCurrent crowd mood: {emo_temp['state']} (valence: {emo_temp['mean_valence']:+.2f})"
                if emo_temp["state"] != "calm" else ""
            )

            # Batch post generation
            round_posts = []
            batches = [active_agents[i:i+BATCH_SIZE] for i in range(0, len(active_agents), BATCH_SIZE)]

            for batch in batches:
                agents_desc = "\n".join([
                    f"Agent {i+1}: {a['name']} | {a['occupation']} | "
                    f"{a['personality_type']} | Platform: {a['platform_preference']} | "
                    f"Stance: {a['initial_stance'][:50]} | "
                    f"{'Background: ' + a.get('background','')[:40] + ' | ' if round_num == 1 else ''}"
                    f"Feeling: {get_emotion_label(a.get('emotional_state',{}).get('valence',0.0))}"
                    for i, a in enumerate(batch)
                ])

                system_prompt = (
                    "You are simulating diverse social media users. Write ONE authentic post per agent "
                    "in their unique voice. Stay in character. "
                    "Return ONLY a valid JSON array, no other text, no markdown."
                )
                user_prompt = f"""World context: {world_context[:1500]}
Prediction question: {query}
Round: {round_num}/{num_rounds}{director_context}{emotional_context}

Recent posts:
{recent_context}

Write ONE post for EACH agent. Twitter: under 200 chars. Reddit: 2-4 sentences.

{agents_desc}

Return JSON array ONLY:
[
  {{"agent_index": 1, "content": "post text"}},
  {{"agent_index": 2, "content": "post text"}}
]"""

                try:
                    response = await call_gemini_flash(system_prompt, user_prompt, max_tokens=600)
                    cleaned = clean_json_response(response)
                    posts_data = json.loads(cleaned)

                    for item in posts_data:
                        idx = item.get("agent_index", 1) - 1
                        if 0 <= idx < len(batch):
                            agent = batch[idx]
                            content = item.get("content", "").strip()
                            if not content:
                                continue
                            if agent.get("platform_preference") == "Twitter" and len(content) > 300:
                                content = content[:280].rsplit(" ", 1)[0] + "..."

                            post = {
                                "session_id": session_id,
                                "round": round_num,
                                "agent_id": agent["id"],
                                "agent_name": agent["name"],
                                "agent_emoji": agent.get("avatar_emoji", ""),
                                "platform": agent.get("platform_preference", "Twitter"),
                                "content": content,
                                "post_type": "post",
                                "is_hub_post": agent["id"] in hub_ids,
                                "influence_level": agent.get("influence_level", 5),
                                "belief_position": agent.get("belief_state", {}).get("position", 0.0),
                                "emotional_valence": agent.get("emotional_state", {}).get("valence", 0.0),
                                "created_at": datetime.now(timezone.utc).isoformat()
                            }
                            await db.sim_posts.insert_one(post)
                            all_posts.append(post)
                            round_posts.append(post)
                            agent["memories"] = agent.get("memories", [])[-9:] + \
                                               [f"Round {round_num}: I posted: {content[:80]}"]
                except Exception as e:
                    logger.error(f"[Sim] Batch error round {round_num}: {e}")
                    continue

                await asyncio.sleep(1.0)

            # Generate replies (batched — ONE call for all replies)
            if round_posts and len(active_agents) >= 2 and round_num >= 2:
                n_replies = min(3, len(round_posts))
                reply_agents = random.sample(active_agents, min(n_replies, len(active_agents)))
                target_posts = random.sample(round_posts, min(n_replies, len(round_posts)))

                # Filter out self-replies and build batch
                reply_pairs = [(a, t) for a, t in zip(reply_agents, target_posts) if t["agent_id"] != a["id"]]

                if reply_pairs:
                    agents_desc = "\n".join([
                        f"Agent {i+1}: {a['name']} ({a['occupation']}, {a['personality_type']}) replying to {t['agent_name']}: \"{t['content'][:80]}\""
                        for i, (a, t) in enumerate(reply_pairs)
                    ])
                    system_prompt = "You are simulating social media users replying to posts. Write brief in-character replies. Return ONLY a valid JSON array."
                    user_prompt = f"""Write a short 1-sentence reply for each agent below.

{agents_desc}

Return JSON array ONLY:
[{{"agent_index": 1, "content": "reply text"}}, ...]"""

                    try:
                        response = await call_gemini_flash(system_prompt, user_prompt, max_tokens=200)
                        cleaned = clean_json_response(response)
                        replies_data = json.loads(cleaned)

                        for item in replies_data:
                            idx = item.get("agent_index", 1) - 1
                            if 0 <= idx < len(reply_pairs):
                                agent, target_post = reply_pairs[idx]
                                reply_content = item.get("content", "").strip()
                                if not reply_content:
                                    continue
                                reply = {
                                    "session_id": session_id,
                                    "round": round_num,
                                    "agent_id": agent["id"],
                                    "agent_name": agent["name"],
                                    "agent_emoji": agent.get("avatar_emoji", ""),
                                    "platform": target_post["platform"],
                                    "content": reply_content,
                                    "post_type": "reply",
                                    "reply_to": target_post["agent_name"],
                                    "is_hub_post": agent["id"] in hub_ids,
                                    "influence_level": agent.get("influence_level", 5),
                                    "belief_position": agent.get("belief_state", {}).get("position", 0.0),
                                    "emotional_valence": agent.get("emotional_state", {}).get("valence", 0.0),
                                    "created_at": datetime.now(timezone.utc).isoformat()
                                }
                                await db.sim_posts.insert_one(reply)
                                all_posts.append(reply)
                                round_posts.append(reply)
                    except Exception as e:
                        logger.error(f"[Sim] Batched reply error: {e}")

            # Tier 2: Generate clone echo posts
            if clones:
                parent_posts_map = {}
                for p in round_posts:
                    pid = p.get("agent_id", "")
                    if pid not in parent_posts_map:
                        parent_posts_map[pid] = []
                    parent_posts_map[pid].append(p)

                echo_posts = generate_clone_posts(clones, parent_posts_map, round_num)
                echo_count = len(echo_posts)
                for ep in echo_posts:
                    ep["session_id"] = session_id
                    ep["created_at"] = datetime.now(timezone.utc).isoformat()
                if echo_posts:
                    await db.sim_posts.insert_many(echo_posts)
                    all_posts.extend(echo_posts)
                    round_posts.extend(echo_posts)
                logger.info(f"[Sim] Round {round_num}: {echo_count} clone echoes")

            # Tier 3: Calculate silent population reactions
            tier1_reactions = {}
            if silent_pop.get("total", 0) > 0 and round_posts:
                tier1_reactions = calculate_silent_reactions(round_posts, silent_pop, round_num)
                # Update posts in DB with reaction data
                for post in round_posts:
                    key = post.get("agent_id", "") + "_" + str(post.get("round", 0))
                    rxn = tier1_reactions.get(key, {})
                    if rxn:
                        echo_count_for_post = sum(1 for ep in echo_posts if ep.get("parent_id") == post.get("agent_id")) if clones else 0
                        await db.sim_posts.update_one(
                            {"session_id": session_id, "agent_id": post["agent_id"], "round": round_num,
                             "content": post["content"]},
                            {"$set": {
                                "tier1_reactions": {"likes": rxn.get("likes", 0), "shares": rxn.get("shares", 0), "hostile": rxn.get("hostile", 0)},
                                "tier2_echo_count": echo_count_for_post,
                                "reach_score": rxn.get("reach_score", 0.0),
                                "viral": rxn.get("viral", False),
                            }},
                        )
                        # Update in-memory post for feed algorithm
                        post["tier1_reactions"] = rxn
                        post["reach_score"] = rxn.get("reach_score", 0.0)
                        post["viral"] = rxn.get("viral", False)

            # Update AI state
            agents = update_beliefs(agents, round_posts, round_num)
            agents = spread_emotions(agents, round_posts, round_num)

            # Critic herd check
            herd_check = check_herd(round_posts)
            if herd_check["herd_detected"] and round_num < num_rounds:
                logger.info(f"[Critic] Herd detected R{round_num}: {herd_check['dominant_sentiment']} at {herd_check['herd_score']:.0%}")
                round_narratives.append(
                    f"BREAKING: A prominent contrarian voice challenged the "
                    f"{herd_check['dominant_sentiment']} consensus — some agents reconsidering."
                )
            elif round_posts and round_num >= 3 and round_num < num_rounds:
                try:
                    sample_posts = "\n".join([f"{p['agent_name']}: {p['content'][:100]}" for p in round_posts[:6]])
                    emo_temp2 = get_emotional_temperature(agents)
                    belief_sum = get_belief_summary(agents)
                    narrative = await call_gemini_flash(
                        "You are a simulation narrator. Write concise 1-2 sentence round summaries.",
                        f"Round {round_num}/{num_rounds} on: {query}\nPosts:\n{sample_posts}\n"
                        f"Emotion: {emo_temp2['state']} | Support: {belief_sum['support']}% | "
                        f"Opposition: {belief_sum['opposition']}%\nSummarise what happened and what's shifting.",
                        max_tokens=80
                    )
                    round_narratives.append(narrative.strip())
                except Exception as e:
                    logger.error(f"[Sim] Narrative error: {e}")

            logger.info(f"[Sim] Round {round_num} — {len(round_posts)} posts, mood: {get_emotional_temperature(agents)['state']}")

        # Save final state
        belief_summary = get_belief_summary(agents)
        emotional_final = get_emotional_temperature(agents)

        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {
                "status": "simulation_done",
                "agents_json": json.dumps(agents),
                "round_narratives": round_narratives,
                "belief_summary": belief_summary,
                "emotional_summary": emotional_final,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )

    except Exception as e:
        logger.error(f"[Sim] Fatal error {session_id}: {e}")
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {"status": "error", "error_message": str(e)}}
        )


@api_router.post("/sessions/{session_id}/simulate")
async def start_simulation(session_id: str, request: SimulateRequest, background_tasks: BackgroundTasks):
    """Start the multi-round social media simulation"""
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("status") not in ["agents_ready", "simulation_done"]:
        raise HTTPException(status_code=400, detail="Agents not ready")
    
    # Clear previous simulation posts if re-running
    await db.sim_posts.delete_many({"session_id": session_id})
    
    # Update status
    await db.sessions.update_one(
        {"id": session_id},
        {
            "$set": {
                "status": "simulating",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Start background task
    background_tasks.add_task(run_simulation, session_id, request.num_rounds)
    
    return {"status": "simulating"}


@api_router.post("/sessions/{session_id}/extend")
async def extend_simulation(
    session_id: str,
    request: ExtendSimulationRequest,
    background_tasks: BackgroundTasks
):
    """Add more rounds to a completed simulation — skips graph/agent regeneration."""
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("status") not in ["simulation_done", "complete"]:
        raise HTTPException(status_code=400, detail="Simulation must be complete to extend")

    current_rounds = session.get("total_rounds", 0)
    new_total = current_rounds + request.additional_rounds

    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {
            "status": "simulating",
            "total_rounds": new_total,
            "report_json": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    background_tasks.add_task(
        run_simulation, session_id, request.additional_rounds
    )
    return {
        "status": "extending",
        "previous_rounds": current_rounds,
        "additional_rounds": request.additional_rounds,
        "total_rounds": new_total
    }


@api_router.get("/sessions/{session_id}/simulation-status")
async def get_simulation_status(session_id: str):
    """Get current simulation status"""
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    post_count = await db.sim_posts.count_documents({"session_id": session_id})
    
    return {
        "status": session.get("status"),
        "post_count": post_count,
        "current_round": session.get("current_round", 0),
        "total_rounds": session.get("total_rounds", 0),
        "belief_summary": session.get("belief_summary"),
        "emotional_summary": session.get("emotional_summary"),
        "network_stats": session.get("network_stats"),
        "round_narratives": session.get("round_narratives", []),
        "population_size": session.get("population_size", 0),
        "tier_breakdown": session.get("tier_breakdown"),
    }


@api_router.get("/sessions/{session_id}/posts")
async def get_posts(session_id: str):
    """Get all simulation posts"""
    posts = await db.sim_posts.find(
        {"session_id": session_id},
        {"_id": 0}
    ).sort([("round", 1), ("created_at", 1)]).to_list(1000)
    
    return {"posts": posts}


async def run_background_critic(session_id: str, report: dict):
    """Runs 30 seconds after report generation — non-blocking."""
    await asyncio.sleep(30)
    try:
        from agents import check_report as agents_check_report
        result = await agents_check_report(report, call_claude_fast)
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {"quality_score": result.get("quality_score", 6),
                      "quality_feedback": result}}
        )
        logger.info(f"[Critic] Background check done for {session_id[:8]}: score={result.get('quality_score')}")
    except Exception as e:
        logger.error(f"[Critic] Background check failed: {e}")


@api_router.post("/sessions/{session_id}/generate-report")
async def generate_report(session_id: str):
    """Progressive 2-phase report: Phase 1 (Haiku, fast core) + Phase 2 (Sonnet, deep analysis)."""
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("status") not in ["simulation_done", "complete"]:
        raise HTTPException(status_code=400, detail="Simulation not complete")

    agents = json.loads(session["agents_json"])
    graph = json.loads(session["graph_json"])
    query = session["prediction_query"]

    posts = await db.sim_posts.find(
        {"session_id": session_id}
    ).sort([("round", 1)]).to_list(1000)

    # Build transcript (capped)
    lines = [f"[R{p['round']}][{p.get('platform','')}] {p['agent_name']}: {p['content'][:80]}"
             for p in posts]
    transcript = "\n".join(lines)
    if len(transcript) > 5000:
        transcript = transcript[:2500] + "\n...\n" + transcript[-2500:]

    agents_summary = "\n".join([
        f"- {a['name']} [{a.get('personality_type','')}]: {a.get('initial_stance','')[:60]}"
        for a in agents[:20]
    ])

    # PHASE 1 — fast core report (Haiku, small)
    phase1_system = "You are a prediction analyst. Return ONLY valid JSON, no markdown."
    phase1_prompt = f"""Prediction: {query}
Context: {graph.get('summary','')}
Agents ({len(agents)}):
{agents_summary}
Simulation ({session.get('total_rounds',3)} rounds):
{transcript}

Return JSON with ONLY these fields:
{{
  "executive_summary": "3 sentences",
  "prediction": {{
    "outcome": "one sentence",
    "confidence": "High|Medium|Low",
    "confidence_score": 0.65,
    "timeframe": "e.g. next month"
  }},
  "opinion_landscape": {{
    "dominant_sentiment": "positive|negative|divided|uncertain",
    "support_percentage": 45,
    "opposition_percentage": 38,
    "undecided_percentage": 17
  }}
}}"""

    try:
        r1 = await call_claude_fast(phase1_system, phase1_prompt, max_tokens=500)
        phase1 = json.loads(clean_json_response(r1))
    except Exception as e:
        logger.error(f"Report phase 1 failed: {e}")
        raise HTTPException(status_code=500, detail=f"Report phase 1 failed: {str(e)}")

    # PHASE 2 — deep analysis (Sonnet, medium)
    phase2_system = "You are a senior analyst. Return ONLY valid JSON, no markdown."
    phase2_prompt = f"""Prediction: {query}
Simulation transcript:
{transcript}

Return JSON with ONLY these fields:
{{
  "key_factions": [
    {{"name": "...", "size": "Large|Medium|Small", "stance": "...", "key_arguments": ["..."]}}
  ],
  "key_turning_points": [
    {{"round": 1, "description": "...", "impact": "..."}}
  ],
  "emergent_patterns": ["..."],
  "risk_factors": [
    {{"factor": "...", "likelihood": "High|Medium|Low", "impact": "..."}}
  ],
  "alternative_scenarios": [
    {{"scenario": "...", "probability": 0.2, "conditions": "..."}}
  ],
  "agent_highlights": [
    {{"agent_name": "...", "role_in_simulation": "...", "notable_quote": "..."}}
  ]
}}"""

    try:
        r2 = await call_claude_premium(phase2_system, phase2_prompt, max_tokens=1200)
        phase2 = json.loads(clean_json_response(r2))
    except Exception as e:
        logger.error(f"Report phase 2 failed: {e}")
        phase2 = {}

    # Merge into complete report
    report = {
        **phase1,
        "opinion_landscape": {
            **phase1.get("opinion_landscape", {}),
            "key_factions": phase2.get("key_factions", [])
        }
    }
    report.update({k: v for k, v in phase2.items() if k != "key_factions"})

    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {
            "status": "complete",
            "report_json": json.dumps(report),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )

    # Background critic check — runs 30s later, non-blocking
    asyncio.create_task(run_background_critic(session_id, report))

    return {"report": report}


@api_router.get("/sessions/{session_id}/report")
async def get_report(session_id: str):
    """Get stored prediction report"""
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.get("report_json"):
        raise HTTPException(status_code=404, detail="Report not generated yet")
    
    return json.loads(session["report_json"])


@api_router.get("/sessions/{session_id}/report/pdf")
async def download_report_pdf(session_id: str):
    """Download prediction report as PDF"""
    from fpdf import FPDF
    
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.get("report_json"):
        raise HTTPException(status_code=404, detail="Report not generated yet")
    
    report = json.loads(session["report_json"])
    query = session.get("prediction_query", "N/A")
    
    def safe_text(text, max_len=500):
        """Sanitize text for PDF output - removes Unicode characters not supported by Helvetica"""
        if not text:
            return "N/A"
        text = str(text)
        
        # Replace common Unicode characters with ASCII equivalents
        replacements = {
            '—': '-',  # em-dash
            '–': '-',  # en-dash
            '"': '"',  # left double quote
            '"': '"',  # right double quote
            ''': "'",  # left single quote
            ''': "'",  # right single quote
            '…': '...',  # ellipsis
            '•': '*',  # bullet
            '→': '->',  # arrow
            '←': '<-',
            '↔': '<->',
            '≈': '~',
            '≠': '!=',
            '≤': '<=',
            '≥': '>=',
            '×': 'x',
            '÷': '/',
            '±': '+/-',
            '°': ' degrees',
            '©': '(c)',
            '®': '(R)',
            '™': '(TM)',
            '\u00a0': ' ',  # non-breaking space
        }
        for unicode_char, ascii_char in replacements.items():
            text = text.replace(unicode_char, ascii_char)
        
        # Remove newlines and tabs
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # Keep only ASCII printable characters
        text = ''.join(c if (ord(c) < 128 and c.isprintable()) or c == ' ' else '' for c in text)
        
        # Clean up multiple spaces
        while '  ' in text:
            text = text.replace('  ', ' ')
        
        if len(text) > max_len:
            text = text[:max_len] + "..."
        return text.strip() or "N/A"
    
    # Create PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Title
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(30, 64, 175)  # Blue
    pdf.cell(0, 15, "SwarmSim Prediction Report", ln=True, align="C")
    pdf.ln(5)
    
    # Prediction Question
    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(190, 6, f"Question: {safe_text(query, 300)}")
    pdf.ln(5)
    
    # Generated Date
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}", ln=True)
    pdf.ln(10)
    
    # Prediction Outcome Box
    pdf.set_fill_color(240, 249, 255)  # Light blue background
    pdf.set_draw_color(59, 130, 246)  # Blue border
    pdf.rect(10, pdf.get_y(), 190, 35, style="DF")
    
    pdf.set_xy(15, pdf.get_y() + 5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 64, 175)
    pdf.cell(0, 8, "PREDICTED OUTCOME", ln=True)
    
    pdf.set_x(15)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    outcome = safe_text(report.get("prediction", {}).get("outcome", "N/A"), 300)
    pdf.multi_cell(180, 6, outcome)
    
    pdf.ln(15)
    
    # Confidence Score
    prediction = report.get("prediction", {})
    confidence = prediction.get("confidence", "N/A")
    score = prediction.get("confidence_score", 0) or 0
    timeframe = safe_text(prediction.get("timeframe", "N/A"), 50)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(60, 8, f"Confidence: {confidence} ({int(score * 100)}%)")
    pdf.cell(60, 8, f"Timeframe: {timeframe}", ln=True)
    pdf.ln(8)
    
    # Executive Summary
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 64, 175)
    pdf.cell(0, 10, "Executive Summary", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    summary = safe_text(report.get("executive_summary", "N/A"), 800)
    pdf.multi_cell(190, 6, summary)
    pdf.ln(8)
    
    # Opinion Landscape
    opinion = report.get("opinion_landscape", {})
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 64, 175)
    pdf.cell(0, 10, "Opinion Landscape", ln=True)
    
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    support = opinion.get("support_percentage", 0) or 0
    opposition = opinion.get("opposition_percentage", 0) or 0
    undecided = opinion.get("undecided_percentage", 0) or 0
    sentiment = safe_text(opinion.get("dominant_sentiment", "N/A"), 50)
    
    pdf.cell(0, 6, f"Dominant Sentiment: {sentiment.title()}", ln=True)
    pdf.cell(60, 6, f"Support: {support}%")
    pdf.cell(60, 6, f"Opposition: {opposition}%")
    pdf.cell(60, 6, f"Undecided: {undecided}%", ln=True)
    pdf.ln(5)
    
    # Key Factions
    factions = opinion.get("key_factions", [])
    if factions:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Key Factions:", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for faction in factions:
            name = safe_text(faction.get('name', 'N/A'), 50)
            size = safe_text(faction.get('size', 'N/A'), 20)
            stance = safe_text(faction.get('stance', 'N/A'), 200)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"- {name} ({size})", ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(190, 5, f"  {stance}")
    pdf.ln(5)
    
    # Risk Factors
    risks = report.get("risk_factors", [])
    if risks:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(220, 38, 38)  # Red
        pdf.cell(0, 10, "Risk Factors", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        for risk in risks:
            likelihood = safe_text(risk.get("likelihood", "N/A"), 20)
            factor = safe_text(risk.get("factor", "N/A"), 100)
            impact = safe_text(risk.get("impact", "N/A"), 200)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"[{likelihood}] {factor}", ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(190, 5, f"  Impact: {impact}")
        pdf.ln(5)
    
    # Key Turning Points
    turning_points = report.get("key_turning_points", [])
    if turning_points:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(30, 64, 175)
        pdf.cell(0, 10, "Key Turning Points", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        for point in turning_points:
            round_num = point.get('round', 'N/A')
            description = safe_text(point.get('description', 'N/A'), 150)
            impact = safe_text(point.get('impact', 'N/A'), 200)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"Round {round_num}: {description}", ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(190, 5, f"  Impact: {impact}")
        pdf.ln(5)
    
    # Alternative Scenarios
    scenarios = report.get("alternative_scenarios", [])
    if scenarios:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(30, 64, 175)
        pdf.cell(0, 10, "Alternative Scenarios", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        for scenario in scenarios:
            prob = scenario.get("probability", 0) or 0
            scenario_name = safe_text(scenario.get('scenario', 'N/A'), 100)
            conditions = safe_text(scenario.get('conditions', 'N/A'), 200)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"{scenario_name} ({int(prob * 100)}% probability)", ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(190, 5, f"  Conditions: {conditions}")
        pdf.ln(5)
    
    # Agent Highlights
    highlights = report.get("agent_highlights", [])
    if highlights:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(30, 64, 175)
        pdf.cell(0, 10, "Agent Highlights", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        for highlight in highlights:
            pdf.set_font("Helvetica", "B", 10)
            name = safe_text(highlight.get('agent_name', 'N/A'), 50)
            pdf.cell(0, 6, f"- {name}", ln=True)
            pdf.set_font("Helvetica", "", 10)
            role = safe_text(highlight.get('role_in_simulation', 'N/A'), 200)
            pdf.multi_cell(190, 5, f"Role: {role}")
            quote = safe_text(highlight.get("notable_quote", ""), 150)
            if quote and quote != "N/A":
                pdf.set_font("Helvetica", "I", 10)
                pdf.multi_cell(190, 5, f'"{quote}"')
                pdf.set_font("Helvetica", "", 10)
            pdf.ln(2)
    
    # Footer
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, "Generated by SwarmSim - Swarm Intelligence Prediction Engine", ln=True, align="C")
    
    # Output PDF to bytes
    pdf_output = io.BytesIO()
    pdf_bytes = pdf.output()
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    
    # Create filename
    filename = f"swarmsim_report_{session_id[:8]}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        pdf_output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@api_router.post("/sessions/{session_id}/chat")
async def chat(session_id: str, request: ChatRequest):
    """Chat with an agent or ReportAgent"""
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    query = session["prediction_query"]
    
    # Get chat history for this target
    history = await db.chat_history.find({
        "session_id": session_id,
        "target_type": request.target_type,
        "target_id": request.target_id
    }).sort("created_at", 1).to_list(20)
    
    # Build conversation context
    conversation = "\n".join([
        f"{'User' if h['role'] == 'user' else 'Assistant'}: {h['content']}"
        for h in history[-6:]  # Last 6 messages for context
    ])
    
    if request.target_type == "agent":
        # Find the agent
        agents = json.loads(session["agents_json"])
        agent = next((a for a in agents if a["id"] == request.target_id), None)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        system_prompt = f"""You are roleplaying as {agent['name']}, a character in a social simulation.
Profile: Age {agent.get('age', 35)}, {agent['occupation']}, {agent['personality_type']}, {agent['communication_style']} communicator.
Background: {agent['background']}
Your stance: {agent['initial_stance']}
Topic: {query}
Stay completely in character. Be opinionated. 2-4 sentences per reply. Do not reveal you are an AI."""
        
    else:  # report agent
        report = json.loads(session.get("report_json", "{}"))
        report_summary = json.dumps(report, indent=2)[:2000]  # Truncate for context
        
        system_prompt = f"""You are the SwarmSim ReportAgent — an expert analyst who completed a multi-agent social simulation.
Prediction Question: {query}
Your findings: {report_summary}
Answer questions about the simulation findings. Be authoritative but acknowledge uncertainty. 3-5 sentences."""
    
    user_prompt = f"""Previous conversation:
{conversation}

User: {request.message}"""

    try:
        response = await call_claude_fast(system_prompt, user_prompt, max_tokens=200)
        response_text = response.strip()
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")
    
    # Save chat history
    now = datetime.now(timezone.utc).isoformat()
    await db.chat_history.insert_many([
        {
            "session_id": session_id,
            "target_type": request.target_type,
            "target_id": request.target_id,
            "role": "user",
            "content": request.message,
            "created_at": now
        },
        {
            "session_id": session_id,
            "target_type": request.target_type,
            "target_id": request.target_id,
            "role": "assistant",
            "content": response_text,
            "created_at": now
        }
    ])
    
    return {"response": response_text}


@api_router.get("/sessions/{session_id}/chat-history")
async def get_chat_history(session_id: str, target_type: str, target_id: str):
    """Get chat history for a specific target"""
    history = await db.chat_history.find({
        "session_id": session_id,
        "target_type": target_type,
        "target_id": target_id
    }, {"_id": 0}).sort("created_at", 1).to_list(100)
    
    return {"history": history}


# Include router and middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
