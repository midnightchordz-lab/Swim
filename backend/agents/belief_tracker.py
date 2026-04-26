from .sentiment import score_text


def _text_valence(text):
    return score_text(text)["valence"]

def initialise_beliefs(agents):
    for agent in agents:
        stance_valence = _text_valence(agent.get("initial_stance", ""))
        influence = agent.get("influence_level", 5) / 10.0
        agent["belief_state"] = {
            "position": round(stance_valence, 2),
            "certainty": round(0.4 + influence * 0.3, 2),
            "prior": round(stance_valence, 2),
            "history": [],
        }
    return agents

def update_beliefs(agents, round_posts, round_num):
    if not round_posts: return agents
    influence_map = {a["id"]: a.get("influence_level", 5) for a in agents}
    weighted_sum = 0.0
    weight_total = 0.0
    for post in round_posts:
        valence = _text_valence(post.get("content",""))
        w = influence_map.get(post.get("agent_id",""), 5)
        weighted_sum += valence * w
        weight_total += w
    round_valence = weighted_sum / weight_total if weight_total > 0 else 0.0
    for agent in agents:
        bs = agent.get("belief_state")
        if not bs: continue
        certainty = bs["certainty"]
        position = bs["position"]
        learning_rate = (1.0 - certainty) * 0.35
        delta = learning_rate * (round_valence - position)
        new_position = max(-1.0, min(1.0, position + delta))
        new_certainty = min(0.95, certainty + 0.02)
        bs["position"] = round(new_position, 3)
        bs["certainty"] = round(new_certainty, 3)
        bs["history"].append({"round": round_num, "position": round(new_position, 3)})
        if len(bs["history"]) > 20: bs["history"] = bs["history"][-20:]
    return agents

def get_belief_summary(agents):
    positions = [a["belief_state"]["position"] for a in agents if "belief_state" in a]
    if not positions: return {"support": 33, "opposition": 33, "undecided": 34}
    total = len(positions)
    support = sum(1 for p in positions if p > 0.15)
    opposition = sum(1 for p in positions if p < -0.15)
    undecided = total - support - opposition
    return {
        "support": round(support/total*100),
        "opposition": round(opposition/total*100),
        "undecided": round(undecided/total*100),
        "mean_position": round(sum(positions)/total, 3),
        "polarisation": round(sum(abs(p) for p in positions)/total, 3),
    }
