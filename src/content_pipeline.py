from __future__ import annotations

from datetime import date

from document_processor import load_knowledge_base
from knowledge_base import get_section_context

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
    """
    Load the KB through document_processor and pass the selected sections,
    markets, and date into knowledge_base to get the combined context string.
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
    }

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

    return {
        "report": {
            "full_text": combined_context,
            "word_count": len(combined_context.split()),
            "sections": normalized_request["sections"],
        },
        "metadata": {
            "generated_on": date.today().isoformat(),
            "sections_selected": normalized_request["sections"],
            "markets_selected": normalized_request["markets"],
            "report_period": normalized_request["report_period"],
        },
    }


def iterate_report(feedback_request: dict[str, object]) -> dict[str, object]:
    """
    Rebuild the selected knowledge-base context from the original inputs and
    attach the submitted feedback to the metadata.
    """
    original_inputs = feedback_request.get("original_inputs", {})

    if not isinstance(original_inputs, dict):
        raise TypeError("Feedback field 'original_inputs' must be a dict payload.")

    regenerated_report = generate_report(original_inputs)
    regenerated_report["metadata"]["feedback_text"] = str(
        feedback_request.get("feedback_text", "")
    )
    return regenerated_report
