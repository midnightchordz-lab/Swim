"""Population scaling system - Tier 2 (statistical clones) and Tier 3 (silent population)."""
import random
import re
import math
import logging

logger = logging.getLogger(__name__)

# Indian demographic distributions (used when topic is India-related)
INDIA_DEMOGRAPHICS = {
    "age": {"18-25": 0.30, "26-40": 0.35, "41-60": 0.25, "60+": 0.10},
    "location": {"urban": 0.35, "rural": 0.65},
    "income": {"low": 0.40, "middle": 0.45, "high": 0.15},
}

# Default global demographics
GLOBAL_DEMOGRAPHICS = {
    "age": {"18-25": 0.25, "26-40": 0.35, "41-60": 0.28, "60+": 0.12},
    "location": {"urban": 0.55, "rural": 0.45},
    "income": {"low": 0.30, "middle": 0.50, "high": 0.20},
}

INDIA_KEYWORDS = {"india", "indian", "nifty", "sensex", "bse", "nse", "rupee", "inr",
                  "mumbai", "delhi", "rbi", "modi", "bjp", "congress", "lok sabha"}

POSITIVE_SWAP = ["good", "great", "strong", "bullish", "positive", "optimistic", "rally", "growth", "gain"]
NEGATIVE_SWAP = ["bad", "weak", "bearish", "negative", "pessimistic", "decline", "crash", "loss", "drop"]


def _is_india_topic(topic: str) -> bool:
    return bool(set(topic.lower().split()) & INDIA_KEYWORDS)


def generate_clones(tier1_agents: list, multiplier: int, seed: int = 42) -> list:
    """Generate Tier 2 statistical clones from Tier 1 LLM agents."""
    rng = random.Random(seed)
    clones = []
    clone_id = 0

    for parent in tier1_agents:
        for i in range(multiplier):
            clone_id += 1
            influence = parent.get("influence_level", 5)
            variance = rng.uniform(-0.15, 0.15)
            clone_influence = max(1, min(10, round(influence * (1 + variance))))

            clone = {
                "id": f"clone_{clone_id}",
                "parent_id": parent["id"],
                "agent_tier": "clone",
                "name": f"{parent['name']} (echo {i+1})",
                "personality_type": parent.get("personality_type", "Neutral"),
                "platform_preference": parent.get("platform_preference", "Twitter"),
                "initial_stance": parent.get("initial_stance", ""),
                "influence_level": clone_influence,
                "occupation": parent.get("occupation", ""),
                "avatar_emoji": parent.get("avatar_emoji", ""),
                "communication_style": parent.get("communication_style", "factual"),
                "post_probability": 0.40,
                "memories": [],
            }
            clones.append(clone)

    logger.info(f"Generated {len(clones)} Tier 2 clones from {len(tier1_agents)} parents")
    return clones


def generate_silent_population(size: int, topic: str, seed: int = 42) -> dict:
    """Generate Tier 3 silent population as demographic distributions."""
    rng = random.Random(seed)
    demo = INDIA_DEMOGRAPHICS if _is_india_topic(topic) else GLOBAL_DEMOGRAPHICS

    segments = []
    for age_group, age_pct in demo["age"].items():
        for location, loc_pct in demo["location"].items():
            for income, inc_pct in demo["income"].items():
                segment_size = round(size * age_pct * loc_pct * inc_pct)
                if segment_size < 1:
                    continue
                # Each segment has a base affinity profile
                base_affinity = rng.uniform(0.2, 0.8)
                segments.append({
                    "age_group": age_group,
                    "location": location,
                    "income": income,
                    "count": segment_size,
                    "base_affinity": round(base_affinity, 3),
                    "engagement_rate": round(rng.uniform(0.02, 0.15), 3),
                })

    total = sum(s["count"] for s in segments)
    logger.info(f"Generated silent population: {total} across {len(segments)} segments")

    return {
        "total": total,
        "segments": segments,
        "demographics": "india" if _is_india_topic(topic) else "global",
    }


def apply_lexical_variation(text: str, rng: random.Random) -> str:
    """Apply minor lexical variation to a parent post for clone echo."""
    words = text.split()
    if len(words) < 3:
        return text

    # Randomly replace 1-2 sentiment words
    for i, word in enumerate(words):
        clean = word.lower().strip(".,!?")
        if rng.random() < 0.2:
            if clean in POSITIVE_SWAP:
                words[i] = rng.choice(POSITIVE_SWAP)
            elif clean in NEGATIVE_SWAP:
                words[i] = rng.choice(NEGATIVE_SWAP)

    # Occasionally add/remove emphasis
    if rng.random() < 0.3 and len(words) > 5:
        idx = rng.randint(0, len(words) - 1)
        if words[idx].endswith("!"):
            words[idx] = words[idx].rstrip("!")
        else:
            words[idx] = words[idx] + ("!" if rng.random() < 0.5 else "")

    return " ".join(words)


