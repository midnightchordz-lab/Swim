from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import json
import re
import random
import asyncio
import io

import base64
import httpx

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
    num_agents: int = Field(default=20, ge=10, le=50)

class SimulateRequest(BaseModel):
    num_rounds: int = Field(default=5, ge=3, le=15)

class ChatRequest(BaseModel):
    target_type: str  # "agent" or "report"
    target_id: str  # agent_id or "report_agent"
    message: str


def clean_json_response(text: str) -> str:
    """Strip markdown code fences and think tags from Claude responses"""
    # Remove think tags
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # Remove markdown code fences
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    return text.strip()


async def call_claude(system_prompt: str, user_prompt: str, max_tokens: int = 3000, image_data: dict = None, retries: int = 3) -> str:
    """Call Claude API using emergentintegrations or litellm for images with retry logic"""
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="EMERGENT_LLM_KEY not configured")
    
    last_error = None
    
    for attempt in range(retries):
        try:
            # If image data is provided, use litellm directly with Emergent proxy
            if image_data:
                import litellm
                from emergentintegrations.llm.chat import get_integration_proxy_url
                
                proxy_url = get_integration_proxy_url()
                
                # Build the message with image
                messages = [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{image_data['media_type']};base64,{image_data['base64']}"
                                }
                            },
                            {
                                "type": "text",
                                "text": user_prompt
                            }
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
            
            # For text-only, use emergentintegrations
            chat = LlmChat(
                api_key=api_key,
                session_id=str(uuid.uuid4()),
                system_message=system_prompt
            )
            chat.with_model("anthropic", "claude-sonnet-4-20250514")
            
            user_message = UserMessage(text=user_prompt)
            response = await chat.send_message(user_message)
            return response
            
        except Exception as e:
            last_error = e
            logger.warning(f"Claude API attempt {attempt + 1}/{retries} failed: {str(e)[:100]}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                continue
            raise
    
    raise last_error


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
    """Upload document and extract knowledge graph"""
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Parse document (returns text and optional image_data)
    text, image_data = await parse_document(file)
    
    # Extract knowledge graph using Claude
    system_prompt = """You are a knowledge-graph extraction expert. Given seed text (or an image) and a prediction question, extract entities and relationships. Respond ONLY with valid JSON, no markdown fences."""
    
    if image_data:
        # Image-based extraction
        user_prompt = f"""Analyze this image carefully and extract a knowledge graph based on the content you see.
Prediction Question: {prediction_query}

Return JSON:
{{
  "summary": "2-3 sentence description of what the image shows and the situation",
  "themes": ["theme1", "theme2", "theme3"],
  "entities": [
    {{
      "id": "e1",
      "name": "Entity Name",
      "type": "person|organization|faction|concept|event",
      "description": "Brief description",
      "stance": "positive|negative|neutral|conflicted"
    }}
  ],
  "relationships": [
    {{
      "source": "e1",
      "target": "e2",
      "label": "relationship description",
      "weight": 0.8
    }}
  ]
}}
Extract 8-20 entities and 10-25 relationships relevant to the prediction question based on what you see in the image."""
    else:
        # Text-based extraction
        text = text[:TEXT_TRUNCATE_LIMIT]
        user_prompt = f"""Seed Text: \"\"\"{text}\"\"\"
Prediction Question: {prediction_query}

Return JSON:
{{
  "summary": "2-3 sentence description of the situation",
  "themes": ["theme1", "theme2", "theme3"],
  "entities": [
    {{
      "id": "e1",
      "name": "Entity Name",
      "type": "person|organization|faction|concept|event",
      "description": "Brief description",
      "stance": "positive|negative|neutral|conflicted"
    }}
  ],
  "relationships": [
    {{
      "source": "e1",
      "target": "e2",
      "label": "relationship description",
      "weight": 0.8
    }}
  ]
}}
Extract 8-20 entities and 10-25 relationships relevant to the prediction question."""

    try:
        response = await call_claude(system_prompt, user_prompt, max_tokens=3000, image_data=image_data)
        cleaned = clean_json_response(response)
        graph = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}, response: {response[:500]}")
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


