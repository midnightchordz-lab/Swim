"""Persona Agent - Generates diverse AI agent personas with demographic + ideological diversity."""
import json
import logging
from collections import Counter

logger = logging.getLogger(__name__)

REQUIRED_TYPES = {"Skeptic", "Expert", "Contrarian", "Activist"}
ALL_TYPES = ["Skeptic", "Optimist", "Insider", "Contrarian", "Expert", "Neutral", "Activist", "Pragmatist"]

CATEGORY_GUIDANCE = {
    "financial": "Include: financial analysts, retail investors, institutional traders, economists, financial journalists, fintech founders",
    "political": "Include: political analysts, voters from different demographics, campaign strategists, journalists, activists, lobbyists",
    "geopolitical": "Include: foreign policy experts, military analysts, diplomats, regional specialists, journalists, affected citizens",
    "sports": "Include: sports analysts, fans, coaches, former players, sports journalists, betting analysts",
    "tech": "Include: tech analysts, startup founders, engineers, VCs, tech journalists, early adopters, skeptics",
    "social_cultural": "Include: cultural critics, influencers, activists, everyday people, researchers, journalists",
}


async def run(graph: dict, prediction_query: str, num_agents: int,
              topic_category: str, data_mode: str, intel_context: str,
              call_claude_fn) -> list:
    """Generate diverse agent personas based on the knowledge graph."""

    entities_summary = json.dumps([
        {"name": e["name"], "type": e["type"]}
        for e in graph.get("entities", [])[:20]
    ])
    guidance = CATEGORY_GUIDANCE.get(topic_category, "Include diverse perspectives from various backgrounds")

    system_prompt = """You are a simulation designer. Create realistic agent personas for a social prediction simulation. Respond ONLY with valid JSON, no markdown fences."""

    user_prompt = f"""World: {graph.get('summary', '')[:800]}
Themes: {', '.join(graph.get('themes', []))}
Prediction: {prediction_query}

Generate exactly {num_agents} diverse agents. For each provide ONLY:
- name (realistic full name)
- age (18-70)
- occupation (specific job title)
- background (one sentence, unique to this person)
- personality_type (choose: Skeptic/Optimist/Insider/Contrarian/Expert/Neutral/Activist/Pragmatist)
- influence_level (1-10)
- initial_stance (one sentence, their position on the topic)
- avatar_emoji (single relevant emoji)

DO NOT write communication_style or platform_preference — derived from personality_type.
Vary demographics, professions, income levels. No two agents the same occupation.
CRITICAL: include at least one each of Skeptic, Expert, Contrarian, and Activist.

Return JSON: {{"agents": [...]}}"""

    from services.agents.common import clean_json
    response = await call_claude_fn(system_prompt, user_prompt, max_tokens=2000)
    agents_data = json.loads(clean_json(response))
    agents = agents_data.get("agents", [])

    for i, agent in enumerate(agents):
        agent.setdefault("id", f"agent_{i+1}")
        agent["memories"] = []

    return agents


async def rebalance(agents: list, graph: dict, prediction_query: str,
                    call_claude_fn) -> list:
    """Add missing personality types to ensure at least 1 of each required type."""
    existing_types = {a.get("personality_type") for a in agents}
    missing = REQUIRED_TYPES - existing_types

    if not missing:
        return agents

    logger.info(f"Persona agent: rebalancing — missing types: {missing}")

    system_prompt = """You are a simulation designer. Create specific agent personas to fill missing personality gaps. Respond ONLY with valid JSON, no markdown fences."""

    user_prompt = f"""The current simulation is missing these personality types: {', '.join(missing)}

World Context: {graph.get('summary', '')[:800]}
Prediction Question: {prediction_query}

Create exactly {len(missing)} new agents, one for each missing type.
Return JSON:
{{
  "agents": [
    {{
      "id": "agent_rebalance_{i+1}",
      "name": "Full Name",
      "avatar_emoji": "single emoji",
      "age": 35,
      "occupation": "specific job",
      "background": "2-sentence backstory",
      "personality_type": "<one of: {', '.join(missing)}>",
      "initial_stance": "Their specific position (1-2 sentences)",
      "influence_level": 7,
      "platform_preference": "Twitter|Reddit",
      "communication_style": "analytical|emotional|aggressive|diplomatic|satirical|factual"
    }}
  ]
}}"""

    from services.agents.common import clean_json
    try:
        response = await call_claude_fn(system_prompt, user_prompt, max_tokens=1000)
        new_agents = json.loads(clean_json(response)).get("agents", [])
        for a in new_agents:
            a["memories"] = []
            a["id"] = f"agent_{len(agents) + 1}"
            agents.append(a)
        logger.info(f"Rebalanced: added {len(new_agents)} agents")
    except Exception as e:
        logger.warning(f"Rebalance failed: {e}")

    return agents
