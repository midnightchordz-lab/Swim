"""Report Agent - Generates structured prediction reports with GraphRAG-enhanced context."""
import json
import logging
from services.agents.graph_agent import generate_report_context

logger = logging.getLogger(__name__)

TRANSCRIPT_CAP = 8000


async def run(agents: list, graph: dict, posts: list, prediction_query: str,
              round_narratives: list, total_rounds: int, call_claude_fn) -> dict:
    """Generate a prediction report incorporating simulation story arc."""

    # Build transcript (capped)
    transcript_parts = []
    for post in posts:
        entry = f"[Round {post['round']}][{post['platform']}][{post['post_type'].upper()}] {post['agent_name']}: {post['content']}"
        transcript_parts.append(entry)

    full_transcript = "\n".join(transcript_parts)
    if len(full_transcript) > TRANSCRIPT_CAP:
        first_part = full_transcript[:3000]
        last_part = full_transcript[-5000:]
        full_transcript = first_part + "\n...[truncated]...\n" + last_part

    agents_summary = "\n".join([
        f"- {a['name']} ({a['occupation']}) [{a['personality_type']}]: {a['initial_stance']}"
        for a in agents
    ])

    # Build narrative arc
    narrative_arc = "\n".join(round_narratives) if round_narratives else "No round narratives available."

    # GraphRAG-enhanced report context
    graph_report_context = generate_report_context(graph)

    system_prompt = """You are a senior analyst who just observed a multi-agent social simulation. Produce a rigorous prediction report. Respond ONLY with valid JSON, no markdown fences."""

    user_prompt = f"""Prediction Question: {prediction_query}

{graph_report_context}

Agents ({len(agents)} total):
{agents_summary}

Simulation story arc:
{narrative_arc}

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

    from services.agents.common import clean_json
    response = await call_claude_fn(system_prompt, user_prompt, max_tokens=1500)
    return json.loads(clean_json(response))
