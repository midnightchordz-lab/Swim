import random

def assign_network_properties(agents, seed=42):
    rng = random.Random(seed)
    n = len(agents)
    if n == 0: return agents
    raw_counts = sorted([int(rng.paretovariate(1.16)*100) for _ in agents])
    indices = list(range(n))
    rng.shuffle(indices)
    for rank, agent_idx in enumerate(indices):
        agents[agent_idx]["follower_count"] = raw_counts[rank]
    sorted_agents = sorted(agents, key=lambda a: a["follower_count"], reverse=True)
    hub_cutoff = max(1, n//10)
    hub_ids = {a["id"] for a in sorted_agents[:hub_cutoff]}
    id_to_agent = {a["id"]: a for a in agents}
    # First pass: assign hub status
    for agent in agents:
        agent["is_hub"] = agent["id"] in hub_ids
        agent["network_tier"] = "hub" if agent["is_hub"] else "peripheral"
    # Second pass: build following network
    hub_agent_ids = [a["id"] for a in agents if a["is_hub"]]
    peripheral_ids = [a["id"] for a in agents if not a["is_hub"]]
    for agent in agents:
        n_follows = min(n-1, rng.randint(10,20) if agent["is_hub"] else rng.randint(5,12))
        pool = [aid for aid in (hub_agent_ids+peripheral_ids) if aid != agent["id"]]
        weights = [3.0 if id_to_agent[aid]["is_hub"] else 1.0 for aid in pool]
        chosen = []
        pool_w = list(zip(pool, weights))
        for _ in range(min(n_follows, len(pool_w))):
            if not pool_w: break
            total = sum(w for _,w in pool_w)
            r = rng.uniform(0, total)
            cum = 0
            for i,(item,w) in enumerate(pool_w):
                cum += w
                if cum >= r:
                    chosen.append(item)
                    pool_w.pop(i)
                    break
        agent["following"] = chosen
    return agents

def get_network_stats(agents):
    if not agents: return {}
    hubs = [a for a in agents if a.get("is_hub")]
    follower_counts = [a.get("follower_count",0) for a in agents]
    return {
        "total_agents": len(agents),
        "hub_count": len(hubs),
        "peripheral_count": len(agents)-len(hubs),
        "max_followers": max(follower_counts) if follower_counts else 0,
        "mean_followers": round(sum(follower_counts)/len(follower_counts),1) if follower_counts else 0,
        "hub_ids": [a["id"] for a in hubs],
    }

def get_visible_posts(agent, all_posts):
    if not all_posts: return []
    following_set = set(agent.get("following",[]))
    visible = [p for p in all_posts if p.get("agent_id") != agent["id"] and (p.get("is_hub_post") or p.get("agent_id") in following_set)]
    visible.sort(key=lambda p: (p.get("round",0), p.get("influence_level",0)), reverse=True)
    return visible[:12]
