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
import urllib.request
import urllib.parse

import base64
import httpx

# xAI/Grok SDK
try:
    from xai_sdk import Client as XAIClient
    from xai_sdk.chat import user as xai_user
    from xai_sdk.tools import x_search as xai_x_search
    from xai_sdk.tools import web_search as xai_web_search
    XAI_AVAILABLE = True
except ImportError:
    XAI_AVAILABLE = False

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
from services.topic import TOPIC_CATEGORIES, detect_topic_category

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

class SocialSeedRequest(BaseModel):
    topic: str
    include_reddit: bool = True
    include_twitter: bool = True
    max_comments: int = Field(default=30, ge=5, le=100)

# Prediction horizons
PREDICTION_HORIZONS = [
    "Next 24 hours",
    "Next week", 
    "Next month",
    "Next 3 months",
    "Next 6 months",
    "Long term (1+ year)"
]

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


def parse_llm_json(text: str, fallback: Any = None, label: str = "LLM JSON") -> Any:
    """Parse JSON from LLM output, including common extra prose around the JSON."""
    cleaned = clean_json_response(text or "")
    candidates = [cleaned]

    first_array, last_array = cleaned.find("["), cleaned.rfind("]")
    if first_array != -1 and last_array > first_array:
        candidates.append(cleaned[first_array:last_array + 1])

    first_obj, last_obj = cleaned.find("{"), cleaned.rfind("}")
    if first_obj != -1 and last_obj > first_obj:
        candidates.append(cleaned[first_obj:last_obj + 1])

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue

    logger.warning("[%s] Could not parse JSON; using fallback", label)
    return fallback


def build_fallback_post(agent: dict, query: str, round_num: int, num_rounds: int) -> str:
    """Create a deterministic in-character post when a bulk LLM batch fails."""
    stance = agent.get("initial_stance", "I am watching for stronger evidence.")
    style = agent.get("personality_type", "Neutral").lower()
    prefix = {
        "skeptic": "I am not convinced yet:",
        "optimist": "There is still upside here:",
        "contrarian": "Counterpoint:",
        "expert": "The signal I would track:",
        "activist": "People should not ignore this:",
        "pragmatist": "Practical read:",
        "insider": "What matters behind the scenes:",
    }.get(style, "My read:")
    content = f"{prefix} {stance[:140]} For {query}, round {round_num}/{num_rounds} still depends on fresh evidence."
    if agent.get("platform_preference") == "Twitter" and len(content) > 260:
        content = content[:257].rsplit(" ", 1)[0] + "..."
    return content


def build_post_document(agent: dict, session_id: str, round_num: int, content: str,
                        hub_ids: set, post_type: str = "post", platform: str = None,
                        reply_to: str = None, fallback: bool = False) -> dict:
    """Normalize simulation post documents across LLM and fallback generation paths."""
    post = {
        "session_id": session_id,
        "round": round_num,
        "agent_id": agent["id"],
        "agent_name": agent["name"],
        "agent_emoji": agent.get("avatar_emoji", ""),
        "platform": platform or agent.get("platform_preference", "Twitter"),
        "content": content,
        "post_type": post_type,
        "is_hub_post": agent["id"] in hub_ids,
        "influence_level": agent.get("influence_level", 5),
        "belief_position": agent.get("belief_state", {}).get("position", 0.0),
        "emotional_valence": agent.get("emotional_state", {}).get("valence", 0.0),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    if reply_to:
        post["reply_to"] = reply_to
    if fallback:
        post["generation_fallback"] = True
    return post


def build_report_quality_metadata(session: dict, posts: list, stock_data: list, report: dict) -> dict:
    """Summarize uncertainty, evidence freshness, and simulation reliability for the report."""
    total_posts = len(posts)
    real_posts = sum(1 for post in posts if post.get("is_real"))
    fallback_posts = sum(1 for post in posts if post.get("generation_fallback"))
    simulated_posts = max(0, total_posts - real_posts)
    fallback_rate = round(fallback_posts / simulated_posts, 3) if simulated_posts else 0.0
    source_count = len(session.get("social_seed_sources", []) or [])
    has_live_intel = bool(session.get("intel_brief"))
    has_real_sentiment = bool(session.get("social_seed_sentiment", {}).get("total_comments_analysed", 0))
    confidence_score = report.get("prediction", {}).get("confidence_score", 0.5) or 0.5

    evidence_score = 0.25
    evidence_score += 0.20 if has_live_intel else 0
    evidence_score += min(0.20, total_posts / 500)
    evidence_score += 0.15 if stock_data else 0
    evidence_score += 0.10 if has_real_sentiment else 0
    evidence_score += min(0.10, source_count * 0.03)
    evidence_score -= min(0.20, fallback_rate * 0.5)
    evidence_score = max(0.05, min(1.0, evidence_score))

    if evidence_score >= 0.75:
        evidence_strength = "strong"
    elif evidence_score >= 0.45:
        evidence_strength = "moderate"
    else:
        evidence_strength = "limited"

    uncertainty = max(0.05, min(0.45, (1 - evidence_score) * 0.35 + fallback_rate * 0.15))
    lower = max(0.0, confidence_score - uncertainty)
    upper = min(1.0, confidence_score + uncertainty)

    caveats = [
        "Scenario simulation output; not a calibrated statistical forecast.",
        "LLM-generated agent behavior may amplify prompt or source framing.",
    ]
    if fallback_posts:
        caveats.append(f"{fallback_posts} simulated posts used deterministic fallbacks after LLM parse failures.")
    if not has_real_sentiment:
        caveats.append("No real social seed sentiment was available for calibration.")
    if not stock_data and detect_topic_category(session.get("topic") or session.get("prediction_query", "")) == "financial":
        caveats.append("No live market data was resolved for this financial topic.")

    latest_inputs = [
        ts for ts in [
            session.get("live_fetched_at"),
            session.get("updated_at"),
        ]
        if ts
    ]
    for item in stock_data or []:
        if item.get("fetched_at"):
            latest_inputs.append(item["fetched_at"])

    return {
        "evidence_strength": evidence_strength,
        "evidence_score": round(evidence_score, 2),
        "confidence_interval": {
            "low": round(lower, 2),
            "high": round(upper, 2),
        },
        "uncertainty": round(uncertainty, 2),
        "data_freshness": {
            "latest_input_at": max(latest_inputs) if latest_inputs else None,
            "live_intel": has_live_intel,
            "market_data_points": len(stock_data or []),
            "real_social_sources": session.get("social_seed_sources", []) or [],
        },
        "simulation_reliability": {
            "total_posts": total_posts,
            "simulated_posts": simulated_posts,
            "real_seed_posts": real_posts,
            "fallback_posts": fallback_posts,
            "fallback_rate": fallback_rate,
        },
        "caveats": caveats,
    }


# ─── Social Media Fetchers ────────────────────────────────────────────
async def fetch_reddit_comments(topic: str, limit: int = 30) -> list:
    """Fetch real social commentary via Google News RSS (uses feedparser, already proven in app)."""
    comments = []
    try:
        import feedparser
        encoded_topic = urllib.parse.quote(topic)
        url = f"https://news.google.com/rss/search?q={encoded_topic}&hl=en&gl=US&ceid=US:en"
        loop = asyncio.get_running_loop()

        def do_parse():
            return feedparser.parse(url)

        feed = await loop.run_in_executor(None, do_parse)

        for entry in feed.entries[:limit]:
            title = entry.get("title", "").strip()
            source = entry.get("source", {}).get("title", "News")
            link = entry.get("link", "")
            summary = entry.get("summary", "")[:200]
            # Clean HTML tags from summary
            summary = re.sub(r'<[^>]+>', '', summary).strip()
            # Remove any remaining HTML entities
            summary = summary.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')

            if title and len(title) > 15:
                # Clean title (feedparser sometimes leaves artifacts)
                title = re.sub(r'<[^>]+>', '', title).strip()
                # Determine if it's Reddit content
                is_reddit = "reddit" in link.lower() or "reddit" in source.lower()
                content = title[:280]
                comments.append({
                    "platform": "Reddit" if is_reddit else "News",
                    "content": content,
                    "score": 0,
                    "subreddit": "news" if not is_reddit else "reddit",
                    "author": source[:30],
                    "url": link
                })
    except Exception as e:
        logger.warning(f"[SocialSeed] Google News RSS fetch failed: {e}")

    return comments[:limit]


async def fetch_twitter_comments(topic: str, limit: int = 20) -> list:
    """Fetch tweets via TwitterAPI.io (optional paid). Falls back gracefully if key not set."""
    api_key = os.environ.get("TWITTER_API_IO_KEY")
    if not api_key:
        logger.info("[Twitter] TWITTER_API_IO_KEY not set — skipping")
        return []

    try:
        encoded_topic = urllib.parse.quote(topic)
        url = f"https://api.twitterapi.io/twitter/tweet/advanced_search?query={encoded_topic}&queryType=Latest&count={limit}"
        req = urllib.request.Request(url, headers={"X-API-Key": api_key, "Content-Type": "application/json"})
        loop = asyncio.get_running_loop()

        def do_request():
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode())

        data = await loop.run_in_executor(None, do_request)
        tweets = data.get("tweets", [])
        comments = []
        for tweet in tweets:
            text = tweet.get("text", "").strip()
            if text and not text.startswith("RT ") and len(text) > 20:
                comments.append({
                    "platform": "Twitter",
                    "content": text[:280],
                    "score": tweet.get("public_metrics", {}).get("like_count", 0),
                    "author": tweet.get("author", {}).get("userName", "user"),
                    "created_at": tweet.get("createdAt", "")
                })
        return comments
    except Exception as e:
        logger.warning(f"[Twitter] Fetch failed: {e}")
        return []


