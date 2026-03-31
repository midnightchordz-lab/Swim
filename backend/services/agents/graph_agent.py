"""Graph Agent - Knowledge graph extraction with GraphRAG Level 1 + Level 2 capabilities.

Level 1: Enhanced entity & relationship extraction (uncapped, with importance, tensions, hooks)
Level 2: Per-agent GraphRAG retrieval for grounded simulation posts
"""
import json
import logging

logger = logging.getLogger(__name__)

# ─── LEVEL 1: ENHANCED GRAPH EXTRACTION ────────────────────────────────────────

GRAPH_EXTRACTION_SYSTEM = """You are an expert knowledge graph extraction specialist.
Your job is to extract EVERY entity and relationship present in the content.
Never truncate, never limit, never summarise away details.
A rich, complete graph produces a realistic simulation.
A sparse graph produces generic, hallucinated agent posts.
Return ONLY valid JSON. No markdown. No extra text."""


def build_graph_extraction_prompt(content: str, topic: str = "") -> str:
    """Build a prompt for entity/relationship extraction optimized for speed."""
    return f"""Extract a knowledge graph from this content. Return ONLY valid JSON.

Content:
{content[:3000]}

{"Topic: " + topic if topic else ""}

RULES:
- Extract 15-30 key entities (people, organizations, countries, companies, policies, events, concepts, metrics)
- Extract relationships between them
- Importance: High = central, Medium = significant, Low = peripheral

Return JSON:
{{
  "summary": "2-3 sentence overview",
  "themes": ["theme1", "theme2", "theme3", "theme4"],
  "entities": [
    {{
      "id": "snake_case_id",
      "name": "Entity Name",
      "type": "Person|Organization|Country|Company|Policy|Event|Concept|Metric|Asset",
      "description": "Brief description",
      "importance": "High|Medium|Low"
    }}
  ],
  "relationships": [
    {{
      "source_id": "entity_id_1",
      "target_id": "entity_id_2",
      "type": "relationship_type",
      "description": "brief description"
    }}
  ],
  "key_tensions": [
    {{
      "tension": "core conflict",
      "entities_involved": ["id1", "id2"],
      "stakes": "what is at stake"
    }}
  ],
  "agent_diversity_hints": ["viewpoint1", "viewpoint2", "viewpoint3"]
}}"""


# ─── GRAPH POST-PROCESSING (entity index + adjacency map) ──────────────────────

def process_graph_response(raw_graph: dict) -> dict:
    """Post-process the raw graph to add entity_index, adjacency_map, and counts."""
    entities = raw_graph.get("entities", [])
    relations = raw_graph.get("relationships", [])

    # Normalize relationship keys: accept both "source"/"target" and "source_id"/"target_id"
    for r in relations:
        if "source_id" not in r and "source" in r:
            r["source_id"] = r["source"]
        if "target_id" not in r and "target" in r:
            r["target_id"] = r["target"]

    # Build entity lookup by ID and by lowercased name
    entity_index = {}
    for e in entities:
        eid = e.get("id", "")
        name = e.get("name", "")
        if eid:
            entity_index[eid] = e
        if name:
            entity_index[name.lower()] = e

    # Build adjacency map: entity_id → [related entity dicts]
    adjacency = {}
    for r in relations:
        src = r.get("source_id", "")
        tgt = r.get("target_id", "")
        rel = r.get("type", "related_to")
        desc = r.get("description", "")

        if src not in adjacency:
            adjacency[src] = []
        if tgt not in adjacency:
            adjacency[tgt] = []

        src_entity = entity_index.get(src, {"name": src, "type": "Unknown"})
        tgt_entity = entity_index.get(tgt, {"name": tgt, "type": "Unknown"})

        adjacency[src].append({
            "entity": tgt_entity,
            "relationship": rel,
            "description": desc,
            "direction": "outgoing"
        })
        adjacency[tgt].append({
            "entity": src_entity,
            "relationship": rel,
            "description": desc,
            "direction": "incoming"
        })

    raw_graph["entity_index"] = entity_index
    raw_graph["adjacency_map"] = adjacency
    raw_graph["entity_count"] = len(entities)
    raw_graph["relationship_count"] = len(relations)

    return raw_graph


def strip_runtime_fields(graph: dict) -> dict:
    """Return a copy of the graph without heavy runtime indices (safe for JSON/MongoDB storage)."""
    clean = {k: v for k, v in graph.items() if k not in ("entity_index", "adjacency_map")}
    return clean


def ensure_indices(graph: dict) -> dict:
    """Rebuild entity_index and adjacency_map if not present (after loading from DB)."""
    if "entity_index" not in graph or "adjacency_map" not in graph:
        graph = process_graph_response(graph)
    return graph


