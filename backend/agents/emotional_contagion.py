import re
import random

FEAR_WORDS = {"crash","panic","crisis","collapse","disaster","plunge","fear","terrified","emergency","catastrophe","meltdown","selloff","bloodbath","carnage","warning","alarm","danger"}
EUPHORIA_WORDS = {"moon","rally","surge","skyrocket","incredible","amazing","explosive","euphoric","unstoppable","record","breakthrough","boom","mania","frenzy","buying","hodl","pump"}
ANGER_WORDS = {"outrageous","unacceptable","furious","angry","disgrace","scandal","corrupt","liar","fraud","betrayal","incompetent","disgusting"}

def _post_emotion(text):
    words = set(re.findall(r'\b\w+\b', text.lower()))
    fear_score = len(words & FEAR_WORDS)
    euphoria_score = len(words & EUPHORIA_WORDS)
    anger_score = len(words & ANGER_WORDS)
    raw_valence = (euphoria_score - fear_score - anger_score * 0.5)
    total = max(1, fear_score + euphoria_score + anger_score)
    valence = max(-1.0, min(1.0, raw_valence / total))
    arousal = min(1.0, (fear_score + euphoria_score + anger_score) * 0.25)
    return valence, arousal

def initialise_emotions(agents):
    rng = random.Random(42)
    susceptibility_map = {"Skeptic":0.4,"Optimist":0.7,"Insider":0.5,"Contrarian":0.3,"Expert":0.4,"Neutral":0.55,"Activist":0.8,"Pragmatist":0.45}
    for agent in agents:
        s = susceptibility_map.get(agent.get("personality_type","Neutral"), 0.55)
        s = min(1.0, max(0.1, s + rng.uniform(-0.1, 0.1)))
        agent["emotional_state"] = {"valence": 0.0, "arousal": 0.3, "susceptibility": round(s,2), "history": []}
    return agents

def spread_emotions(agents, round_posts, round_num):
    if not round_posts: return agents
    post_emotions = [_post_emotion(p.get("content","")) for p in round_posts]
    weights = [p.get("influence_level", 5) for p in round_posts]
    total_w = sum(weights)
    if total_w == 0: return agents
    wv = sum(v*w for (v,_),w in zip(post_emotions,weights)) / total_w
    wa = sum(a*w for (_,a),w in zip(post_emotions,weights)) / total_w
    for agent in agents:
        es = agent.get("emotional_state")
        if not es: continue
        s = es["susceptibility"]
        nv = max(-1.0, min(1.0, es["valence"]*0.6 + wv*s*0.4))
        na = max(0.1, min(1.0, es["arousal"]*0.7 + wa*s*0.3))
        es["valence"] = round(nv, 3)
        es["arousal"] = round(na, 3)
        es["history"].append({"round": round_num, "valence": round(nv,3), "arousal": round(na,3)})
        if len(es["history"]) > 20: es["history"] = es["history"][-20:]
    return agents

def get_emotional_temperature(agents):
    if not agents: return {"mean_valence":0.0,"mean_arousal":0.3,"state":"calm"}
    valences = [a.get("emotional_state",{}).get("valence",0.0) for a in agents]
    arousals = [a.get("emotional_state",{}).get("arousal",0.3) for a in agents]
    mv = sum(valences)/len(valences)
    ma = sum(arousals)/len(arousals)
    if mv < -0.5 and ma > 0.6: state = "PANIC"
    elif mv < -0.3: state = "fear"
    elif mv > 0.5 and ma > 0.6: state = "EUPHORIA"
    elif mv > 0.3: state = "optimism"
    elif ma > 0.5: state = "agitated"
    else: state = "calm"
    return {"mean_valence":round(mv,3),"mean_arousal":round(ma,3),"state":state,"panic_mode":mv<-0.5 and ma>0.6,"euphoria_mode":mv>0.5 and ma>0.6}

def get_emotion_label(valence):
    if valence < -0.6: return "panicking"
    elif valence < -0.3: return "anxious"
    elif valence < -0.1: return "concerned"
    elif valence < 0.1: return "neutral"
    elif valence < 0.3: return "cautiously optimistic"
    elif valence < 0.6: return "optimistic"
    else: return "euphoric"
