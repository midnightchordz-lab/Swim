import math
import re
import logging

logger = logging.getLogger(__name__)

POSITIVE_WORDS = {
    "good","great","excellent","amazing","bullish","optimistic","support",
    "agree","hope","better","win","positive","rally","growth","strong",
    "confident","opportunity","recover","gain","up","rise","improve",
    "promising","benefit","success","profit","buy","long","boom"
}
NEGATIVE_WORDS = {
    "bad","terrible","awful","bearish","pessimistic","oppose","disagree",
    "fear","worse","fail","negative","crash","crisis","weak","worried",
    "concern","risk","decline","fall","drop","loss","sell","short",
    "bust","collapse","warning","danger","threat","problem","disaster"
}

def _score_sentiment(text):
    words = set(re.findall(r'\b\w+\b', text.lower()))
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    if pos > neg: return "positive"
    elif neg > pos: return "negative"
    return "neutral"

def check_herd(posts):
    if not posts:
        return {"herd_detected": False, "herd_score": 0.0, "dominant_sentiment": "neutral"}
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    for post in posts:
        counts[_score_sentiment(post.get("content", ""))] += 1
    total = len(posts)
    dominant = max(counts, key=counts.get)
    herd_score = counts[dominant] / total
    return {
        "herd_detected": herd_score >= 0.70,
        "herd_score": round(herd_score, 2),
        "dominant_sentiment": dominant,
        "sentiment_breakdown": {k: round(v/total, 2) for k, v in counts.items()},
    }

def score_diversity(agents):
    if not agents: return 0.0
    counts = {}
    for agent in agents:
        p = agent.get("personality_type", "Neutral")
        counts[p] = counts.get(p, 0) + 1
    total = len(agents)
    n_categories = len(counts)
    if n_categories <= 1: return 0.0
    entropy = -sum((c/total)*math.log2(c/total) for c in counts.values())
    return round(entropy / math.log2(n_categories), 2)

def get_missing_personalities(agents):
    all_types = {"Skeptic","Optimist","Insider","Contrarian","Expert","Neutral","Activist","Pragmatist"}
    present = {a.get("personality_type","Neutral") for a in agents}
    return list(all_types - present)

async def check_report(report, call_claude_fn):
    confidence_score = report.get("prediction", {}).get("confidence_score", 0)
    issues = []
    if confidence_score > 0.85:
        issues.append(f"Confidence score {confidence_score:.0%} is unusually high")
    if not report.get("risk_factors"):
        issues.append("No risk factors identified")
    if not report.get("alternative_scenarios"):
        issues.append("No alternative scenarios")
    quality_score = max(1, min(10, round(10 - len(issues)*1.5 - max(0,(confidence_score-0.80)*20))))
    return {
        "quality_score": quality_score,
        "overconfident": confidence_score > 0.85,
        "issues": issues,
        "recommendation": "Good quality" if quality_score>=7 else "Consider re-running" if quality_score>=5 else "Low confidence — treat as exploratory"
    }
