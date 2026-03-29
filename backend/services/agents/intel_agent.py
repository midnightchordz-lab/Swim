"""Intel Agent - Focused on intelligence gathering, news synthesis, and brief generation."""
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def run(topic: str, horizon: str, prediction_query: str,
              web_context: str, yahoo_headlines: str, financial_context: str,
              call_claude_fn) -> dict:
    """Generate a structured intelligence brief from gathered data sources."""

    system_prompt = """You are an intelligence analyst creating a brief on a current topic. Based on the web data provided, create a structured intelligence brief of 800-1200 words. 
CRITICAL: If real-time market data is provided (marked as VERIFIED), you MUST use those exact price figures in your analysis. Do NOT invent or estimate prices — use only the verified data provided.
Respond ONLY with valid JSON, no markdown fences."""

    user_prompt = f"""Topic: {topic}
Prediction Horizon: {horizon}
Prediction Question: {prediction_query}
{financial_context}
Latest headlines for {topic}:
{yahoo_headlines}

Live Web Data:
{web_context}

Using these as your primary source, write a comprehensive 800-word intel brief covering all angles relevant to the prediction horizon: {horizon}

IMPORTANT: If VERIFIED REAL-TIME MARKET DATA is provided above, use those exact prices and figures in your summary and data_points. Do NOT make up different numbers.

Return JSON:
{{
  "summary": "Detailed 800-1200 word executive summary synthesizing all findings, covering current state, key developments, stakeholder positions, data trends, and outlook. Use verified market prices if available.",
  "key_developments": ["development 1", "development 2", "development 3", "development 4", "development 5"],
  "stakeholders": [
    {{"name": "Stakeholder Name", "position": "Their current stance or action", "influence": "high|medium|low"}}
  ],
  "data_points": [
    {{"metric": "Key metric or stat", "value": "Current value", "trend": "up|down|stable"}}
  ],
  "themes": ["theme1", "theme2", "theme3", "theme4", "theme5"],
  "uncertainty_factors": ["factor that could change outcomes"],
  "confidence_level": "high|medium|low"
}}"""

    from services.agents.common import clean_json
    response = await call_claude_fn(system_prompt, user_prompt, max_tokens=800)
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
