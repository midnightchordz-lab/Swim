"""Common utilities shared across agents."""
import re


def clean_json(text: str) -> str:
    """Strip markdown code fences and think tags from Claude responses."""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    return text.strip()
