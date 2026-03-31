"""Graph Agent - Knowledge graph extraction with GraphRAG Level 1 + Level 2 capabilities.

Level 1: Enhanced entity & relationship extraction with importance, tensions, hooks
Level 2: Per-agent GraphRAG retrieval for grounded simulation posts
Level 3: Multi-chunk extraction + multi-source merge (brief + Twitter + Reddit)
"""
import json
import logging
import asyncio
import re

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


# ─── CHUNKING & MULTI-SOURCE MERGE ──────────────────────────────────────────────

def chunk_content(text: str, chunk_size: int = 2500, overlap: int = 300) -> list:
    """Split content into overlapping chunks for multi-pass graph extraction.
    Overlap ensures entities at chunk boundaries are captured with context."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            last_period = text.rfind('.', start, end)
            if last_period > start + chunk_size // 2:
                end = last_period + 1
        chunks.append(text[start:end].strip())
        start = end - overlap
        if start >= len(text):
            break

    return [c for c in chunks if len(c) > 100]


def merge_graph_sources(graphs: list) -> dict:
    """Merge multiple partial graphs into one unified graph, deduplicating entities by name."""
    all_entities = []
    all_relationships = []
    seen_entity_names = {}

    for g in graphs:
        for entity in g.get("entities", []):
            name_key = entity.get("name", "").lower().strip()
            if not name_key:
                continue
            if name_key in seen_entity_names:
                existing = seen_entity_names[name_key]
                imp_rank = {"High": 0, "Medium": 1, "Low": 2}
                if imp_rank.get(entity.get("importance"), 2) < imp_rank.get(existing.get("importance"), 2):
                    existing["importance"] = entity["importance"]
                if entity.get("source") and entity["source"] != existing.get("source"):
                    existing["source"] = existing.get("source", "") + "+" + entity["source"]
            else:
                seen_entity_names[name_key] = entity
                all_entities.append(entity)

        for rel in g.get("relationships", []):
            all_relationships.append(rel)

    valid_ids = {e.get("id") for e in all_entities}
    deduped_rels = []
    seen_rel_keys = set()
    for rel in all_relationships:
        src = rel.get("source_id", rel.get("source", ""))
        tgt = rel.get("target_id", rel.get("target", ""))
        if src in valid_ids and tgt in valid_ids:
            rel_key = f"{src}_{tgt}_{rel.get('type', '')}"
            if rel_key not in seen_rel_keys:
                seen_rel_keys.add(rel_key)
                deduped_rels.append(rel)

    return {"entities": all_entities, "relationships": deduped_rels}


async def chunk_and_extract(content: str, topic: str, call_fn, max_chunks: int = 3) -> dict:
    """Multi-chunk graph extraction. Splits content, extracts per chunk, merges.
    Each chunk gets full LLM attention for richer extraction than single-pass."""
    from services.agents.common import clean_json

    chunks = chunk_content(content, chunk_size=2500, overlap=300)
    chunks = chunks[:max_chunks]

    if len(chunks) <= 1:
        response = await call_fn(
            GRAPH_EXTRACTION_SYSTEM,
            build_graph_extraction_prompt(content, topic),
            max_tokens=1000
        )
        return json.loads(clean_json(response))

    logger.info(f"[ChunkExtract] {len(chunks)} chunks for topic: {topic[:40]}")
    partial_graphs = []

    for i, chunk in enumerate(chunks):
        chunk_label = f"chunk {i+1}/{len(chunks)}"
        try:
            prompt = build_graph_extraction_prompt(chunk, topic)
            response = await call_fn(
                GRAPH_EXTRACTION_SYSTEM,
                f"This is {chunk_label} of a larger document about: {topic}\n\n{prompt}",
                max_tokens=1000
            )
            partial = json.loads(clean_json(response))
            for e in partial.get("entities", []):
                e["chunk"] = i
            partial_graphs.append(partial)
            logger.info(f"[ChunkExtract] {chunk_label}: {len(partial.get('entities', []))} entities")
        except Exception as e:
            logger.error(f"[ChunkExtract] {chunk_label} failed: {e}")
        await asyncio.sleep(0.2)

    if not partial_graphs:
        logger.warning("[ChunkExtract] All chunks failed, single-pass fallback")
        response = await call_fn(
            GRAPH_EXTRACTION_SYSTEM,
            build_graph_extraction_prompt(content[:2000], topic),
            max_tokens=1000
        )
        return json.loads(clean_json(response))

    merged = merge_graph_sources(partial_graphs)
    if partial_graphs:
        merged["summary"] = partial_graphs[0].get("summary", "")
        merged["themes"] = partial_graphs[0].get("themes", [])
        merged["key_tensions"] = partial_graphs[0].get("key_tensions", [])
        merged["agent_diversity_hints"] = partial_graphs[0].get("agent_diversity_hints", [])

    logger.info(f"[ChunkExtract] Merged: {len(merged['entities'])} entities, {len(merged['relationships'])} rels from {len(partial_graphs)} chunks")
    return merged


async def extract_from_social(posts: list, source_label: str, topic: str, call_fn) -> dict:
    """Extract entities from social media posts (Twitter/Reddit)."""
    from services.agents.common import clean_json

    if not posts:
        return {"entities": [], "relationships": []}

    text = "\n".join([
        f"{p.get('author', 'user')}: {p.get('content', p.get('text', ''))}"
        for p in posts[:20]
    ])[:2500]

    try:
        response = await call_fn(
            GRAPH_EXTRACTION_SYSTEM,
            f"Extract entities and relationships from these {source_label} posts about: {topic}\n\n{text}\n\nReturn JSON with entities and relationships arrays only.",
            max_tokens=800
        )
        graph = json.loads(clean_json(response))
        for e in graph.get("entities", []):
            e["source"] = source_label
        logger.info(f"[SocialExtract] {source_label}: {len(graph.get('entities', []))} entities")
        return graph
    except Exception as e:
        logger.error(f"[SocialExtract] {source_label} failed: {e}")
        return {"entities": [], "relationships": []}



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

async def run(intel_brief: dict, prediction_query: str, call_claude_fn,
              social_posts: list = None, progress_fn=None) -> dict:
    """Extract a knowledge graph from an intel brief. Single-pass for speed and memory efficiency."""
    from services.agents.common import clean_json

    summary = intel_brief.get("summary", "")
    themes = intel_brief.get("themes", [])
    stakeholders = intel_brief.get("stakeholders", [])

    content = f"Intelligence Brief Summary:\n{summary[:3000]}\n\nThemes: {', '.join(themes)}\nKey Stakeholders: {json.dumps(stakeholders[:6])}\nPrediction Question: {prediction_query}"

    if progress_fn:
        await progress_fn("Extracting knowledge graph...")

    response = await call_claude_fn(
        GRAPH_EXTRACTION_SYSTEM,
        build_graph_extraction_prompt(content, prediction_query),
        max_tokens=1000
    )
    graph = json.loads(clean_json(response))

    for e in graph.get("entities", []):
        if "source" not in e:
            e["source"] = "brief"

    if not graph.get("summary"):
        graph["summary"] = summary
    if not graph.get("themes"):
        graph["themes"] = themes

    graph = process_graph_response(graph)

    if progress_fn:
        await progress_fn(f"Graph complete: {graph['entity_count']} entities, {graph['relationship_count']} rels")

    logger.info(f"[GraphAgent] Final: {graph['entity_count']} entities, {graph['relationship_count']} rels")
    return graph


async def run_from_document(text: str, prediction_query: str, call_claude_fn,
                            image_data: dict = None) -> dict:
    """Extract knowledge graph from uploaded document text or image."""
    from services.agents.common import clean_json

    if image_data:
        graph_prompt = build_graph_extraction_prompt("(See image content)", prediction_query)
        user_prompt = f"Analyze this image and extract a knowledge graph.\nPrediction Question: {prediction_query}\n\n{graph_prompt}"
        response = await call_claude_fn(GRAPH_EXTRACTION_SYSTEM, user_prompt, max_tokens=1000, image_data=image_data)
    else:
        response = await call_claude_fn(
            GRAPH_EXTRACTION_SYSTEM,
            build_graph_extraction_prompt(text[:3000], prediction_query),
            max_tokens=1000
        )

    graph = json.loads(clean_json(response))
    graph = process_graph_response(graph)
    return graph
