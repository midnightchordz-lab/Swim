"""Simulation Director - Runs multi-round simulations with round narratives and herd detection."""
import json
import logging
import random
import asyncio
from datetime import datetime, timezone
from services.agents import critic_agent

logger = logging.getLogger(__name__)

CONTRARIAN_EVENTS = [
    "BREAKING: A major institutional player has just taken a contrarian position, defying the dominant market narrative.",
    "ALERT: New data has emerged that contradicts the prevailing consensus — experts are reassessing their positions.",
    "DEVELOPING: An unexpected regulatory announcement has thrown a wrench into the dominant thesis.",
    "UPDATE: A whistleblower report challenges the assumptions underlying the majority view.",
    "FLASH: Surprising economic data released — several analysts are reversing their earlier positions.",
]


async def write_round_narrative(round_num: int, posts: list, graph: dict,
                                query: str, call_claude_fn) -> str:
    """Summarise what happened in a simulation round in 2 sentences."""
    post_snippets = "\n".join([
        f"[{p['platform']}] {p['agent_name']}: {p['content'][:100]}"
        for p in posts[:12]
    ])

    system_prompt = "You are a simulation narrator. Write exactly 2 sentences summarizing a discussion round. No JSON, just plain text."
    user_prompt = f"""Round {round_num} posts:
{post_snippets}

Question being debated: {query}

Write 2 sentences summarizing the key dynamics, shifts, or tensions in this round."""

    try:
        narrative = await call_claude_fn(system_prompt, user_prompt, max_tokens=150)
        return narrative.strip()
    except Exception as e:
        logger.warning(f"Narrative generation failed for round {round_num}: {e}")
        return f"Round {round_num}: Discussion continued with mixed perspectives."


async def run(session_id: str, agents: list, graph: dict, prediction_query: str,
              num_rounds: int, db, call_claude_fn) -> tuple:
    """Run multi-round simulation with narratives and herd detection.
    Returns (agents_with_memories, round_narratives)."""

    round_narratives = []
    prev_narrative = ""

    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {"current_round": 0, "total_rounds": num_rounds}}
    )

    for round_num in range(1, num_rounds + 1):
        await db.sessions.update_one(
            {"id": session_id}, {"$set": {"current_round": round_num}}
        )

        # Select 60-80% of agents
        active_agents = random.sample(agents, k=max(3, int(len(agents) * random.uniform(0.6, 0.8))))

        # Get recent posts for context
        recent_posts = await db.sim_posts.find(
            {"session_id": session_id}
        ).sort("_id", -1).limit(8).to_list(8)

        recent_context = "\n".join([
            f"{p['platform']}: {p['agent_name']}: {p['content']}"
            for p in reversed(recent_posts)
        ]) if recent_posts else "No previous posts yet."

        # Build narrative context injection
        narrative_injection = ""
        if prev_narrative:
            narrative_injection = f"\nPrevious round summary: {prev_narrative}\nReact to developments from last round in your post."

        # Check for herd mentality from previous round's posts
        if round_num > 1:
            prev_round_posts = await db.sim_posts.find(
                {"session_id": session_id, "round": round_num - 1}
            ).to_list(100)
            herd = critic_agent.check_herd(prev_round_posts)

            if herd["herd_score"] > 0.7:
                event = random.choice(CONTRARIAN_EVENTS)
                narrative_injection += f"\n\nBREAKING NEWS EVENT: {event}\nThis directly challenges the {herd['dominant_sentiment']} consensus. React to this in your post."
                logger.info(f"Round {round_num}: Herd detected (score={herd['herd_score']}), injecting contrarian event")

        # Generate posts for each active agent
        for agent in active_agents:
            platform = agent.get("platform_preference", random.choice(["Twitter", "Reddit"]))
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
World Context: {graph.get('summary', '')[:800]}
Prediction Question: {prediction_query}
Recent posts (last 8): {recent_context}
Platform: {platform}
{platform_instruction}
{narrative_injection}

Write ONE authentic post as {agent['name']}. Output ONLY the post content."""

            try:
                response = await call_claude_fn(system_prompt, user_prompt, max_tokens=200)
                content = response.strip()

                post = {
                    "session_id": session_id,
                    "round": round_num,
                    "agent_id": agent["id"],
                    "agent_name": agent["name"],
                    "agent_emoji": agent.get("avatar_emoji", ""),
                    "platform": platform,
                    "content": content,
                    "post_type": "post",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.sim_posts.insert_one(post)
                agent["memories"] = agent.get("memories", [])[-9:] + [f"I posted: {content[:100]}"]

            except Exception as e:
                logger.error(f"Error generating post for {agent['name']}: {e}")
                continue

            await asyncio.sleep(0.5)

        # Generate replies
        all_round_posts = await db.sim_posts.find(
            {"session_id": session_id, "round": round_num}
        ).to_list(100)

        if all_round_posts and len(active_agents) >= 2:
            reply_agents = random.sample(active_agents, min(2, len(active_agents)))
            target_posts = random.sample(all_round_posts, min(2, len(all_round_posts)))

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
                    response = await call_claude_fn(system_prompt, user_prompt, max_tokens=150)
                    reply = {
                        "session_id": session_id,
                        "round": round_num,
                        "agent_id": agent["id"],
                        "agent_name": agent["name"],
                        "agent_emoji": agent.get("avatar_emoji", ""),
                        "platform": platform,
                        "content": response.strip(),
                        "post_type": "reply",
                        "reply_to": target_post["agent_name"],
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.sim_posts.insert_one(reply)
                except Exception as e:
                    logger.error(f"Error generating reply: {e}")

                await asyncio.sleep(0.3)

        # Write round narrative
        round_posts = await db.sim_posts.find(
            {"session_id": session_id, "round": round_num}
        ).to_list(100)
        narrative = await write_round_narrative(round_num, round_posts, graph, prediction_query, call_claude_fn)
        round_narratives.append(f"Round {round_num}: {narrative}")
        prev_narrative = narrative
        logger.info(f"Round {round_num} narrative: {narrative[:100]}")

    return agents, round_narratives