async def fetch_nitter_rss(topic: str, limit: int = 15) -> list:
    """Fallback: fetch tweets via Nitter RSS (free, no auth)."""
    try:
        encoded = urllib.parse.quote(topic)
        nitter_urls = [
            f"https://nitter.net/search/rss?f=tweets&q={encoded}",
            f"https://nitter.privacydev.net/search/rss?f=tweets&q={encoded}",
        ]
        loop = asyncio.get_running_loop()
        for nitter_url in nitter_urls:
            try:
                req = urllib.request.Request(nitter_url, headers={"User-Agent": "SwarmSim/1.0"})

                def do_request(r=req):
                    with urllib.request.urlopen(r, timeout=6) as response:
                        return response.read().decode()

                raw = await loop.run_in_executor(None, do_request)
                items = re.findall(r'<item>(.*?)</item>', raw, re.DOTALL)
                comments = []
                for item in items[:limit]:
                    title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', item)
                    if title_match:
                        text = title_match.group(1).strip()
                        if len(text) > 15:
                            comments.append({
                                "platform": "Twitter",
                                "content": text[:280],
                                "score": 0,
                                "author": "twitter_user"
                            })
                if comments:
                    return comments
            except Exception:
                continue
        return []
    except Exception as e:
        logger.warning(f"[Nitter] RSS fetch failed: {e}")
        return []


def _analyse_real_sentiment(comments: list) -> dict:
    """Quick keyword-based sentiment analysis on real comments (no LLM)."""
    POSITIVE = {"good", "great", "bullish", "rally", "hope", "win", "support", "positive",
                "optimistic", "up", "buy", "growth", "rise", "strong", "confident", "recover", "gain"}
    NEGATIVE = {"bad", "crash", "crisis", "fear", "loss", "bearish", "panic", "collapse",
                "worried", "fall", "drop", "sell", "weak", "danger", "scam", "fraud", "disaster"}
    pos = neg = neu = 0
    for c in comments:
        words = set(c.get("content", "").lower().split())
        p = len(words & POSITIVE)
        n = len(words & NEGATIVE)
        if p > n:
            pos += 1
        elif n > p:
            neg += 1
        else:
            neu += 1
    total = max(1, len(comments))
    return {
        "positive": round(pos / total * 100),
        "negative": round(neg / total * 100),
        "neutral": round(neu / total * 100),
        "dominant": "positive" if pos > neg else "negative" if neg > pos else "mixed",
        "total_comments_analysed": total
    }


# ═══════════════════════════════════════════════════════════════════════════
# Grok (xAI) integration — Real Twitter/X data + Web intelligence
# ═══════════════════════════════════════════════════════════════════════════

