"""LLM integration and usage tracking for report generation.

This module provides model discovery utilities, generation wrappers around the
OpenAI client, and lightweight token/cost accounting.
"""

import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

# -----------------------------
# ENV SETUP
# -----------------------------

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
_OPENAI_CLIENT: Optional[OpenAI] = None

FALLBACK_MODEL_IDS = [
    "gpt-4.1-mini",
    "gpt-4.1",
    "o4-mini",
    "o3-mini",
]

# -----------------------------
# GLOBAL TOKEN + COST TRACKING
# -----------------------------

USAGE_STATS = {
    "total_tokens": 0,
    "total_requests": 0,
    "total_cost_usd": 0.0,
}


def _get_client() -> OpenAI:
    """Return a singleton OpenAI client using `OPENAI_API_KEY`."""
    global _OPENAI_CLIENT

    if _OPENAI_CLIENT is not None:
        return _OPENAI_CLIENT

    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    _OPENAI_CLIENT = OpenAI(api_key=API_KEY)
    return _OPENAI_CLIENT

# -----------------------------
# MODEL DISCOVERY
# -----------------------------

def get_openai_models() -> List[str]:
    """List available models from the OpenAI API, with safe fallbacks."""
    if not API_KEY:
        return list(FALLBACK_MODEL_IDS)

    try:
        models = _get_client().models.list()
        return sorted(model.id for model in models.data)
    except Exception:
        return list(FALLBACK_MODEL_IDS)


def categorize_model(model_id: str) -> str:
    """Map a model id to a coarse capability category."""
    model = model_id.lower()

    if "embedding" in model:
        return "embeddings"
    if "whisper" in model or "transcribe" in model:
        return "speech_to_text"
    if "tts" in model or "audio" in model or "speech" in model:
        return "audio"
    if "dall-e" in model or "image" in model or "gpt-image" in model:
        return "image"
    if "moderation" in model:
        return "moderation"
    if "realtime" in model:
        return "realtime"
    if model.startswith("o") and any(char.isdigit() for char in model):
        return "reasoning"
    if "reasoning" in model:
        return "reasoning"
    if "mini" in model or "nano" in model:
        return "cheap_text_generation"
    if "preview" in model or "pro" in model:
        return "strong_text_generation"
    if model.startswith("gpt"):
        return "text_generation"

    return "unknown"


def get_categorized_openai_models() -> Dict[str, List[str]]:
    """Return discovered models grouped by `categorize_model` labels."""
    models = get_openai_models()

    categories = {
        "cheap_text_generation": [],
        "text_generation": [],
        "strong_text_generation": [],
        "reasoning": [],
        "embeddings": [],
        "speech_to_text": [],
        "audio": [],
        "image": [],
        "moderation": [],
        "realtime": [],
        "unknown": [],
    }

    for model_id in models:
        category = categorize_model(model_id)
        categories[category].append(model_id)

    return {k: v for k, v in categories.items() if v}


def get_summary_candidate_models() -> List[str]:
    """Return text-generation candidates suitable for this app UI."""
    categorized = get_categorized_openai_models()

    candidates = []
    for category in [
        "cheap_text_generation",
        "text_generation",
        "strong_text_generation",
        "reasoning",
    ]:
        candidates.extend(categorized.get(category, []))

    return candidates

# -----------------------------
# DEFAULT MODEL
# -----------------------------

def get_default_model() -> str:
    """Choose the default model used when no explicit model is passed."""
    candidates = get_summary_candidate_models()

    for preferred in ["gpt-4.1", "gpt-4.1-mini"]:
        if preferred in candidates:
            return preferred

    return candidates[0] if candidates else "gpt-4.1"

# -----------------------------
# MODEL PRICING (USD per 1K tokens)
# -----------------------------

MODEL_PRICING = {
    "gpt-4.1": {"input": 0.01, "output": 0.03},
    "gpt-4.1-mini": {"input": 0.002, "output": 0.006},

    "cheap_text_generation": {"input": 0.001, "output": 0.002},
    "text_generation": {"input": 0.005, "output": 0.015},
    "strong_text_generation": {"input": 0.01, "output": 0.03},
    "reasoning": {"input": 0.02, "output": 0.06},

    "embeddings": {"input": 0.0001, "output": 0.0001},
}

