"""Content pipeline orchestration.

This module coordinates:
1. KB loading and context assembly,
2. prompt generation,
3. LLM generation for initial reports and feedback-based revisions.
"""

from __future__ import annotations

from datetime import date

from document_processor import load_knowledge_base
from knowledge_base import get_section_context
from llm_integration import generate_text
from prompt_templates import build_feedback_prompt, build_prompt

MARKET_NAME_MAP = {
    "DE": "Germany",
    "UK": "UK",
    "FR": "France",
}

SECTION_NAME_MAP = {
    "market_trends": "market_trends",
    "platform_updates": "platform_updates",
    "competitor_intelligence": "competition",
    "independent_artist_economy": "artist_economy",
    "market_opportunities": "opportunities",
}


def generate_report(report_request: dict[str, object]) -> dict[str, object]:
    """Generate a report from UI request parameters.

    Args:
        report_request (dict): Request payload from UI with date, sections,
        markets, and generation controls.

    Returns:
        dict: Pipeline response including generated report text, prompt payload,
        raw combined KB context, LLM metadata, and usage/cost metrics.
    """
    required_fields = ("month", "year", "report_period", "markets", "sections")
    missing_fields = [
        field for field in required_fields if field not in report_request
    ]
    if missing_fields:
        raise ValueError(
            "Report request is missing required fields: "
            + ", ".join(missing_fields)
        )

    markets = report_request["markets"]
    sections = report_request["sections"]

    if not isinstance(markets, list) or not all(
        isinstance(market, str) for market in markets
    ):
        raise TypeError("Report request field 'markets' must be a list[str].")

    if not isinstance(sections, list) or not all(
        isinstance(section, str) for section in sections
    ):
        raise TypeError("Report request field 'sections' must be a list[str].")

    normalized_request = {
        "month": str(report_request["month"]),
        "year": str(report_request["year"]),
        "report_period": str(report_request["report_period"]),
        "markets": markets,
        "sections": sections,
        "report_depth": str(report_request.get("report_depth", "")),
        "audience": str(report_request.get("audience", "")),
        "style": str(report_request.get("style", "")),
        "model": str(report_request.get("model", "")),
        "temperature": float(report_request.get("temperature", 0.2)),
    }

    # Convert UI-facing labels/codes into KB-internal keys.
    kb_markets = [
        MARKET_NAME_MAP.get(market_code, market_code)
        for market_code in normalized_request["markets"]
    ]
    kb_sections = [
        SECTION_NAME_MAP.get(section_name, section_name)
        for section_name in normalized_request["sections"]
    ]

    kb_data = load_knowledge_base()
    kb_period = f"{normalized_request['year']} {normalized_request['month']}"
    combined_context = get_section_context(
        kb_data,
        kb_sections,
        kb_period,
        kb_markets,
    )

    if not isinstance(combined_context, str):
        raise TypeError(
            "knowledge_base.get_section_context() must return a string."
        )

    prompt_payload = build_prompt(
        {
            "combined_context": combined_context,
            "report_depth": normalized_request["report_depth"],
            "audience": normalized_request["audience"],
            "style": normalized_request["style"],
        }
    )

    if prompt_payload.get("error"):
        raise RuntimeError(prompt_payload["error"])

    prompt_payload["temperature"] = normalized_request["temperature"]
    llm_response = generate_text(
        prompt_payload,
        model=normalized_request["model"] or None,
        temperature=normalized_request["temperature"],
    )

    if not llm_response.get("success"):
        raise RuntimeError(str(llm_response.get("error", "LLM generation failed.")))

    generated_text = str(llm_response.get("generated_text", ""))

    return {
        "report": {
            "full_text": generated_text,
            "word_count": len(generated_text.split()),
            "sections": normalized_request["sections"],
        },
        "prompt": prompt_payload,
        "combined_context": combined_context,
        "llm_response": llm_response,
        "metadata": {
            "generated_on": date.today().isoformat(),
            "sections_selected": normalized_request["sections"],
            "markets_selected": normalized_request["markets"],
            "report_period": normalized_request["report_period"],
            "model_used": llm_response.get("model_used", normalized_request["model"]),
            "temperature_used": llm_response.get(
                "temperature_used", normalized_request["temperature"]
            ),
            "tokens_used": llm_response.get("tokens_used", 0),
            "cost_usd": llm_response.get("cost_usd", 0.0),
        },
    }


def iterate_report(feedback_request: dict[str, object]) -> dict[str, object]:
    """Generate a revised report version using user feedback.

    Args:
        feedback_request (dict): Payload containing previous prompt/output,
        general + section-level feedback, and current generation controls.

    Returns:
        dict: Revised report payload and LLM metadata for the feedback pass.
    """
    original_inputs = feedback_request.get("original_inputs", {})
    original_report_text = str(feedback_request.get("original_report_text", ""))
    original_prompt = str(feedback_request.get("original_prompt", ""))

    if not isinstance(original_inputs, dict):
        raise TypeError("Feedback field 'original_inputs' must be a dict payload.")

    if not original_report_text.strip():
        raise ValueError("Feedback field 'original_report_text' is required.")

    if not original_prompt.strip():
        raise ValueError("Feedback field 'original_prompt' is required.")

    model = str(feedback_request.get("model", original_inputs.get("model", "")))
    temperature = float(
        feedback_request.get("temperature", original_inputs.get("temperature", 0.2))
    )
    report_depth = str(
        feedback_request.get(
            "report_depth", original_inputs.get("report_depth", "")
        )
    )
    audience = str(
        feedback_request.get("audience", original_inputs.get("audience", ""))
    )
    style = str(feedback_request.get("style", original_inputs.get("style", "")))
    feedback_prompt_payload = build_feedback_prompt(
        {
            "section": "combined_report",
            "sections": original_inputs.get("sections", []),
            "original_prompt": original_prompt,
            "generated_content": original_report_text,
            "report_depth": report_depth,
            "audience": audience,
            "style": style,
            "feedback_text": str(feedback_request.get("feedback_text", "")),
            "general_feedback": str(feedback_request.get("general_feedback", "")),
            "section_feedback": feedback_request.get("section_feedback", {}),
        }
    )

    if feedback_prompt_payload.get("error"):
        raise RuntimeError(feedback_prompt_payload["error"])

    feedback_prompt_payload["temperature"] = temperature
    llm_response = generate_text(
        feedback_prompt_payload,
        model=model or None,
        temperature=temperature,
    )

    if not llm_response.get("success"):
        raise RuntimeError(str(llm_response.get("error", "LLM generation failed.")))

    revised_text = str(llm_response.get("generated_text", ""))

    return {
        "report": {
            "full_text": revised_text,
            "word_count": len(revised_text.split()),
            "sections": list(original_inputs.get("sections", [])),
        },
        "feedback_prompt": feedback_prompt_payload,
        "llm_response": llm_response,
        "metadata": {
            "generated_on": date.today().isoformat(),
            "sections_selected": list(original_inputs.get("sections", [])),
            "markets_selected": list(original_inputs.get("markets", [])),
            "report_period": str(original_inputs.get("report_period", "")),
            "feedback_text": str(feedback_request.get("feedback_text", "")),
            "general_feedback": str(feedback_request.get("general_feedback", "")),
            "section_feedback": feedback_request.get("section_feedback", {}),
            "model_used": llm_response.get("model_used", model),
            "temperature_used": llm_response.get(
                "temperature_used", temperature
            ),
            "tokens_used": llm_response.get("tokens_used", 0),
            "cost_usd": llm_response.get("cost_usd", 0.0),
        },
    }