async def fetch_grok_twitter(topic: str, hours_back: int = 48) -> dict:
    """Fetch real X/Twitter posts using Grok's native x_search tool.
    No Twitter API key needed — just XAI_API_KEY."""
    xai_key = os.environ.get("XAI_API_KEY")
    if not xai_key or not XAI_AVAILABLE:
        logger.warning("[Grok] XAI_API_KEY not set or xai-sdk not available")
        return {"tweets": [], "intel_brief": "", "sentiment": {}, "available": False}

    try:
        client = XAIClient(api_key=xai_key)
        from_date = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        to_date = datetime.now(timezone.utc)

        prompt = f"""Search X (Twitter) for real posts about: "{topic}"
from the last {hours_back} hours.

Return REAL tweets from real accounts — exact text, real usernames.
Do not paraphrase or summarise. Quote the actual posts directly.

Reply in EXACTLY this format:

INTEL_BRIEF:
[2-3 sentences summarising what real X users are saying right now
about this topic — dominant mood, key arguments, emerging narratives]

SENTIMENT:
positive: [0-100]
negative: [0-100]
neutral: [0-100]

TWEETS:
AUTHOR: @realusername
CONTENT: [exact tweet text as posted, not paraphrased]
LIKES: [number or unknown]
RETWEETS: [number or unknown]
STANCE: positive|negative|neutral
---
AUTHOR: @realusername
CONTENT: [exact tweet text]
LIKES: [number or unknown]
RETWEETS: [number or unknown]
STANCE: positive|negative|neutral
---
[8-12 tweets, real accounts, mix of verified/unverified,
mix of retail/expert/media perspectives, no bots]"""

        loop = asyncio.get_running_loop()

        def _call():
            chat = client.chat.create(
                model="grok-4-1-fast",
                tools=[xai_x_search(from_date=from_date, to_date=to_date)],
            )
            chat.append(xai_user(prompt))
            return chat.sample()

        response = await loop.run_in_executor(None, _call)
        raw = response.content or ""

        # Parse intel brief
        intel_brief = ""
        if "INTEL_BRIEF:" in raw:
            start = raw.index("INTEL_BRIEF:") + len("INTEL_BRIEF:")
            end = raw.index("SENTIMENT:") if "SENTIMENT:" in raw else start + 400
            intel_brief = raw[start:end].strip()

        # Parse sentiment
        sentiment = {"positive": 33, "negative": 33, "neutral": 34}
        for key in ["positive", "negative", "neutral"]:
            m = re.search(rf'{key}:\s*(\d+)', raw, re.IGNORECASE)
            if m:
                sentiment[key] = int(m.group(1))

        # Parse individual tweets
        tweets = []
        if "TWEETS:" in raw:
            section = raw[raw.index("TWEETS:") + len("TWEETS:"):]
            for block in section.split("---"):
                block = block.strip()
                if not block:
                    continue
                author_m = re.search(r'AUTHOR:\s*(.+)', block)
                content_m = re.search(r'CONTENT:\s*(.+)', block, re.DOTALL)
                stance_m = re.search(r'STANCE:\s*(\w+)', block)
                likes_m = re.search(r'LIKES:\s*(.+)', block)
                rt_m = re.search(r'RETWEETS:\s*(.+)', block)

                def parse_num(m):
                    if not m:
                        return 0
                    val = m.group(1).strip().lower()
                    if val in ["unknown", "n/a", ""]:
                        return 0
                    try:
                        val = val.replace(",", "").replace("k", "000").replace("m", "000000")
                        return int(float(val))
                    except Exception:
                        return 0

                likes = parse_num(likes_m)
                retweets = parse_num(rt_m)

                if content_m:
                    content = content_m.group(1).strip()
                    for stop in ["LIKES:", "RETWEETS:", "STANCE:", "AUTHOR:", "---"]:
                        if stop in content:
                            content = content[:content.index(stop)].strip()
                    if len(content) > 15:
                        tweets.append({
                            "platform": "Twitter",
                            "author": author_m.group(1).strip() if author_m else "X User",
                            "content": content[:280],
                            "stance": stance_m.group(1).lower() if stance_m else "neutral",
                            "likes": likes,
                            "retweets": retweets,
                            "score": likes + (retweets * 3),
                            "is_real": True,
                            "verbatim": True,
                            "source": "grok_x_search"
                        })

        logger.info(f"[Grok] {len(tweets)} tweets fetched for '{topic}'")
        return {
            "tweets": tweets,
            "intel_brief": intel_brief,
            "sentiment": sentiment,
            "available": True,
            "source": "grok_x_search",
            "hours_searched": hours_back
        }

    except Exception as e:
        logger.error(f"[Grok] x_search error: {e}")
        return {"tweets": [], "intel_brief": "", "sentiment": {}, "available": False, "error": str(e)}


async def fetch_grok_web_intel(topic: str, horizon: str = "next week") -> dict:
    """Use Grok with live web_search to build a real-time intelligence brief."""
    xai_key = os.environ.get("XAI_API_KEY")
    if not xai_key or not XAI_AVAILABLE:
        logger.warning("[Grok] XAI_API_KEY not set or xai-sdk not available for web intel")
        return {"brief": "", "available": False}

    try:
        client = XAIClient(api_key=xai_key)
        loop = asyncio.get_running_loop()

        def _call():
            chat = client.chat.create(
                model="grok-4-1-fast",
                tools=[xai_web_search()],
            )
            chat.append(xai_user(
                f"""Search for the very latest news about: "{topic}"
Relevant to predicting outcomes over: {horizon}
Focus on the last 72 hours only.

Write a 200-word intelligence brief with these sections:
1. Current situation — specific facts, numbers, prices, dates
2. Key players and their positions — 2-3 sentences
3. Main risks and opportunities — 2-3 sentences
4. What to watch for {horizon} — 1-2 sentences

Use real names, real numbers. No vague statements. No filler."""
            ))
            return chat.sample()

        response = await loop.run_in_executor(None, _call)
        brief = (response.content or "").strip()
        logger.info(f"[Grok] Web intel brief: {len(brief)} chars")
        return {"brief": brief, "available": True, "source": "grok_web_search"}

    except Exception as e:
        logger.error(f"[Grok] web_search error: {e}")
        return {"brief": "", "available": False, "error": str(e)}



# ═══════════════════════════════════════════════════════════════════════════
# Stock Prediction Engine — Ticker Resolution + Technical Data
# ═══════════════════════════════════════════════════════════════════════════

import numpy as np

try:
    import yfinance as yf
except ImportError:
    yf = None

STOCK_NAME_MAP = {
    # India NSE
    "reliance":"RELIANCE.NS","tcs":"TCS.NS","infosys":"INFY.NS",
    "hdfc bank":"HDFCBANK.NS","hdfcbank":"HDFCBANK.NS",
    "icici bank":"ICICIBANK.NS","icicibank":"ICICIBANK.NS",
    "itc":"ITC.NS","wipro":"WIPRO.NS","sun pharma":"SUNPHARMA.NS",
    "bajaj finance":"BAJFINANCE.NS","bajfinance":"BAJFINANCE.NS",
    "axis bank":"AXISBANK.NS","axisbank":"AXISBANK.NS",
    "kotak":"KOTAKBANK.NS","kotakbank":"KOTAKBANK.NS",
    "maruti":"MARUTI.NS","titan":"TITAN.NS",
    "hul":"HINDUNILVR.NS","hindustan unilever":"HINDUNILVR.NS",
    "tata motors":"TATAMOTORS.NS","tatamotors":"TATAMOTORS.NS",
    "dr reddy":"DRREDDY.NS","adani":"ADANIENT.NS",
    "ongc":"ONGC.NS","ntpc":"NTPC.NS",
    "sbi":"SBIN.NS","state bank":"SBIN.NS",
    "lt":"LT.NS","larsen":"LT.NS",
    "bharti airtel":"BHARTIARTL.NS","airtel":"BHARTIARTL.NS",
    "nifty":"^NSEI","nifty 50":"^NSEI","nifty50":"^NSEI",
    "sensex":"^BSESN","bank nifty":"^NSEBANK","banknifty":"^NSEBANK",
    # US Stocks
    "apple":"AAPL","microsoft":"MSFT","google":"GOOGL","alphabet":"GOOGL",
    "amazon":"AMZN","tesla":"TSLA","nvidia":"NVDA","meta":"META",
    "netflix":"NFLX","amd":"AMD","intel":"INTC","salesforce":"CRM",
    "berkshire":"BRK-B","jpmorgan":"JPM","goldman":"GS",
    "visa":"V","mastercard":"MA",
    # US Indices
    "sp500":"^GSPC","s&p 500":"^GSPC","s&p":"^GSPC",
    "dow jones":"^DJI","dow":"^DJI","nasdaq composite":"^IXIC",
    # Crypto
    "bitcoin":"BTC-USD","btc":"BTC-USD","ethereum":"ETH-USD","eth":"ETH-USD",
    "solana":"SOL-USD","sol":"SOL-USD","bnb":"BNB-USD",
    "xrp":"XRP-USD","dogecoin":"DOGE-USD","doge":"DOGE-USD",
    # Commodities
    "gold":"GC=F","silver":"SI=F","crude oil":"CL=F","oil":"CL=F",
    "natural gas":"NG=F",
}


