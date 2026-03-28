"""Graph Agent - Focused on structured entity and relationship extraction."""
import json
import logging

logger = logging.getLogger(__name__)


async def run(intel_brief: dict, prediction_query: str, call_claude_fn) -> dict:
    """Extract a knowledge graph (entities + relationships) from an intel brief."""

    summary = intel_brief.get("summary", "")
    themes = intel_brief.get("themes", [])
    stakeholders = intel_brief.get("stakeholders", [])

    system_prompt = """You are a knowledge-graph extraction expert. Extract entities and relationships from the intelligence brief. Respond ONLY with valid JSON, no markdown fences."""

    user_prompt = f"""Intelligence Brief Summary:
{summary[:3000]}

Themes: {', '.join(themes)}
Key Stakeholders: {json.dumps(stakeholders[:8])}
Prediction Question: {prediction_query}

Return JSON:
{{
  "summary": "{summary[:200]}...",
  "themes": {json.dumps(themes)},
  "entities": [
    {{
      "id": "e1",
      "name": "Entity Name",
      "type": "person|organization|faction|concept|event",
      "description": "Brief description based on current data",
      "stance": "positive|negative|neutral|conflicted"
    }}
  ],
  "relationships": [
    {{"source": "e1", "target": "e2", "label": "relationship", "weight": 0.8}}
  ]
}}
Extract 10-20 entities and 15-30 relationships. Be granular — include specific people, organizations, events, and abstract concepts."""

    from services.agents.common import clean_json
    response = await call_claude_fn(system_prompt, user_prompt, max_tokens=3000)
    graph = json.loads(clean_json(response))

    # Validate: if too few entities, retry once with more explicit instruction
    if len(graph.get("entities", [])) < 6:
        logger.info("Graph agent: too few entities, retrying with more granular prompt")
        retry_prompt = f"""{user_prompt}

IMPORTANT: Your previous attempt only extracted {len(graph.get('entities', []))} entities. 
Extract at LEAST 10 entities. Be more granular — include specific people, sub-organizations, 
individual events, regulatory bodies, market instruments, and abstract forces like 'retail sentiment'."""

        response = await call_claude_fn(system_prompt, retry_prompt, max_tokens=3000)
        graph = json.loads(clean_json(response))

    # Preserve the full summary from intel brief
    graph["summary"] = summary
    graph["themes"] = themes
    return graph


async def run_from_document(text: str, prediction_query: str, call_claude_fn,
                            image_data: dict = None) -> dict:
    """Extract knowledge graph from uploaded document text or image."""

    system_prompt = """You are a knowledge-graph extraction expert. Given seed text (or an image) and a prediction question, extract entities and relationships. Respond ONLY with valid JSON, no markdown fences."""

    if image_data:
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
        user_prompt = f"""Seed Text: \"\"\"{text[:12000]}\"\"\"
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

    from services.agents.common import clean_json
    response = await call_claude_fn(system_prompt, user_prompt, max_tokens=3000, image_data=image_data)
    graph = json.loads(clean_json(response))

    if len(graph.get("entities", [])) < 6 and not image_data:
        logger.info("Graph agent (doc): too few entities, retrying")
        retry_prompt = user_prompt + f"\n\nIMPORTANT: Extract at LEAST 10 entities. Be more granular."
        response = await call_claude_fn(system_prompt, retry_prompt, max_tokens=3000)
        graph = json.loads(clean_json(response))

    return graph
