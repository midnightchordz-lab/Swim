"""Lightweight sentiment scoring shared by belief and critic agents."""
import re

POSITIVE_TERMS = {
    "good": 0.6, "great": 0.9, "excellent": 1.0, "amazing": 0.9,
    "bullish": 1.0, "optimistic": 0.8, "support": 0.7, "agree": 0.5,
    "hope": 0.4, "better": 0.5, "win": 0.8, "positive": 0.7,
    "rally": 0.9, "growth": 0.7, "strong": 0.7, "confident": 0.8,
    "opportunity": 0.6, "recover": 0.7, "gain": 0.7, "rise": 0.6,
    "improve": 0.6, "benefit": 0.5, "success": 0.8, "profit": 0.8,
    "buy": 0.7, "long": 0.5, "boom": 0.8, "promising": 0.7,
    "resilient": 0.6, "breakthrough": 0.8, "outperform": 0.8,
}

NEGATIVE_TERMS = {
    "bad": 0.6, "terrible": 1.0, "awful": 0.9, "bearish": 1.0,
    "pessimistic": 0.8, "oppose": 0.7, "disagree": 0.5, "fear": 0.7,
    "worse": 0.6, "fail": 0.8, "negative": 0.7, "crash": 1.0,
    "crisis": 0.9, "weak": 0.6, "worried": 0.6, "concern": 0.5,
    "risk": 0.5, "decline": 0.7, "fall": 0.6, "drop": 0.7,
    "loss": 0.8, "sell": 0.7, "short": 0.5, "bust": 0.8,
    "collapse": 1.0, "warning": 0.7, "danger": 0.8, "threat": 0.7,
    "problem": 0.5, "disaster": 1.0, "underperform": 0.8,
}

POSITIVE_PHRASES = {
    "price target raised": 0.9,
    "beats expectations": 0.9,
    "strong demand": 0.8,
    "upside surprise": 0.8,
    "risk on": 0.6,
}

NEGATIVE_PHRASES = {
    "misses expectations": 0.9,
    "price target cut": 0.9,
    "weak demand": 0.8,
    "downside risk": 0.8,
    "risk off": 0.6,
}

NEGATIONS = {"not", "never", "no", "hardly", "barely", "without"}
INTENSIFIERS = {"very": 1.25, "extremely": 1.5, "highly": 1.25, "really": 1.15}
DIMINISHERS = {"slightly": 0.65, "somewhat": 0.75, "maybe": 0.75, "possibly": 0.75}


def sentiment_valence(text: str) -> float:
    """Return a bounded -1..1 valence score with simple phrase, negation, and intensity handling."""
    text_lower = (text or "").lower()
    score = 0.0

    for phrase, weight in POSITIVE_PHRASES.items():
        if phrase in text_lower:
            score += weight
    for phrase, weight in NEGATIVE_PHRASES.items():
        if phrase in text_lower:
            score -= weight

    tokens = re.findall(r"\b[\w']+\b", text_lower)
    for idx, token in enumerate(tokens):
        if token not in POSITIVE_TERMS and token not in NEGATIVE_TERMS:
            continue

        base = POSITIVE_TERMS.get(token, 0.0) - NEGATIVE_TERMS.get(token, 0.0)
        window = tokens[max(0, idx - 3):idx]
        if any(item in NEGATIONS for item in window):
            base *= -0.8
        for item in reversed(window[-2:]):
            if item in INTENSIFIERS:
                base *= INTENSIFIERS[item]
                break
            if item in DIMINISHERS:
                base *= DIMINISHERS[item]
                break
        score += base

    if not tokens:
        return 0.0

    # Normalize by evidence-bearing terms rather than all tokens so short posts remain expressive.
    evidence_terms = sum(1 for token in tokens if token in POSITIVE_TERMS or token in NEGATIVE_TERMS)
    phrase_hits = sum(1 for phrase in POSITIVE_PHRASES if phrase in text_lower)
    phrase_hits += sum(1 for phrase in NEGATIVE_PHRASES if phrase in text_lower)
    denominator = max(1.0, (evidence_terms + phrase_hits) ** 0.7)
    return round(max(-1.0, min(1.0, score / denominator)), 3)


def sentiment_label(text: str, threshold: float = 0.15) -> str:
    """Classify text as positive, negative, or neutral from sentiment_valence."""
    valence = sentiment_valence(text)
    if valence > threshold:
        return "positive"
    if valence < -threshold:
        return "negative"
    return "neutral"


def score_text_valence(text: str) -> float:
    """Compatibility wrapper for callers using the older sentiment API."""
    return sentiment_valence(text)


def score_text(text: str) -> dict:
    """Compatibility wrapper returning both valence and label."""
    valence = sentiment_valence(text)
    return {"valence": valence, "label": sentiment_label(text)}


def classify_sentiment(text: str, threshold: float = 0.15) -> str:
    """Compatibility wrapper for callers using the older sentiment API."""
    return sentiment_label(text, threshold)


def aggregate_sentiment(posts) -> dict:
    """Summarize sentiment labels and mean valence for a collection of posts."""
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    valences = []

    for post in posts or []:
        text = post.get("content", "") if isinstance(post, dict) else str(post)
        label = classify_sentiment(text)
        counts[label] += 1
        valences.append(score_text_valence(text))

    total = len(valences)
    return {
        "counts": counts,
        "total": total,
        "mean_valence": round(sum(valences) / total, 3) if total else 0.0,
        "dominant_sentiment": max(counts, key=counts.get) if total else "neutral",
    }
