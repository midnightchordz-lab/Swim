"""Intel Agent - Focused on intelligence gathering, news synthesis, and brief generation."""
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def run(topic: str, horizon: str, prediction_query: str,
              web_context: str, yahoo_headlines: str, financial_context: str,
              call_claude_fn) -> dict:
    """Generate a structured intelligence brief from gathered data sources."""

    system_prompt = """You are an intelligence analyst. Create a concise structured brief on the topic. If real-time market data is provided (VERIFIED), use those exact figures. Respond ONLY with valid JSON."""

    user_prompt = f"""Topic: {topic}
Horizon: {horizon}
Question: {prediction_query}
{financial_context}
Headlines:
{yahoo_headlines[:1500]}

Web Data:
{web_context[:2000]}

Write a focused 300-400 word intel brief.
Return JSON:
{{
  "summary": "300-400 word executive summary with current state, key developments, and outlook",
  "key_developments": ["dev1", "dev2", "dev3"],
  "stakeholders": [{{"name": "Name", "position": "stance", "influence": "high|medium|low"}}],
  "data_points": [{{"metric": "key stat", "value": "value", "trend": "up|down|stable"}}],
  "themes": ["theme1", "theme2", "theme3"],
  "uncertainty_factors": ["factor1"],
  "confidence_level": "high|medium|low"
}}"""

    from services.agents.common import clean_json
    response = await call_claude_fn(system_prompt, user_prompt, max_tokens=500)
    return json.loads(clean_json(response))


async def rewrite(brief: dict, feedback: str, topic: str, call_claude_fn) -> dict:
    """Rewrite a biased brief incorporating critic feedback."""
    system_prompt = """You are an intelligence analyst rewriting a brief to reduce bias. Respond ONLY with valid JSON, no markdown fences."""
    user_prompt = f"""The following intelligence brief about "{topic}" was flagged for bias.

Critic Feedback: {feedback}

Original brief summary (first 1500 chars):
{brief.get('summary', '')[:1500]}

Rewrite the summary to be more balanced and address the feedback. Keep the same JSON structure.
Return JSON with the same keys as the original brief:
{{
  "summary": "Rewritten balanced 800-1200 word summary",
  "key_developments": {json.dumps(brief.get('key_developments', []))},
  "stakeholders": {json.dumps(brief.get('stakeholders', []))},
  "data_points": {json.dumps(brief.get('data_points', []))},
  "themes": {json.dumps(brief.get('themes', []))},
  "uncertainty_factors": {json.dumps(brief.get('uncertainty_factors', []))},
  "confidence_level": "{brief.get('confidence_level', 'medium')}"
}}"""

    from services.agents.common import clean_json
    response = await call_claude_fn(system_prompt, user_prompt, max_tokens=800)
    rewritten = json.loads(clean_json(response))
    # Preserve original fields that weren't rewritten
    for key in brief:
        if key not in rewritten:
            rewritten[key] = brief[key]
    return rewritten