async def resolve_ticker(query: str, graph: dict) -> list:
    """Extract stock tickers from query + graph entities. Returns [{name, ticker, exchange}]."""
    if not yf:
        return []
    found = []
    q_lower = query.lower()
    entities = [e.get("name", "").lower() for e in (graph.get("entities") or []) if isinstance(e, dict)]
    search_text = q_lower + " " + " ".join(entities)

    # Strategy 1: name map
    for name, ticker in STOCK_NAME_MAP.items():
        if name in search_text:
            exchange = (
                "NSE" if ".NS" in ticker else
                "BSE" if ".BO" in ticker else
                "INDEX" if "^" in ticker else
                "CRYPTO" if "USD" in ticker else "US"
            )
            found.append({"name": name.title(), "ticker": ticker, "exchange": exchange})

    # Strategy 2: explicit CAPS ticker patterns
    skip_words = {"NIFTY","NSE","BSE","FII","DII","IPO","RBI","GDP","CPI","RSI","EMA","SMA","ATH","ATL","ETF"}
    cap_patterns = re.findall(r'\b([A-Z]{2,10}(?:\.NS|\.BO|\.L)?)\b', query)
    loop = asyncio.get_running_loop()
    for pattern in cap_patterns:
        if pattern.upper() in skip_words or any(t["ticker"].upper().startswith(pattern.upper()) for t in found):
            continue
        def _validate(t):
            try:
                obj = yf.Ticker(t)
                fi = obj.fast_info
                return hasattr(fi, "last_price") and fi.last_price and fi.last_price > 0
            except Exception:
                return False
        for candidate in [pattern + ".NS", pattern]:
            valid = await loop.run_in_executor(None, _validate, candidate)
            if valid:
                found.append({"name": pattern, "ticker": candidate, "exchange": "NSE" if ".NS" in candidate else "US"})
                break

    # Deduplicate
    seen, unique = set(), []
    for f in found:
        if f["ticker"] not in seen:
            seen.add(f["ticker"])
            unique.append(f)
    logger.info(f"[Ticker] Resolved: {[u['ticker'] for u in unique[:5]]}")
    return unique[:5]


async def fetch_stock_data_for_prediction(tickers: list) -> list:
    """Fetch 60d OHLCV + MA5/MA20/RSI/support/resistance per ticker."""
    if not yf:
        return []
    results = []
    loop = asyncio.get_running_loop()

    for ticker_info in tickers:
        ticker = ticker_info["ticker"]
        def _fetch(t, tinfo):
            try:
                stock = yf.Ticker(t)
                hist = stock.history(period="70d", interval="1d", auto_adjust=True)
                if hist.empty or len(hist) < 20:
                    return None
                closes = hist["Close"].values.astype(float)
                volumes = hist["Volume"].values.astype(float)
                highs = hist["High"].values.astype(float)
                lows = hist["Low"].values.astype(float)

                last_close = float(closes[-1])
                prev_close = float(closes[-2])
                change = last_close - prev_close
                change_pct = (change / prev_close * 100) if prev_close else 0

                ma5 = float(np.mean(closes[-5:]))
                ma20 = float(np.mean(closes[-20:])) if len(closes) >= 20 else float(np.mean(closes))
                avg_vol = float(np.mean(volumes[-20:])) if len(volumes) >= 20 else float(np.mean(volumes))
                last_vol = float(volumes[-1])
                vol_ratio = last_vol / avg_vol if avg_vol > 0 else 1.0

                wk52_high = float(np.max(highs))
                wk52_low = float(np.min(lows))
                pct_from_high = ((last_close - wk52_high) / wk52_high * 100) if wk52_high else 0
                pct_from_low = ((last_close - wk52_low) / wk52_low * 100) if wk52_low else 0

                recent_highs = sorted(highs[-10:], reverse=True)
                recent_lows = sorted(lows[-10:])
                resistance = float(recent_highs[1]) if len(recent_highs) > 1 else float(recent_highs[0])
                support = float(recent_lows[1]) if len(recent_lows) > 1 else float(recent_lows[0])

                rsi = 50.0
                if len(closes) >= 15:
                    deltas = np.diff(closes[-15:])
                    gains = deltas[deltas > 0]
                    losses = deltas[deltas < 0]
                    avg_gain = float(np.mean(gains)) if gains.size > 0 else 0.0
                    avg_loss = float(np.mean(abs(losses))) if losses.size > 0 else 0.001
                    if avg_loss == 0.0: avg_loss = 0.001
                    rsi = round(100 - (100 / (1 + avg_gain / avg_loss)), 1)

                above_ma5 = last_close > ma5
                above_ma20 = last_close > ma20
                trend = (
                    "STRONG UPTREND" if above_ma5 and above_ma20 and change_pct > 0.5 else
                    "UPTREND" if above_ma20 else
                    "STRONG DOWNTREND" if not above_ma5 and not above_ma20 and change_pct < -0.5 else
                    "DOWNTREND" if not above_ma20 else "MIXED"
                )
                rsi_signal = "OVERSOLD - bounce likely" if rsi < 30 else "OVERBOUGHT - pullback likely" if rsi > 70 else "NEUTRAL"
                vol_signal = "HIGH VOLUME - strong conviction" if vol_ratio > 1.5 else "LOW VOLUME - weak conviction" if vol_ratio < 0.7 else "NORMAL VOLUME"

                currency = "USD"
                try:
                    fi = stock.fast_info
                    currency = getattr(fi, "currency", currency)
                except Exception:
                    if ".NS" in t or ".BO" in t: currency = "INR"

                news_titles = []
                try:
                    for n in (stock.news or [])[:3]:
                        title = n.get("title") or ""
                        if title: news_titles.append(title)
                except Exception:
                    pass

                return {
                    "name": tinfo.get("name", t), "ticker": t,
                    "exchange": tinfo.get("exchange", ""), "currency": currency.upper(),
                    "last_close": round(last_close, 2), "prev_close": round(prev_close, 2),
                    "change": round(change, 2), "change_pct": round(change_pct, 2),
                    "ma5": round(ma5, 2), "ma20": round(ma20, 2),
                    "above_ma5": bool(above_ma5), "above_ma20": bool(above_ma20),
                    "volume": int(last_vol), "avg_volume_20d": int(avg_vol),
                    "vol_ratio": round(vol_ratio, 2), "vol_signal": vol_signal,
                    "wk52_high": round(wk52_high, 2), "wk52_low": round(wk52_low, 2),
                    "pct_from_high": round(pct_from_high, 2), "pct_from_low": round(pct_from_low, 2),
                    "support": round(support, 2), "resistance": round(resistance, 2),
                    "rsi": rsi, "rsi_signal": rsi_signal, "trend": trend, "news": news_titles,
                }
            except Exception as e:
                logger.error(f"[Market] Fetch error for {t}: {e}")
                return None
        data = await loop.run_in_executor(None, _fetch, ticker, ticker_info)
        if data:
            results.append(data)
        await asyncio.sleep(0.1)
    return results