@api_router.post("/sessions/{session_id}/generate-agents")
async def generate_agents(session_id: str, request: GenerateAgentsRequest):
    """Generate AI agent personas based on knowledge graph"""
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("status") not in ["graph_ready", "agents_ready"]:
        raise HTTPException(status_code=400, detail="Knowledge graph not ready")
    
    graph = json.loads(session["graph_json"])
    query = session["prediction_query"]
    num_agents = request.num_agents
    
    entities_summary = json.dumps([{"name": e["name"], "type": e["type"]} for e in graph.get("entities", [])])
    
    system_prompt = """You are a simulation designer. Create realistic agent personas for a social prediction simulation. Respond ONLY with valid JSON, no markdown fences."""
    
    user_prompt = f"""World Context: {graph.get('summary', '')}
Key Themes: {', '.join(graph.get('themes', []))}
Entities: {entities_summary}
Prediction Question: {query}

Create exactly {num_agents} diverse agent personas. Return JSON:
{{
  "agents": [
    {{
      "id": "agent_1",
      "name": "Full Name",
      "avatar_emoji": "single emoji",
      "age": 35,
      "occupation": "specific job",
      "background": "2-sentence backstory",
      "personality_type": "Skeptic|Optimist|Insider|Contrarian|Expert|Neutral|Activist|Pragmatist",
      "initial_stance": "Their position on the topic (1-2 sentences)",
      "influence_level": 7,
      "platform_preference": "Twitter|Reddit",
      "communication_style": "analytical|emotional|aggressive|diplomatic|satirical|factual"
    }}
  ]
}}
Make agents feel like real distinct people. Vary demographics, professions, viewpoints."""

    try:
        response = await call_claude(system_prompt, user_prompt, max_tokens=4000)
        cleaned = clean_json_response(response)
        agents_data = json.loads(cleaned)
        agents = agents_data.get("agents", [])
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse agents from AI response")
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")
    
    # Initialize agent memories
    for agent in agents:
        agent["memories"] = []
    
    await db.sessions.update_one(
        {"id": session_id},
        {
            "$set": {
                "status": "agents_ready",
                "agents_json": json.dumps(agents),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"agents": agents, "count": len(agents)}


async def run_simulation(session_id: str, num_rounds: int):
    """Background task to run the simulation"""
    try:
        session = await db.sessions.find_one({"id": session_id})
        if not session:
            return
        
        agents = json.loads(session["agents_json"])
        graph = json.loads(session["graph_json"])
        query = session["prediction_query"]
        
        # Store current round for status tracking
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {"current_round": 0, "total_rounds": num_rounds}}
        )
        
        for round_num in range(1, num_rounds + 1):
            await db.sessions.update_one(
                {"id": session_id},
                {"$set": {"current_round": round_num}}
            )
            
            # Select random subset of agents (60-80%)
            active_agents = random.sample(agents, k=max(3, int(len(agents) * random.uniform(0.6, 0.8))))
            
            # Get recent posts for context
            recent_posts = await db.sim_posts.find(
                {"session_id": session_id}
            ).sort("_id", -1).limit(8).to_list(8)
            
            recent_context = "\n".join([
                f"{p['platform']}: {p['agent_name']}: {p['content']}"
                for p in reversed(recent_posts)
            ]) if recent_posts else "No previous posts yet."
            
            for agent in active_agents:
                platform = agent.get("platform_preference", random.choice(["Twitter", "Reddit"]))
                
                # Get agent's recent memories
                agent_memories = agent.get("memories", [])[-5:]
                memory_context = "\n".join(agent_memories) if agent_memories else "No previous memories."
                
                platform_instruction = "Keep under 280 characters. Short and punchy." if platform == "Twitter" else "Write 2-4 sentences. More nuanced."
                
                system_prompt = f"""You are playing the role of {agent['name']}. Stay deeply in character. Write authentic social media posts reflecting this person's background, personality, and stance. Be specific and human."""
                
                user_prompt = f"""You are: {agent['name']} ({agent['occupation']})
Personality: {agent['personality_type']}
Communication Style: {agent['communication_style']}
Background: {agent['background']}
Current Stance: {agent['initial_stance']}
Your recent thoughts: {memory_context}
World Context: {graph.get('summary', '')}
Prediction Question: {query}
Recent posts (last 8): {recent_context}
Platform: {platform}
{platform_instruction}

Write ONE authentic post as {agent['name']}. Output ONLY the post content."""

                try:
                    response = await call_claude(system_prompt, user_prompt, max_tokens=200)
                    content = response.strip()
                    
                    # Save post
                    post = {
                        "session_id": session_id,
                        "round": round_num,
                        "agent_id": agent["id"],
                        "agent_name": agent["name"],
                        "agent_emoji": agent.get("avatar_emoji", "🧑"),
                        "platform": platform,
                        "content": content,
                        "post_type": "post",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.sim_posts.insert_one(post)
                    
                    # Update agent memory
                    agent["memories"] = agent.get("memories", [])[-9:] + [f"I posted: {content[:100]}"]
                    
                except Exception as e:
                    logger.error(f"Error generating post for {agent['name']}: {e}")
                    continue
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
            
            # Generate some replies
            all_posts = await db.sim_posts.find({"session_id": session_id, "round": round_num}).to_list(100)
            if all_posts and len(active_agents) >= 2:
                reply_agents = random.sample(active_agents, min(2, len(active_agents)))
                target_posts = random.sample(all_posts, min(2, len(all_posts)))
                
                for i, agent in enumerate(reply_agents):
                    if i >= len(target_posts):
                        break
                    target_post = target_posts[i]
                    if target_post["agent_id"] == agent["id"]:
                        continue
                    
                    platform = target_post["platform"]
                    system_prompt = f"""You are playing the role of {agent['name']}. You're replying to someone else's post. Stay in character and respond authentically."""
                    
                    user_prompt = f"""You are: {agent['name']} ({agent['occupation']})
Personality: {agent['personality_type']}
You're replying to this post by {target_post['agent_name']}: "{target_post['content']}"
Platform: {platform}
Write a brief reply (1-2 sentences). Output ONLY the reply content."""

                    try:
                        response = await call_claude(system_prompt, user_prompt, max_tokens=150)
                        reply_content = response.strip()
                        
                        reply = {
                            "session_id": session_id,
                            "round": round_num,
                            "agent_id": agent["id"],
                            "agent_name": agent["name"],
                            "agent_emoji": agent.get("avatar_emoji", "🧑"),
                            "platform": platform,
                            "content": reply_content,
                            "post_type": "reply",
                            "reply_to": target_post["agent_name"],
                            "created_at": datetime.now(timezone.utc).isoformat()
                        }
                        await db.sim_posts.insert_one(reply)
                    except Exception as e:
                        logger.error(f"Error generating reply: {e}")
                    
                    await asyncio.sleep(0.3)
        
        # Update agents with final memories
        await db.sessions.update_one(
            {"id": session_id},
            {
                "$set": {
                    "status": "simulation_done",
                    "agents_json": json.dumps(agents),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Simulation error: {e}")
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
        "total_rounds": session.get("total_rounds", 0)
    }


@api_router.get("/sessions/{session_id}/posts")
async def get_posts(session_id: str):
    """Get all simulation posts"""
    posts = await db.sim_posts.find(
        {"session_id": session_id},
        {"_id": 0}
    ).sort([("round", 1), ("created_at", 1)]).to_list(1000)
    
    return {"posts": posts}


@api_router.post("/sessions/{session_id}/generate-report")
async def generate_report(session_id: str):
    """Generate prediction report from simulation"""
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("status") not in ["simulation_done", "complete"]:
        raise HTTPException(status_code=400, detail="Simulation not complete")
    
    agents = json.loads(session["agents_json"])
    graph = json.loads(session["graph_json"])
    query = session["prediction_query"]
    
    # Get all posts
    posts = await db.sim_posts.find({"session_id": session_id}).sort([("round", 1), ("created_at", 1)]).to_list(1000)
    
    # Build transcript (capped at 8000 chars)
    transcript_parts = []
    for post in posts:
        entry = f"[Round {post['round']}][{post['platform']}][{post['post_type'].upper()}] {post['agent_name']}: {post['content']}"
        transcript_parts.append(entry)
    
    full_transcript = "\n".join(transcript_parts)
    if len(full_transcript) > TRANSCRIPT_CAP:
        first_part = full_transcript[:3000]
        last_part = full_transcript[-5000:]
        full_transcript = first_part + "\n...[truncated]...\n" + last_part
    
    # Build agents summary
    agents_summary = "\n".join([
        f"- {a['name']} ({a['occupation']}) [{a['personality_type']}]: {a['initial_stance']}"
        for a in agents
    ])
    
    total_rounds = session.get("total_rounds", 5)
    
    system_prompt = """You are a senior analyst who just observed a multi-agent social simulation. Produce a rigorous prediction report. Respond ONLY with valid JSON, no markdown fences."""
    
    user_prompt = f"""Prediction Question: {query}
World Summary: {graph.get('summary', '')}
Themes: {', '.join(graph.get('themes', []))}
Agents ({len(agents)} total):
{agents_summary}

Simulation transcript ({total_rounds} rounds):
{full_transcript}

Return JSON:
{{
  "executive_summary": "3-4 sentence high-level answer",
  "prediction": {{
    "outcome": "Most likely predicted outcome",
    "confidence": "High|Medium|Low",
    "confidence_score": 0.72,
    "timeframe": "e.g. next 3-6 months"
  }},
  "opinion_landscape": {{
    "dominant_sentiment": "positive|negative|divided|uncertain",
    "support_percentage": 45,
    "opposition_percentage": 38,
    "undecided_percentage": 17,
    "key_factions": [
      {{
        "name": "Faction Name",
        "size": "Large|Medium|Small",
        "stance": "Their position",
        "key_arguments": ["arg1", "arg2"]
      }}
    ]
  }},
  "key_turning_points": [
    {{"round": 2, "description": "What shifted", "impact": "How dynamics changed"}}
  ],
  "emergent_patterns": ["Pattern that emerged from agent interactions"],
  "risk_factors": [
    {{"factor": "Risk name", "likelihood": "High|Medium|Low", "impact": "Description"}}
  ],
  "alternative_scenarios": [
    {{"scenario": "Title", "probability": 0.25, "conditions": "What would trigger this"}}
  ],
  "agent_highlights": [
    {{"agent_name": "Name", "role_in_simulation": "How they influenced dynamics", "notable_quote": "Their most impactful post"}}
  ]
}}"""

    try:
        response = await call_claude(system_prompt, user_prompt, max_tokens=3000)
        cleaned = clean_json_response(response)
        report = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse report from AI response")
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")
    
    await db.sessions.update_one(
        {"id": session_id},
        {
            "$set": {
                "status": "complete",
                "report_json": json.dumps(report),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
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
        """Sanitize text for PDF output"""
        if not text:
            return "N/A"
        text = str(text).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        # Remove any non-printable characters
        text = ''.join(c if c.isprintable() or c == ' ' else '' for c in text)
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
        response = await call_claude(system_prompt, user_prompt, max_tokens=400)
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
