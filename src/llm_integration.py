import os

from dotenv import load_dotenv
from openai import OpenAI


# Load variables from .env into the process environment.
# This allows OPENAI_API_KEY to be read with os.getenv().
load_dotenv()


# Read the user-provided OpenAI API key.
api_key = os.getenv("OPENAI_API_KEY")


# Stop immediately if the key is missing.
# Without this, the OpenAI call would fail later with a less clear error.
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set.")


# Create a reusable OpenAI client.
# Other functions in this module can use this same client.
client = OpenAI(api_key=api_key)


def get_openai_models() -> list[str]:
    """
    Fetch the model IDs available to the configured OpenAI API key.

    Returns:
        Sorted list of available OpenAI model IDs.

    Notes:
        The result depends on the API key being used.
        Different users/accounts may have access to different models.
    """
    models = client.models.list()

    # Extract only the model ID from each returned model object.
    return sorted(model.id for model in models.data)


def categorize_model(model_id: str) -> str:
    """
    Assign an application-level category to one OpenAI model ID.

    Args:
        model_id:
            Model ID returned by OpenAI, for example "gpt-4.1-mini".

    Returns:
        Category name used by the application.

    Notes:
        This categorization is based on model-name patterns.
        It is not an official OpenAI category system.
    """
    model = model_id.lower()

    # Embedding models are used for semantic search/RAG, not direct text output.
    if "embedding" in model:
        return "embeddings"

    # Speech-to-text / transcription models.
    if "whisper" in model or "transcribe" in model:
        return "speech_to_text"

    # Text-to-speech or audio models.
    if "tts" in model or "audio" in model or "speech" in model:
        return "audio"

    # Image generation or image-processing models.
    if "dall-e" in model or "image" in model or "gpt-image" in model:
        return "image"

    # Moderation/safety classification models.
    if "moderation" in model:
        return "moderation"

    # Realtime models are usually for streaming/voice use cases.
    if "realtime" in model:
        return "realtime"

    # Reasoning models usually use names like o1, o3, or o4-mini.
    if model.startswith("o") and any(char.isdigit() for char in model):
        return "reasoning"

    # Extra fallback for any explicitly named reasoning model.
    if "reasoning" in model:
        return "reasoning"

    # Mini/nano models are usually smaller, faster, and cheaper.
    if "mini" in model or "nano" in model:
        return "cheap_text_generation"

    # Preview/pro models are separated because they may be stronger,
    # experimental, unstable, or more expensive.
    if "preview" in model or "pro" in model:
        return "strong_text_generation"

    # General GPT models are treated as normal text-generation candidates.
    if model.startswith("gpt"):
        return "text_generation"

    # Unknown models are kept separate so they can be hidden or reviewed.
    return "unknown"


def get_categorized_openai_models() -> dict[str, list[str]]:
    """
    Fetch available OpenAI models and group them by application category.

    Returns:
        Dictionary mapping category names to lists of model IDs.

    Example:
        {
            "cheap_text_generation": ["gpt-4.1-mini"],
            "embeddings": ["text-embedding-3-small"]
        }
    """
    models = get_openai_models()

    # Predefine all categories so models are grouped consistently.
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

    # Categorize each available model and append it to its group.
    for model_id in models:
        category = categorize_model(model_id)
        categories[category].append(model_id)

    # Remove empty categories before returning the result.
    return {
        category: model_list
        for category, model_list in categories.items()
        if model_list
    }


def get_summary_candidate_models() -> list[str]:
    """
    Return models that are usable for text editing and summarization.

    Returns:
        List of model IDs suitable for direct text-generation tasks.

    Notes:
        This excludes non-text-generation categories such as:
        embeddings, audio, image, moderation, realtime, and unknown.
    """
    categorized = get_categorized_openai_models()

    candidates = []

    # These are the categories relevant for summary and editing workflows.
    for category in [
        "cheap_text_generation",
        "text_generation",
        "strong_text_generation",
        "reasoning",
    ]:
        candidates.extend(categorized.get(category, []))

    return candidates