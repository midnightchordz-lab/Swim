"""Shared topic classification helpers for prediction and persona generation."""

TOPIC_CATEGORIES = {
    "financial": [
        "stock", "market", "crypto", "bitcoin", "trading", "investment",
        "economy", "fed", "interest rate", "inflation",
    ],
    "political": [
        "election", "vote", "congress", "senate", "president", "policy",
        "law", "democrat", "republican", "legislation",
    ],
    "geopolitical": [
        "war", "conflict", "military", "treaty", "sanctions", "diplomacy",
        "nato", "un", "border",
    ],
    "sports": [
        "game", "match", "championship", "player", "team", "league",
        "score", "tournament", "coach",
    ],
    "tech": [
        "ai", "startup", "tech", "software", "app", "launch", "product",
        "innovation", "company",
    ],
    "social_cultural": [
        "trend", "viral", "culture", "social", "celebrity", "movement",
        "protest",
    ],
}


def detect_topic_category(topic: str) -> str:
    """Detect the category of a topic for agent customization."""
    topic_lower = (topic or "").lower()
    for category, keywords in TOPIC_CATEGORIES.items():
        if any(keyword in topic_lower for keyword in keywords):
            return category
    return "general"