def build_market_context(stock_data: list) -> str:
    """Build a text block of stock data for injection into LLM prompts."""
    if not stock_data:
        return ""
    ccy_map = {"INR":"Rs","USD":"$","GBP":"GBP","EUR":"EUR","JPY":"JPY"}
    lines = ["LIVE STOCK DATA - USE THESE EXACT NUMBERS:\n" + "=" * 55]
    for s in stock_data:
        ccy = ccy_map.get(s["currency"], s["currency"] + " ")
        lines.append(f"""
{s['name'].upper()} | {s['ticker']}
Close:      {ccy}{s['last_close']:,.2f}  ({s['change']:+.2f} | {s['change_pct']:+.2f}%)
Previous:   {ccy}{s['prev_close']:,.2f}
MA5:        {ccy}{s['ma5']:,.2f}  ({'ABOVE-bullish' if s['above_ma5'] else 'BELOW-bearish'})
MA20:       {ccy}{s['ma20']:,.2f}  ({'ABOVE-bullish' if s['above_ma20'] else 'BELOW-bearish'})
Support:    {ccy}{s['support']:,.2f}
Resistance: {ccy}{s['resistance']:,.2f}
52W High:   {ccy}{s['wk52_high']:,.2f}  ({s['pct_from_high']:+.1f}% from high)
52W Low:    {ccy}{s['wk52_low']:,.2f}  ({s['pct_from_low']:+.1f}% from low)
RSI(14):    {s['rsi']} - {s['rsi_signal']}
Volume:     {s['volume']:,} ({s['vol_ratio']:.1f}x 20d avg) - {s['vol_signal']}
Trend:      {s['trend']}
News:       {' | '.join(s['news'][:2]) if s['news'] else 'None'}""")
    lines.append("\n" + "=" * 55)
    lines.append("""
PREDICTION RULES:
1. Use EXACT prices above - never approximate
2. UP target = resistance. DOWN target = support
3. RSI < 30 = oversold -> bias UP. RSI > 70 = overbought -> bias DOWN
4. Price above MA20 = bullish bias. Below = bearish bias
5. Vol ratio > 1.5 = institutional activity - high conviction
6. Within 2% of 52W high = potential reversal zone
7. Within 5% of 52W low = potential bounce zone
8. Use: "will likely", "expect", "target is" (not: may, could, might)
""")
    return "\n".join(lines)



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
    grok_ready = bool(os.environ.get("XAI_API_KEY") and XAI_AVAILABLE)
    return {
        "status": "ok",
        "grok_available": grok_ready,
        "twitter_source": "Grok X Search" if grok_ready else "Nitter RSS fallback",
    }


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

        # Also try Grok web intel in parallel (enhances the brief)
        grok_web_result = await fetch_grok_web_intel(topic, horizon)
        grok_web_brief = grok_web_result.get("brief", "") if grok_web_result.get("available") else ""

        # Also fetch real Twitter via Grok to seed into the session
        grok_twitter_result = await fetch_grok_twitter(topic, hours_back=48)
        if grok_twitter_result.get("available") and grok_twitter_result.get("tweets"):
            await db.sessions.update_one(
                {"id": session_id},
                {"$set": {
                    "social_seed": grok_twitter_result["tweets"],
                    "social_seed_sentiment": grok_twitter_result.get("sentiment", {}),
                    "social_seed_sources": ["X/Twitter via Grok"],
                    "social_seed_brief": grok_twitter_result.get("intel_brief", ""),
                }}
            )
            logger.info(f"[Live] Grok Twitter seeded: {len(grok_twitter_result['tweets'])} posts")

        if not web_data.get("results") and not financial_data.get("has_data") and not grok_web_brief:
            await db.sessions.update_one(
                {"id": session_id},
                {"$set": {"live_fetch_status": "failed", "live_fetch_error": "Could not fetch live data. Please try a different topic."}}
            )
            return

        # Build contexts for the orchestrator
        context_parts = [f"- {r['title']}: {r['snippet']}" for r in web_data["results"][:20]]
        web_context = "\n".join(context_parts)

        # Prepend Grok web intel brief if available (higher quality, more current)
        if grok_web_brief:
            web_context = f"=== GROK REAL-TIME WEB INTELLIGENCE ===\n{grok_web_brief}\n=== END GROK INTEL ===\n\n{web_context}"

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
    """Background task: orchestrator runs Persona Agent pipeline with caching + social seeding."""
    from services.agents import orchestrator
    try:
        session = await db.sessions.find_one({"id": session_id})
        if not session:
            return

        # Build social context from seed data
        social_context = ""
        social_seed = session.get("social_seed", [])
        real_sentiment = session.get("social_seed_sentiment", {})
        if social_seed:
            top_real = social_seed[:12]
            real_voices = "\n".join([
                f"[{c.get('platform', 'Unknown')}] {c.get('content', '')[:100]}"
                for c in top_real
            ])
            dominant = real_sentiment.get("dominant", "mixed")
            social_context = (
                f"\nREAL PUBLIC OPINION (from actual Reddit/Twitter):\n{real_voices}\n"
                f"\nReal sentiment: {real_sentiment.get('positive', 0)}% positive, "
                f"{real_sentiment.get('negative', 0)}% negative, "
                f"{real_sentiment.get('neutral', 0)}% neutral. Dominant: {dominant}\n"
                f"\nGenerate agents whose initial_stance REFLECTS this real distribution. "
                f"Mirror the diversity of opinion above."
            )

        # Check agent cache (skip cache if social seed exists - stances should be fresh)
        graph_hash = hashlib.md5(session.get("graph_json", "").encode()).hexdigest()
        cached_agents = None if social_seed else await get_cached_agents(graph_hash, num_agents)

        if cached_agents:
            logger.info(f"[Cache] Agent cache hit: {len(cached_agents)} agents")
            agents = cached_agents
            for i, agent in enumerate(agents):
                agent.setdefault("id", f"agent_{i+1}")
                ptype = agent.get("personality_type", "Neutral")
                template = PERSONALITY_TEMPLATES.get(ptype, PERSONALITY_TEMPLATES["Neutral"])
                agent.setdefault("communication_style", template["style"])
                agent.setdefault("platform_preference", template["platform"])
                agent.setdefault("memories", [])
            diversity_score = 0.7
        else:
            call_fns = {"premium": call_claude_premium, "fast": call_claude_fast, "flash": call_gemini_flash}
            result = await orchestrator.run_agent_generation_pipeline(
                session_id, num_agents, call_fns, db, social_context=social_context
            )
            if not result:
                return

            agents = result["agents"]
            diversity_score = result["diversity_score"]

            for i, agent in enumerate(agents):
                agent.setdefault("id", f"agent_{i+1}")
                ptype = agent.get("personality_type", "Neutral")
                template = PERSONALITY_TEMPLATES.get(ptype, PERSONALITY_TEMPLATES["Neutral"])
                agent.setdefault("communication_style", template["style"])
                agent.setdefault("platform_preference", template["platform"])
                agent.setdefault("memories", [])

            if not social_seed:
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


