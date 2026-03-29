"""Critic Agent - Pure evaluation agent for quality control across the pipeline."""
import logging
import json
import math
from collections import Counter

logger = logging.getLogger(__name__)


def score_diversity(agents: list) -> float:
    """Score persona diversity using entropy-based measure. Pure Python, no LLM."""
    if not agents:
        return 0.0
    types = [a.get("personality_type", "Unknown") for a in agents]
    counts = Counter(types)
    n = len(types)
    if n <= 1:
        return 0.0
    # Shannon entropy normalized to 0-1
    entropy = -sum((c / n) * math.log2(c / n) for c in counts.values() if c > 0)
    max_entropy = math.log2(len(counts)) if len(counts) > 1 else 1.0
    return round(entropy / max_entropy, 3) if max_entropy > 0 else 0.0


def check_herd(posts: list) -> dict:
    """Detect herd mentality in posts via keyword sentiment. Pure Python, no LLM."""
    if not posts:
        return {"herd_score": 0.0, "dominant_sentiment": "neutral"}

    positive_kw = {"bullish", "optimistic", "growth", "rally", "surge", "buy", "strong",
                   "support", "positive", "upside", "recovery", "boom", "gain", "profit"}
    negative_kw = {"bearish", "crash", "decline", "sell", "panic", "fear", "drop",
                   "risk", "collapse", "downturn", "loss", "weak", "negative", "falling"}

    pos_count = 0
    neg_count = 0
    for p in posts:
        words = set(p.get("content", "").lower().split())
        pos_count += len(words & positive_kw)
        neg_count += len(words & negative_kw)

    total = pos_count + neg_count
    if total == 0:
        return {"herd_score": 0.0, "dominant_sentiment": "neutral"}

    dominant = "positive" if pos_count > neg_count else "negative"
    imbalance = abs(pos_count - neg_count) / total
    return {"herd_score": round(imbalance, 3), "dominant_sentiment": dominant}


async def check_brief(brief_text: str, call_claude_fn) -> dict:
    """Evaluate intel brief for bias and source diversity. Returns bias_score 0-10."""
    system_prompt = "You are a media bias evaluator. Respond ONLY with valid JSON, no markdown."
    user_prompt = f"""Rate this intelligence brief for source diversity and ideological balance.

Brief (first 2000 chars):
{brief_text[:2000]}

Return JSON:
{{
  "bias_score": <0-10 integer, 10=extremely biased>,
  "feedback": "<one sentence explaining the main bias issue, or 'well-balanced' if score<=4>",
  "dominant_perspective": "<the perspective that dominates, e.g. 'bullish investors', 'government sources'>"
}}"""
    try:
        from services.agents.common import clean_json
        raw = await call_claude_fn(system_prompt, user_prompt, max_tokens=200)
        return json.loads(clean_json(raw))
    except Exception as e:
        logger.warning(f"Critic check_brief failed: {e}")
        return {"bias_score": 5, "feedback": "Unable to evaluate", "dominant_perspective": "unknown"}


async def check_report(report: dict, call_claude_fn) -> dict:
    """Evaluate final report quality. Flags overconfidence."""
    confidence_score = report.get("prediction", {}).get("confidence_score", 0.5)
    overconfident = confidence_score > 0.85

    system_prompt = "You are a prediction report quality auditor. Respond ONLY with valid JSON, no markdown."
    user_prompt = f"""Rate this prediction report for analytical rigor and evidence quality.

Executive Summary: {report.get('executive_summary', '')[:500]}
Confidence Score: {confidence_score}
Risk Factors: {len(report.get('risk_factors', []))}
Alternative Scenarios: {len(report.get('alternative_scenarios', []))}
Key Factions: {len(report.get('opinion_landscape', {}).get('key_factions', []))}

Return JSON:
{{
  "quality_score": <0-10 integer>,
  "overconfident": {str(overconfident).lower()},
  "feedback": "<one sentence summary of quality>"
}}"""
    try:
        from services.agents.common import clean_json
        raw = await call_claude_fn(system_prompt, user_prompt, max_tokens=200)
        result = json.loads(clean_json(raw))
        result["overconfident"] = overconfident or result.get("overconfident", False)
        return result
    except Exception as e:
        logger.warning(f"Critic check_report failed: {e}")
        return {"quality_score": 6, "overconfident": overconfident, "feedback": "Unable to evaluate"}