# ─── LEVEL 2: PER-AGENT GRAPHRAG RETRIEVAL ──────────────────────────────────────

OCCUPATION_ENTITY_TYPES = {
    "trader":     ["Asset", "Instrument", "Metric", "Company"],
    "investor":   ["Asset", "Instrument", "Metric", "Company", "Policy"],
    "analyst":    ["Metric", "Policy", "Organization", "Company", "Concept"],
    "politician": ["Person", "Organization", "Policy", "Law", "Country"],
    "journalist": ["Event", "Person", "Organization", "Policy"],
    "economist":  ["Metric", "Policy", "Concept", "Organization", "Country"],
    "activist":   ["Policy", "Law", "Event", "Concept", "Organization"],
    "expert":     ["Concept", "Policy", "Metric", "Organization"],
}


def retrieve_graph_context(graph: dict, agent: dict, recent_posts: list,
                           round_num: int, max_entities: int = 8) -> str:
    """GraphRAG retrieval: fetch relevant knowledge-graph context for a specific agent.

    Selects entities based on importance, recent post mentions, and agent occupation,
    then formats them with their key relationships and relevant tensions.
    """
    entity_index = graph.get("entity_index", {})  # noqa: F841 — retained for potential future use
    adjacency_map = graph.get("adjacency_map", {})
    all_entities = graph.get("entities", [])

    if not all_entities:
        return graph.get("summary", "No specific knowledge graph available.")

    # Step 1: High-importance entities (always included)
    high_importance = [e for e in all_entities if e.get("importance") == "High"][:3]

    # Step 2: Entities mentioned in recent posts
    recent_entity_hits = []
    recent_text = " ".join([p.get("content", "") for p in recent_posts[-5:]])
    for entity in all_entities:
        name = entity.get("name", "")
        if name and name.lower() in recent_text.lower():
            if entity not in high_importance:
                recent_entity_hits.append(entity)

    # Step 3: Entities relevant to agent's occupation
    occupation = agent.get("occupation", "").lower()
    relevant_types = []
    for occ_key, types in OCCUPATION_ENTITY_TYPES.items():
        if occ_key in occupation:
            relevant_types.extend(types)
            break
    if not relevant_types:
        relevant_types = ["Event", "Policy", "Metric", "Organization", "Person"]

    agent_relevant = [
        e for e in all_entities
        if e.get("type") in relevant_types
        and e not in high_importance
        and e not in recent_entity_hits
    ]

    # Step 4: Combine and limit
    selected = high_importance + recent_entity_hits[:3] + agent_relevant[:2]
    selected = selected[:max_entities]
    if not selected:
        selected = all_entities[:max_entities]

    # Step 5: Format entities + their key relationships
    context_parts = []
    seen_relationships = set()

    for entity in selected:
        eid = entity.get("id", "")
        name = entity.get("name", "")
        desc = entity.get("description", "")
        etype = entity.get("type", "")

        context_parts.append(f"* {name} ({etype}): {desc}")

        neighbors = adjacency_map.get(eid, [])[:2]
        for neighbor in neighbors:
            rel_key = f"{eid}_{neighbor.get('entity', {}).get('id', '')}_{neighbor.get('direction', '')}"
            if rel_key not in seen_relationships:
                seen_relationships.add(rel_key)
                neighbor_name = neighbor.get("entity", {}).get("name", "")
                rel_type = neighbor.get("relationship", "related to")
                rel_desc = neighbor.get("description", "")
                if neighbor_name and rel_desc:
                    context_parts.append(f"  -> {rel_type} {neighbor_name}: {rel_desc}")

    # Step 6: Add relevant tensions
    tensions = graph.get("key_tensions", [])
    selected_ids = {e.get("id") for e in selected}
    relevant_tensions = [
        t.get("tension", "")
        for t in tensions
        if set(t.get("entities_involved", [])) & selected_ids
    ]

    context = "\n".join(context_parts)
    if relevant_tensions:
        context += "\n\nKey tensions:\n" + "\n".join(f"* {t}" for t in relevant_tensions[:2])

    return context


# ─── HELPER: AGENT GENERATION CONTEXT ───────────────────────────────────────────

