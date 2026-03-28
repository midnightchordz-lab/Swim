"""Orchestrator - Manages the full SwarmSim pipeline, coordinating 6 specialist agents."""
import json
import logging
from datetime import datetime, timezone

from services.agents import (
    intel_agent,
    graph_agent,
    persona_agent,
    sim_director,
    critic_agent,
    report_agent,
)

logger = logging.getLogger(__name__)


async def run_live_intel_pipeline(session_id: str, topic: str, horizon: str,
                                  prediction_query: str, web_context: str,
                                  yahoo_headlines: str, financial_context: str,
                                  financial_data: dict, call_claude_fn, db):
    """Run the Intel + Graph pipeline for live intelligence mode.
    Steps: Intel Agent → Critic check → Graph Agent"""

    state = {"pipeline_status": "intel"}

    # Step 1: Intel Agent generates brief
    logger.info(f"[Orchestrator] Step 1: Intel Agent for session {session_id}")
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {"live_progress": "Generating intelligence brief..."}}
    )

    intel_brief = await intel_agent.run(
        topic, horizon, prediction_query,
        web_context, yahoo_headlines, financial_context,
        call_claude_fn
    )
    state["intel_brief"] = intel_brief

    # Step 1b: Critic checks brief for bias
    logger.info(f"[Orchestrator] Step 1b: Critic checking brief bias")
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {"live_progress": "Evaluating brief quality..."}}
    )

    critique = await critic_agent.check_brief(
        intel_brief.get("summary", ""), call_claude_fn
    )
    state["brief_critique"] = critique

    if critique.get("bias_score", 0) > 7:
        logger.info(f"[Orchestrator] Brief bias_score={critique['bias_score']}, rewriting...")
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {"live_progress": "Rewriting brief to reduce bias..."}}
        )
        intel_brief = await intel_agent.rewrite(
            intel_brief, critique.get("feedback", ""), topic, call_claude_fn
        )
        state["intel_brief"] = intel_brief
        state["brief_rewritten"] = True

    # Inject verified financial data
    if financial_data and financial_data.get("has_data"):
        intel_brief["verified_market_data"] = financial_data["data"]

    # Step 2: Graph Agent extracts knowledge graph
    logger.info(f"[Orchestrator] Step 2: Graph Agent for session {session_id}")
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {"live_progress": "Extracting knowledge graph..."}}
    )

    graph = await graph_agent.run(intel_brief, prediction_query, call_claude_fn)
    state["graph"] = graph
    state["pipeline_status"] = "graph_ready"

    return state


async def run_agent_generation_pipeline(session_id: str, num_agents: int,
                                        call_claude_fn, db):
    """Run the Persona Agent pipeline with diversity check.
    Steps: Persona Agent → Critic diversity check → Rebalance if needed"""

    session = await db.sessions.find_one({"id": session_id})
    if not session:
        return None

    graph = json.loads(session["graph_json"])
    query = session["prediction_query"]
    data_mode = session.get("data_mode", "upload")
    topic = session.get("topic", "")

    # Import detect function
    from server import detect_topic_category
    topic_category = detect_topic_category(topic or query)

    intel_context = ""
    if data_mode == "live" and session.get("intel_brief"):
        brief = json.loads(session["intel_brief"])
        stakeholders = brief.get("stakeholders", [])
        if stakeholders:
            intel_context = f"\nKey Stakeholders from live data: {json.dumps(stakeholders[:5])}"

    # Step 3: Persona Agent generates agents
    logger.info(f"[Orchestrator] Step 3: Persona Agent ({num_agents} agents)")
    agents = await persona_agent.run(
        graph, query, num_agents, topic_category, data_mode, intel_context,
        call_claude_fn
    )

    # Step 3b: Critic scores diversity
    diversity = critic_agent.score_diversity(agents)
    logger.info(f"[Orchestrator] Diversity score: {diversity}")

    if diversity < 0.6:
        logger.info(f"[Orchestrator] Low diversity ({diversity}), rebalancing...")
        agents = await persona_agent.rebalance(agents, graph, query, call_claude_fn)
        diversity = critic_agent.score_diversity(agents)
        logger.info(f"[Orchestrator] Post-rebalance diversity: {diversity}")

    return {"agents": agents, "diversity_score": diversity}


async def run_simulation_pipeline(session_id: str, num_rounds: int,
                                  call_claude_fn, db):
    """Run the Simulation Director pipeline.
    Steps: Sim Director (with per-round critic checks) → Report Agent → Critic quality check"""

    session = await db.sessions.find_one({"id": session_id})
    if not session:
        return

    agents = json.loads(session["agents_json"])
    graph = json.loads(session["graph_json"])
    query = session["prediction_query"]

    # Step 4: Simulation Director runs rounds
    logger.info(f"[Orchestrator] Step 4: Simulation Director ({num_rounds} rounds)")
    agents, round_narratives = await sim_director.run(
        session_id, agents, graph, query, num_rounds, db, call_claude_fn
    )

    # Store round narratives and updated agents
    await db.sessions.update_one(
        {"id": session_id},
        {
            "$set": {
                "status": "simulation_done",
                "agents_json": json.dumps(agents),
                "round_narratives": json.dumps(round_narratives),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )

    logger.info(f"[Orchestrator] Simulation complete with {len(round_narratives)} round narratives")


async def run_report_pipeline(session_id: str, call_claude_fn, db) -> dict:
    """Run the Report Agent + Critic pipeline.
    Steps: Report Agent → Critic quality check → Return report with quality_score"""

    session = await db.sessions.find_one({"id": session_id})
    if not session:
        return None

    agents = json.loads(session["agents_json"])
    graph = json.loads(session["graph_json"])
    query = session["prediction_query"]
    total_rounds = session.get("total_rounds", 5)

    # Get round narratives
    round_narratives = []
    if session.get("round_narratives"):
        round_narratives = json.loads(session["round_narratives"])

    # Get posts
    posts = await db.sim_posts.find(
        {"session_id": session_id}
    ).sort([("round", 1), ("created_at", 1)]).to_list(1000)

    # Step 5: Report Agent generates report
    logger.info(f"[Orchestrator] Step 5: Report Agent")
    report = await report_agent.run(
        agents, graph, posts, query, round_narratives, total_rounds, call_claude_fn
    )

    # Step 5b: Critic evaluates report quality
    logger.info(f"[Orchestrator] Step 5b: Critic evaluating report quality")
    quality = await critic_agent.check_report(report, call_claude_fn)
    report["quality_score"] = quality.get("quality_score", 6)
    report["quality_feedback"] = quality.get("feedback", "")
    report["overconfident"] = quality.get("overconfident", False)

    logger.info(f"[Orchestrator] Report quality_score={report['quality_score']}, overconfident={report['overconfident']}")

    return report