# -----------------------------
# COST CALCULATION
# -----------------------------

def calculate_cost_from_usage(usage, model: str) -> float:
    """Estimate request cost (USD) from token usage and pricing table."""
    if not usage:
        return 0.0

    input_tokens = getattr(usage, "prompt_tokens", 0)
    output_tokens = getattr(usage, "completion_tokens", 0)

    # Exact model pricing
    if model in MODEL_PRICING:
        pricing = MODEL_PRICING[model]
    else:
        category = categorize_model(model)
        pricing = MODEL_PRICING.get(category)

    if not pricing:
        raise ValueError(f"No pricing found for model: {model}")

    input_cost = (input_tokens / 1000) * pricing["input"]
    output_cost = (output_tokens / 1000) * pricing["output"]

    return round(input_cost + output_cost, 6)


def _normalize_generation_request(
    prompt_obj: Dict[str, Any],
) -> Dict[str, Any]:
    """Validate the minimum required prompt payload shape."""
    if not isinstance(prompt_obj, dict):
        raise TypeError("Prompt payload must be a dict.")

    if not prompt_obj.get("prompt"):
        raise ValueError("Prompt payload is missing 'prompt'.")

    return prompt_obj

# -----------------------------
# LLM GENERATION FUNCTION
# -----------------------------

def generate_text(
    prompt_obj: Dict[str, Any],
    model: str = None,
    temperature: float = 0.2
) -> Dict[str, Any]:
    """Call the chat completion endpoint and return normalized output payload.

    Args:
        prompt_obj (dict): Prompt payload containing at least `prompt`.
        model (str | None): Requested model id. Falls back to default model.
        temperature (float): Fallback temperature if payload does not override.

    Returns:
        dict: Generation result with text, usage/cost, and success/error flags.
    """
    if "error" in prompt_obj:
        return {
            "section": prompt_obj.get("section"),
            "success": False,
            "error": f"Invalid prompt: {prompt_obj['error']}"
        }

    prompt_obj = _normalize_generation_request(prompt_obj)

    if model is None:
        model = get_default_model()

    final_temperature = prompt_obj.get("temperature", temperature)

    try:
        response = _get_client().chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You generate high-quality, non-generic business content."},
                {"role": "user", "content": prompt_obj["prompt"]}
            ],
            max_tokens=prompt_obj.get("max_tokens", 16000),
            temperature=final_temperature
        )

        content = response.choices[0].message.content.strip()

        usage = response.usage
        tokens_used = usage.total_tokens if usage else 0
        cost = calculate_cost_from_usage(usage, model)

        # Global tracking
        USAGE_STATS["total_tokens"] += tokens_used
        USAGE_STATS["total_requests"] += 1
        USAGE_STATS["total_cost_usd"] += cost

        return {
            "section": prompt_obj.get("section"),
            "generated_text": content,
            "tokens_used": tokens_used,
            "cost_usd": cost,
            "model_used": model,
            "temperature_used": final_temperature,
            "success": True
        }

    except Exception as e:
        return {
            "section": prompt_obj.get("section"),
            "success": False,
            "error": str(e)
        }


def generate_section(prompt_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Backward-compatible wrapper expected by content_pipeline."""
    return generate_text(prompt_obj)

# -----------------------------
# USAGE STATS FUNCTION
# -----------------------------

def get_usage_stats() -> Dict[str, Any]:
    """Return global usage/cost counters with per-request averages."""
    return {
        **USAGE_STATS,
        "avg_tokens_per_request": (
            USAGE_STATS["total_tokens"] / USAGE_STATS["total_requests"]
            if USAGE_STATS["total_requests"] > 0 else 0
        ),
        "avg_cost_per_request": (
            USAGE_STATS["total_cost_usd"] / USAGE_STATS["total_requests"]
            if USAGE_STATS["total_requests"] > 0 else 0
        )
    }
