import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI

# -----------------------------
# ENV SETUP
# -----------------------------

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY is not set.")

client = OpenAI(api_key=api_key)

# -----------------------------
# GLOBAL TOKEN TRACKING
# -----------------------------

USAGE_STATS = {
    "total_tokens": 0,
    "total_requests": 0
}

# -----------------------------
# MODEL DISCOVERY
# -----------------------------

def get_openai_models() -> List[str]:
    models = client.models.list()
    return sorted(model.id for model in models.data)


def categorize_model(model_id: str) -> str:
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

    return {
        k: v for k, v in categories.items() if v
    }


def get_summary_candidate_models() -> List[str]:
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
# OPTIONAL: SMART DEFAULT MODEL
# -----------------------------

def get_default_model() -> str:
    candidates = get_summary_candidate_models()

    for preferred in ["gpt-4.1", "gpt-4.1-mini"]:
        if preferred in candidates:
            return preferred

    return candidates[0] if candidates else "gpt-4.1"

# -----------------------------
# LLM GENERATION FUNCTION
# -----------------------------

def generate_text(
    prompt_obj: Dict[str, Any],
    model: str = None,
    temperature: float = 0.2
) -> Dict[str, Any]:

    if "error" in prompt_obj:
        return {
            "section": prompt_obj.get("section"),
            "success": False,
            "error": f"Invalid prompt: {prompt_obj['error']}"
        }

    # Select model dynamically if not provided
    if model is None:
        model = get_default_model()

    # Allow prompt_obj to override temperature
    final_temperature = prompt_obj.get("temperature", temperature)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You generate high-quality, non-generic business content."},
                {"role": "user", "content": prompt_obj["prompt"]}
            ],
            max_tokens=prompt_obj.get("max_tokens", 600),
            temperature=final_temperature
        )

        content = response.choices[0].message.content.strip()

        usage = response.usage
        tokens_used = usage.total_tokens if usage else 0

        # Track usage globally
        USAGE_STATS["total_tokens"] += tokens_used
        USAGE_STATS["total_requests"] += 1

        return {
            "section": prompt_obj.get("section"),
            "generated_text": content,
            "tokens_used": tokens_used,
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

# -----------------------------
# USAGE STATS FUNCTION
# -----------------------------

def get_usage_stats() -> Dict[str, Any]:
    return USAGE_STATS