def build_agent_generation_context(graph: dict, num_agents: int) -> str:
    """Build a rich context string for persona generation using graph data."""
    entities = graph.get("entities", [])
    hints = graph.get("agent_diversity_hints", [])
    themes = graph.get("themes", [])
    tensions = graph.get("key_tensions", [])

    people = [e for e in entities if e.get("type") == "Person"][:5]
    orgs = [e for e in entities if e.get("type") in ["Organization", "Company"]][:5]
    concepts = [e for e in entities if e.get("type") in ["Concept", "Policy"]][:5]
    metrics = [e for e in entities if e.get("type") == "Metric"][:5]

    return f"""KNOWLEDGE GRAPH SUMMARY:
Themes: {', '.join(themes[:6])}
Total entities: {len(entities)} | Relationships: {len(graph.get('relationships', []))}

Key people: {', '.join([p['name'] for p in people]) or 'N/A'}
Key organizations: {', '.join([o['name'] for o in orgs]) or 'N/A'}
Key concepts/policies: {', '.join([c['name'] for c in concepts]) or 'N/A'}
Key metrics at stake: {', '.join([m['name'] for m in metrics]) or 'N/A'}

Core tensions:
{chr(10).join([f"- {t.get('tension', '')}" for t in tensions[:4]]) or '- None identified'}

Suggested diverse viewpoints:
{chr(10).join([f"- {h}" for h in hints[:8]]) or '- General public perspectives'}

AGENT GENERATION RULES:
1. Generate exactly {num_agents} agents.
2. Each agent must reference specific entities from the graph in their background and initial_stance.
3. Each agent initial_stance must take a specific position on a specific tension.
4. Vary occupations based on who would realistically care about this topic.
5. Include at least one agent per major faction implied by the tensions.
6. Make initial_stance concrete - reference actual entity names from the graph.
   BAD:  "I think the market will go down"
   GOOD: "With FII net selling and NIFTY below support, reducing exposure to IT heavyweights like Infosys and TCS"
"""


# ─── HELPER: REPORT GENERATION CONTEXT ──────────────────────────────────────────

def generate_report_context(graph: dict) -> str:
    """Build a rich context string for report generation using full graph."""
    entities = graph.get("entities", [])
    tensions = graph.get("key_tensions", [])
    high_entities = [e for e in entities if e.get("importance") == "High"]
    all_entity_names = [e["name"] for e in entities]

    return f"""FULL KNOWLEDGE GRAPH ({len(entities)} entities, {len(graph.get('relationships', []))} relationships):

High-importance entities:
{chr(10).join([f"* {e['name']} ({e['type']}): {e['description']}" for e in high_entities[:20]]) or '* None classified as high importance'}

All entities in scope:
{', '.join(all_entity_names)}

Core tensions:
{chr(10).join([f"* {t.get('tension', '')} (Stakes: {t.get('stakes', '')})" for t in tensions[:5]]) or '* None identified'}"""


# ─── MAIN EXTRACTION FUNCTIONS ──────────────────────────────────────────────────

async def run(intel_brief: dict, prediction_query: str, call_claude_fn) -> dict:
    """Extract a knowledge graph from an intel brief using enhanced L1 prompts."""

    summary = intel_brief.get("summary", "")
    themes = intel_brief.get("themes", [])
    stakeholders = intel_brief.get("stakeholders", [])

    content = f"""Intelligence Brief Summary:
{summary[:3000]}

Themes: {', '.join(themes)}
Key Stakeholders: {json.dumps(stakeholders[:6])}
Prediction Question: {prediction_query}"""

    from services.agents.common import clean_json
    response = await call_claude_fn(
        GRAPH_EXTRACTION_SYSTEM,
        build_graph_extraction_prompt(content, prediction_query),
        max_tokens=1000
    )
    graph = json.loads(clean_json(response))

    # Preserve intel brief metadata
    if not graph.get("summary"):
        graph["summary"] = summary
    if not graph.get("themes"):
        graph["themes"] = themes

    # Post-process: build indices and counts
    graph = process_graph_response(graph)
    return graph


async def run_from_document(text: str, prediction_query: str, call_claude_fn,
                            image_data: dict = None) -> dict:
    """Extract knowledge graph from uploaded document text or image using enhanced L1 prompts."""

    if image_data:
        system_prompt = GRAPH_EXTRACTION_SYSTEM
        graph_prompt = build_graph_extraction_prompt("(See image content)", prediction_query)
        user_prompt = f"Analyze this image carefully and extract a knowledge graph.\nPrediction Question: {prediction_query}\n\n{graph_prompt}"

        from services.agents.common import clean_json
        response = await call_claude_fn(system_prompt, user_prompt, max_tokens=1000, image_data=image_data)
        graph = json.loads(clean_json(response))
    else:
        from services.agents.common import clean_json
        response = await call_claude_fn(
            GRAPH_EXTRACTION_SYSTEM,
            build_graph_extraction_prompt(text, prediction_query),
            max_tokens=1000
        )
        graph = json.loads(clean_json(response))

    # Post-process: build indices and counts
    graph = process_graph_response(graph)
    return graph