@api_router.post("/sessions/{session_id}/fetch-social-seed")
async def fetch_social_seed(session_id: str, request: SocialSeedRequest):
    """Fetch real Reddit + Twitter comments on the topic to seed the simulation."""
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    topic = request.topic or session.get("topic", "")
    if not topic:
        raise HTTPException(status_code=400, detail="Topic required")

    all_comments = []
    sources_fetched = []

    if request.include_reddit:
        try:
            reddit_comments = await fetch_reddit_comments(topic, limit=request.max_comments)
            all_comments.extend(reddit_comments)
            if reddit_comments:
                news_count = sum(1 for c in reddit_comments if c['platform'] == 'News')
                reddit_count = sum(1 for c in reddit_comments if c['platform'] == 'Reddit')
                parts = []
                if reddit_count > 0:
                    parts.append(f"Reddit ({reddit_count})")
                if news_count > 0:
                    parts.append(f"News ({news_count})")
                sources_fetched.extend(parts)
        except Exception as e:
            logger.error(f"[SocialSeed] Reddit error: {e}")

    grok_brief = ""
    grok_sentiment = {}
    grok_twitter_fetched = False

    if request.include_twitter:
        # Priority 1: Grok X Search (real tweets)
        grok_result = await fetch_grok_twitter(topic, hours_back=48)
        if grok_result.get("available") and grok_result.get("tweets"):
            all_comments.extend(grok_result["tweets"])
            grok_brief = grok_result.get("intel_brief", "")
            grok_sentiment = grok_result.get("sentiment", {})
            grok_twitter_fetched = True
            sources_fetched.append(f"X/Twitter via Grok ({len(grok_result['tweets'])} posts)")
            logger.info(f"[SocialSeed] Grok fetched {len(grok_result['tweets'])} tweets")
        else:
            # Fallback: existing Twitter + Nitter path
            logger.info("[SocialSeed] Grok unavailable — falling back to Twitter/Nitter")
            twitter_comments = await fetch_twitter_comments(topic, limit=20)
            if not twitter_comments:
                twitter_comments = await fetch_nitter_rss(topic, limit=15)
            all_comments.extend(twitter_comments)
            if twitter_comments:
                sources_fetched.append(f"Twitter ({len(twitter_comments)} tweets)")

    if not all_comments:
        return {
            "comments_fetched": 0,
            "sources": [],
            "real_sentiment": {"positive": 0, "negative": 0, "neutral": 100, "dominant": "mixed", "total_comments_analysed": 0},
            "sample": [],
            "message": f"No social data found for: {topic}. Simulation will proceed without seeding."
        }

    all_comments.sort(key=lambda x: x.get("score", 0), reverse=True)
    top_comments = all_comments[:request.max_comments]
    real_sentiment = grok_sentiment if grok_twitter_fetched and grok_sentiment else _analyse_real_sentiment(top_comments)

    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {
            "social_seed": top_comments,
            "social_seed_sentiment": real_sentiment,
            "social_seed_sources": sources_fetched,
            "social_seed_brief": grok_brief,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )

    powered_by = "Grok X Search" if grok_twitter_fetched else "Reddit + Nitter fallback"

    return {
        "comments_fetched": len(top_comments),
        "sources": sources_fetched,
        "real_sentiment": real_sentiment,
        "grok_brief": grok_brief,
        "sample": top_comments[:5],
        "powered_by": powered_by,
        "message": f"Seeded with {len(top_comments)} real comments from {', '.join(sources_fetched)}"
    }


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

        # Round 0: Inject real social media seed posts
        social_seed = session.get("social_seed", [])
        if social_seed:
            logger.info(f"[Sim] Injecting {len(social_seed)} real social seed posts as Round 0")
            for i, comment in enumerate(social_seed[:20]):
                seed_post = {
                    "session_id": session_id,
                    "round": 0,
                    "agent_id": f"real_{i+1}",
                    "agent_name": comment.get("author", "real_user")[:20],
                    "agent_emoji": "",
                    "platform": comment.get("platform", "Reddit"),
                    "content": comment.get("content", "")[:280],
                    "post_type": "real_seed",
                    "is_hub_post": False,
                    "is_real": True,
                    "source_url": comment.get("url", ""),
                    "source_score": comment.get("score", 0),
                    "influence_level": min(10, max(1, comment.get("score", 0) // 10 + 3)),
                    "belief_position": 0.0,
                    "emotional_valence": 0.0,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.sim_posts.insert_one(seed_post)
                all_posts.append(seed_post)

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
                    posts_data = parse_llm_json(response, fallback=[], label=f"simulation round {round_num} posts")
                    if not isinstance(posts_data, list):
                        logger.warning("[Sim] Non-list post JSON in round %s; using fallbacks", round_num)
                        posts_data = []

                    for item in posts_data:
                        if not isinstance(item, dict):
                            continue
                        idx = item.get("agent_index", 1) - 1
                        if 0 <= idx < len(batch):
                            agent = batch[idx]
                            content = item.get("content", "").strip()
                            if not content:
                                continue
                            if agent.get("platform_preference") == "Twitter" and len(content) > 300:
                                content = content[:280].rsplit(" ", 1)[0] + "..."

                            post = build_post_document(agent, session_id, round_num, content, hub_ids)
                            await db.sim_posts.insert_one(post)
                            all_posts.append(post)
                            round_posts.append(post)
                            agent["memories"] = agent.get("memories", [])[-9:] + \
                                               [f"Round {round_num}: I posted: {content[:80]}"]
                except Exception as e:
                    logger.error(f"[Sim] Batch error round {round_num}: {e}")
                    posts_data = []

                posted_ids = {post.get("agent_id") for post in round_posts if post.get("round") == round_num}
                for agent in batch:
                    if agent["id"] in posted_ids:
                        continue
                    content = build_fallback_post(agent, query, round_num, num_rounds)
                    post = build_post_document(agent, session_id, round_num, content, hub_ids, fallback=True)
                    await db.sim_posts.insert_one(post)
                    all_posts.append(post)
                    round_posts.append(post)
                    agent["memories"] = agent.get("memories", [])[-9:] + \
                                       [f"Round {round_num}: I fallback-posted: {content[:80]}"]

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
                        replies_data = parse_llm_json(response, fallback=[], label=f"simulation round {round_num} replies")
                        if not isinstance(replies_data, list):
                            replies_data = []

                        for item in replies_data:
                            if not isinstance(item, dict):
                                continue
                            idx = item.get("agent_index", 1) - 1
                            if 0 <= idx < len(reply_pairs):
                                agent, target_post = reply_pairs[idx]
                                reply_content = item.get("content", "").strip()
                                if not reply_content:
                                    continue
                                reply = build_post_document(
                                    agent, session_id, round_num, reply_content, hub_ids,
                                    post_type="reply", platform=target_post["platform"],
                                    reply_to=target_post["agent_name"],
                                )
                                await db.sim_posts.insert_one(reply)
                                all_posts.append(reply)
                                round_posts.append(reply)
                    except Exception as e:
                        logger.error(f"[Sim] Batched reply error: {e}")

            # Tier 2: Generate clone echo posts
            echo_posts = []
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
    """Progressive 2-phase report: Phase 1 (Haiku, fast core) + Phase 2 (Sonnet, deep analysis).
    Now with live stock data injection for financial predictions."""
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

    # ── STEP 0: Resolve tickers + fetch live market data ──
    tickers = await resolve_ticker(query, graph)
    stock_data = await fetch_stock_data_for_prediction(tickers) if tickers else []
    market_context = build_market_context(stock_data) if stock_data else ""
    logger.info(f"[Report] Stock data for {len(stock_data)} tickers injected into report prompt")

    # ── PHASE 1 — fast core report (Haiku, small) ──
    phase1_system = "You are a prediction analyst. Return ONLY valid JSON, no markdown."
    phase1_prompt = f"""Prediction: {query}
Context: {graph.get('summary','')}
{market_context}
Agents ({len(agents)}):
{agents_summary}
Simulation ({session.get('total_rounds',3)} rounds):
{transcript}

Return JSON with ONLY these fields:
{{
  "executive_summary": "3 sentences. If stock data provided, cite exact prices and technical signals.",
  "prediction": {{
    "outcome": "one sentence with specific price targets if stock data available",
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
        phase1 = parse_llm_json(r1, fallback=None, label="report phase 1")
        if not isinstance(phase1, dict):
            raise ValueError("Phase 1 did not return a JSON object")
    except Exception as e:
        logger.error(f"Report phase 1 failed: {e}")
        raise HTTPException(status_code=500, detail=f"Report phase 1 failed: {str(e)}")

    # ── PHASE 2 — deep analysis (Sonnet, medium) ──
    phase2_system = "You are a senior analyst. Return ONLY valid JSON, no markdown."
    phase2_prompt = f"""Prediction: {query}
{market_context}
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
        phase2 = parse_llm_json(r2, fallback={}, label="report phase 2")
        if not isinstance(phase2, dict):
            phase2 = {}
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

    # Attach live stock data to report for frontend + PDF
    if stock_data:
        report["stock_data"] = stock_data

    report["prediction_quality"] = build_report_quality_metadata(
        session=session,
        posts=posts,
        stock_data=stock_data,
        report=report,
    )

    # Add real vs simulated sentiment comparison if social seed exists
    real_sentiment = session.get("social_seed_sentiment")
    if real_sentiment and real_sentiment.get("total_comments_analysed", 0) > 0:
        sim_support = report.get("opinion_landscape", {}).get("support_percentage", 50)
        sim_opposition = report.get("opinion_landscape", {}).get("opposition_percentage", 30)
        real_positive = real_sentiment.get("positive", 50)
        drift = abs(sim_support - real_positive)
        report["real_vs_simulated"] = {
            "real_sentiment": real_sentiment,
            "simulated_sentiment": {
                "positive": sim_support,
                "negative": sim_opposition,
                "neutral": 100 - sim_support - sim_opposition
            },
            "drift_percentage": drift,
            "verdict": (
                "Strong alignment" if drift <= 10 else
                "Moderate drift" if drift <= 25 else
                "Significant divergence"
            ),
            "total_real_comments": real_sentiment.get("total_comments_analysed", 0),
            "sources": session.get("social_seed_sources", [])
        }

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
    """Download prediction report as PDF — uses multi_cell() throughout to prevent text truncation."""
    from fpdf import FPDF
    
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.get("report_json"):
        raise HTTPException(status_code=404, detail="Report not generated yet")
    
    report = json.loads(session["report_json"])
    query = session.get("prediction_query", "N/A")
    
    def safe_text(text, max_len=800):
        """Sanitize text for PDF output"""
        if not text:
            return "N/A"
        if isinstance(text, list):
            text = "; ".join(str(item) for item in text)
        text = str(text)
        replacements = {
            '\u2014': '-', '\u2013': '-', '\u201c': '"', '\u201d': '"',
            '\u2018': "'", '\u2019': "'", '\u2026': '...', '\u2022': '*',
            '\u2192': '->', '\u2190': '<-', '\u2248': '~', '\u2260': '!=',
            '\u2264': '<=', '\u2265': '>=', '\u00d7': 'x', '\u00f7': '/',
            '\u00b1': '+/-', '\u00b0': ' deg', '\u00a9': '(c)', '\u00ae': '(R)',
            '\u2122': '(TM)', '\u00a0': ' ',
        }
        for u, a in replacements.items():
            text = text.replace(u, a)
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        text = ''.join(c if (ord(c) < 128 and c.isprintable()) or c == ' ' else '' for c in text)
        while '  ' in text:
            text = text.replace('  ', ' ')
        if len(text) > max_len:
            text = text[:max_len] + "..."
        return text.strip() or "N/A"
    
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # ── Title ──
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(0, 80, 60)
    pdf.cell(0, 15, "SwarmSim Prediction Report", ln=True, align="C")
    pdf.ln(5)
    
    # ── Question ──
    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(190, 6, f"Question: {safe_text(query, 300)}")
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}", ln=True)
    pdf.ln(8)
    
    # ── Prediction Outcome Box ──
    pdf.set_fill_color(235, 250, 245)
    pdf.set_draw_color(0, 180, 140)
    y_box = pdf.get_y()
    outcome = safe_text(report.get("prediction", {}).get("outcome", "N/A"), 400)
    # Estimate box height
    box_h = max(30, 10 + len(outcome) // 80 * 6 + 14)
    pdf.rect(10, y_box, 190, box_h, style="DF")
    pdf.set_xy(15, y_box + 4)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(0, 80, 60)
    pdf.cell(0, 7, "PREDICTED OUTCOME", ln=True)
    pdf.set_x(15)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(180, 6, outcome)
    pdf.set_y(y_box + box_h + 6)
    
    # ── Confidence ──
    prediction = report.get("prediction", {})
    confidence = prediction.get("confidence", "N/A")
    score = prediction.get("confidence_score", 0) or 0
    timeframe = safe_text(prediction.get("timeframe", "N/A"), 50)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(60, 8, f"Confidence: {confidence} ({int(score * 100)}%)")
    pdf.cell(60, 8, f"Timeframe: {timeframe}", ln=True)
    pdf.ln(6)
    
    # ── Stock Data Section ──
    stock_data = report.get("stock_data", [])
    if stock_data:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(0, 80, 60)
        pdf.cell(0, 10, "Live Market Data", ln=True)
        pdf.set_text_color(0, 0, 0)
        ccy_map = {"INR": "Rs", "USD": "$", "GBP": "GBP", "EUR": "EUR"}
        for s in stock_data:
            ccy = ccy_map.get(s.get("currency", ""), "")
            change_color = (0, 130, 80) if s.get("change_pct", 0) >= 0 else (200, 40, 40)
            
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(60, 7, f"{s['name']} ({s['ticker']})")
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(40, 7, f"{ccy}{s['last_close']:,.2f}")
            pdf.set_text_color(*change_color)
            pdf.cell(30, 7, f"{s['change_pct']:+.2f}%")
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 7, f"RSI: {s.get('rsi', 'N/A')} | {s.get('trend', '')}", ln=True)
            
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 5, f"  MA5: {ccy}{s.get('ma5',0):,.2f}  |  MA20: {ccy}{s.get('ma20',0):,.2f}  |  Support: {ccy}{s.get('support',0):,.2f}  |  Resistance: {ccy}{s.get('resistance',0):,.2f}", ln=True)
            pdf.cell(0, 5, f"  52W Range: {ccy}{s.get('wk52_low',0):,.2f} - {ccy}{s.get('wk52_high',0):,.2f}  |  Vol: {s.get('volume',0):,} ({s.get('vol_ratio',0):.1f}x avg)  |  {s.get('vol_signal','')}", ln=True)
            
            if s.get("news"):
                for n in s["news"][:2]:
                    pdf.set_font("Helvetica", "I", 8)
                    pdf.set_text_color(80, 80, 80)
                    pdf.multi_cell(190, 4, f"  News: {safe_text(n, 200)}")
                    pdf.set_text_color(0, 0, 0)
            pdf.ln(3)
        pdf.ln(4)
    
    # ── Executive Summary ──
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 80, 60)
    pdf.cell(0, 10, "Executive Summary", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(190, 6, safe_text(report.get("executive_summary", "N/A"), 1200))
    pdf.ln(6)
    
    # ── Opinion Landscape ──
    opinion = report.get("opinion_landscape", {})
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 80, 60)
    pdf.cell(0, 10, "Opinion Landscape", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    sentiment = safe_text(opinion.get("dominant_sentiment", "N/A"), 50)
    pdf.cell(0, 6, f"Dominant Sentiment: {sentiment.title()}", ln=True)
    pdf.cell(60, 6, f"Support: {opinion.get('support_percentage', 0)}%")
    pdf.cell(60, 6, f"Opposition: {opinion.get('opposition_percentage', 0)}%")
    pdf.cell(60, 6, f"Undecided: {opinion.get('undecided_percentage', 0)}%", ln=True)
    pdf.ln(4)
    
    # ── Key Factions ──
    factions = opinion.get("key_factions", [])
    if factions:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Key Factions:", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for faction in factions:
            name = safe_text(faction.get('name', 'N/A'), 80)
            size = safe_text(faction.get('size', 'N/A'), 20)
            stance = safe_text(faction.get('stance', 'N/A'), 300)
            arguments = safe_text(faction.get('key_arguments', []), 400)
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(190, 6, f"- {name} ({size})")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(190, 5, f"  {stance}")
            if arguments and arguments != "N/A":
                pdf.multi_cell(190, 5, f"  Arguments: {arguments}")
    pdf.ln(4)
    
    # ── Risk Factors ──
    risks = report.get("risk_factors", [])
    if risks:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(200, 40, 40)
        pdf.cell(0, 10, "Risk Factors", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        for risk in risks:
            likelihood = safe_text(risk.get("likelihood", "N/A"), 30)
            factor = safe_text(risk.get("factor", "N/A"), 300)
            impact = safe_text(risk.get("impact", "N/A"), 400)
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(190, 6, f"[{likelihood}] {factor}")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(190, 5, f"  Impact: {impact}")
        pdf.ln(4)
    
    # ── Key Turning Points ──
    turning_points = report.get("key_turning_points", [])
    if turning_points:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(0, 80, 60)
        pdf.cell(0, 10, "Key Turning Points", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        for point in turning_points:
            round_num = point.get('round', 'N/A')
            description = safe_text(point.get('description', 'N/A'), 300)
            impact = safe_text(point.get('impact', 'N/A'), 400)
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(190, 6, f"Round {round_num}: {description}")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(190, 5, f"  Impact: {impact}")
        pdf.ln(4)
    
    # ── Alternative Scenarios ──
    scenarios = report.get("alternative_scenarios", [])
    if scenarios:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(0, 80, 60)
        pdf.cell(0, 10, "Alternative Scenarios", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        for scenario in scenarios:
            prob = scenario.get("probability", 0) or 0
            scenario_name = safe_text(scenario.get('scenario', 'N/A'), 200)
            conditions = safe_text(scenario.get('conditions', 'N/A'), 400)
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(190, 6, f"{scenario_name} ({int(prob * 100)}% probability)")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(190, 5, f"  Conditions: {conditions}")
        pdf.ln(4)
    
    # ── Agent Highlights ──
    highlights = report.get("agent_highlights", [])
    if highlights:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(0, 80, 60)
        pdf.cell(0, 10, "Agent Highlights", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        for highlight in highlights:
            pdf.set_font("Helvetica", "B", 10)
            name = safe_text(highlight.get('agent_name', 'N/A'), 80)
            pdf.multi_cell(190, 6, f"- {name}")
            pdf.set_font("Helvetica", "", 10)
            role = safe_text(highlight.get('role_in_simulation', 'N/A'), 300)
            pdf.multi_cell(190, 5, f"Role: {role}")
            quote = safe_text(highlight.get("notable_quote", ""), 300)
            if quote and quote != "N/A":
                pdf.set_font("Helvetica", "I", 10)
                pdf.multi_cell(190, 5, f'"{quote}"')
                pdf.set_font("Helvetica", "", 10)
            pdf.ln(2)
    
    # ── Footer ──
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, "Generated by SwarmSim - Swarm Intelligence Prediction Engine", ln=True, align="C")
    if stock_data:
        pdf.cell(0, 5, f"Market data as of {datetime.now().strftime('%Y-%m-%d %H:%M UTC')} via yfinance", ln=True, align="C")
    
    pdf_output = io.BytesIO()
    pdf_bytes = pdf.output()
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    
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