def generate_clone_posts(clones: list, parent_posts: dict, round_num: int, seed: int = 42) -> list:
    """Generate echo posts from clones based on parent posts."""
    rng = random.Random(seed + round_num)
    echo_posts = []

    for clone in clones:
        if rng.random() > clone.get("post_probability", 0.40):
            continue

        parent_id = clone["parent_id"]
        recent = parent_posts.get(parent_id, [])
        if not recent:
            continue

        source_post = rng.choice(recent)
        varied_content = apply_lexical_variation(source_post["content"], rng)

        echo_posts.append({
            "agent_id": clone["id"],
            "parent_id": parent_id,
            "agent_name": clone["name"],
            "agent_emoji": clone.get("avatar_emoji", ""),
            "agent_tier": "clone",
            "platform": clone.get("platform_preference", "Twitter"),
            "content": varied_content,
            "post_type": "echo",
            "round": round_num,
            "influence_level": clone.get("influence_level", 3),
            "is_hub_post": False,
        })

    return echo_posts


def calculate_silent_reactions(posts: list, silent_pop: dict, round_num: int, seed: int = 42) -> dict:
    """Calculate Tier 3 silent population reactions to posts."""
    rng = random.Random(seed + round_num)
    reactions = {}

    for post in posts:
        influence = post.get("influence_level", 5)
        is_hub = post.get("is_hub_post", False)
        total_likes = 0
        total_shares = 0
        total_hostile = 0

        for segment in silent_pop.get("segments", []):
            seg_count = segment["count"]
            base_aff = segment["base_affinity"]
            engagement = segment["engagement_rate"]

            # Affinity based on post sentiment vs segment tendency
            post_valence = post.get("belief_position", post.get("emotional_valence", 0.0))
            affinity = base_aff
            if post_valence > 0.15 and base_aff > 0.5:
                affinity = min(1.0, base_aff + 0.2)
            elif post_valence < -0.15 and base_aff < 0.5:
                affinity = min(1.0, base_aff + 0.2)

            # Hub boost
            hub_mult = 1.5 if is_hub else 1.0

            like_prob = affinity * (influence / 10.0) * 0.1 * hub_mult * engagement
            share_prob = like_prob * 0.3
            hostile_prob = (1 - affinity) * 0.05 * engagement

            seg_likes = sum(1 for _ in range(seg_count) if rng.random() < like_prob)
            seg_shares = sum(1 for _ in range(seg_count) if rng.random() < share_prob)
            seg_hostile = sum(1 for _ in range(seg_count) if rng.random() < hostile_prob)

            total_likes += seg_likes
            total_shares += seg_shares
            total_hostile += seg_hostile

        total_pop = silent_pop.get("total", 1)
        reach = (total_likes + total_shares * 3) / max(1, total_pop)

        reactions[post.get("agent_id", "") + "_" + str(post.get("round", 0))] = {
            "likes": total_likes,
            "shares": total_shares,
            "hostile": total_hostile,
            "reach_score": round(reach, 4),
            "viral": reach > 0.05,
        }

    return reactions


def get_agent_feed(agent: dict, all_posts: list, round_num: int) -> list:
    """OASIS-style interest-based feed algorithm."""
    following = set(agent.get("following", []))
    scored = []

    for post in all_posts:
        score = 0.0
        if post["agent_id"] in following:
            score += 3.0
        if post.get("is_hub_post"):
            score += 2.0
        if post.get("viral"):
            score += 2.0
        if post.get("personality_type") == agent.get("personality_type"):
            score += 1.0
        score += 1.0 / max(1, round_num - post.get("round", round_num))
        scored.append((score, post))

    scored.sort(key=lambda x: -x[0])
    return [p for _, p in scored[:8]]


def get_demographic_breakdown(silent_pop: dict, posts: list, reactions: dict) -> list:
    """Get how each demographic segment reacted overall."""
    if not silent_pop or not silent_pop.get("segments"):
        return []

    segments_summary = []
    for seg in silent_pop["segments"]:
        label = f"{seg['age_group']}/{seg['location']}/{seg['income']}"
        affinity = seg["base_affinity"]
        stance = "support" if affinity > 0.55 else "oppose" if affinity < 0.45 else "undecided"
        segments_summary.append({
            "label": label,
            "count": seg["count"],
            "stance": stance,
            "engagement_rate": seg["engagement_rate"],
            "affinity": affinity,
        })

    return segments_summary
