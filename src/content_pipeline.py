from __future__ import annotations

from copy import deepcopy


SECTION_ORDER = [
    "executive_summary",
    "market_trends",
    "platform_updates",
    "competitor_intelligence",
    "independent_artist_economy",
    "market_opportunities",
    "data_sources_used",
]

SECTION_TITLES = {
    "executive_summary": "Executive Summary",
    "market_trends": "Market Trends",
    "platform_updates": "Platform Updates",
    "competitor_intelligence": "Competitor Intelligence",
    "independent_artist_economy": "Independent Artist Economy",
    "market_opportunities": "Market Opportunities",
    "data_sources_used": "Data Sources Used",
}


MOCK_CONTENT_PIPELINE_RESPONSE = {
    "report": {
        "full_text": (
            "BELIEVE MARKET INTELLIGENCE REPORT\n\n"
            "## Executive Summary\n"
            "MOCK: Believe saw stable momentum across DE, UK, and FR with "
            "platform policy changes creating both opportunity and risk.\n\n"
            "## Market Trends\n"
            "MOCK: Germany remains digital-restructuring focused, the UK "
            "continues to over-index on independent discovery, and France "
            "retains a strong domestic-language streaming bias.\n\n"
            "## Platform Updates\n"
            "MOCK: Spotify, Apple Music, Deezer, YouTube Music, and TikTok "
            "all require monthly monitoring for monetization and discovery "
            "shifts.\n\n"
            "## Competitor Intelligence\n"
            "MOCK: AWAL, DistroKid, Virgin Music Group, and CD Baby remain "
            "the core competitive watchlist for Believe.\n\n"
            "## Independent Artist Economy\n"
            "MOCK: Independent artists continue gaining share, but revenue "
            "concentration and platform thresholds remain structural risks.\n\n"
            "## Market Opportunities\n"
            "MOCK: Priorities include Premium Solutions upsell, local "
            "editorial leverage, and artist development in DE, UK, and FR.\n\n"
            "## Data Sources Used\n"
            "MOCK: Believe internal KB files only. No live external retrieval "
            "was used."
        ),
        "word_count": 987,
        "sections": {
            "executive_summary": (
                "MOCK: Summary of the most important monthly developments."
            ),
            "market_trends": (
                "MOCK: Market-level updates for Germany, UK, France, and "
                "global context."
            ),
            "platform_updates": (
                "MOCK: Platform policy and product changes affecting artists."
            ),
            "competitor_intelligence": (
                "MOCK: Competitor moves, risks, and Believe implications."
            ),
            "independent_artist_economy": (
                "MOCK: Independent artist revenue and growth dynamics."
            ),
            "market_opportunities": (
                "MOCK: Recommended strategic opportunities for Believe."
            ),
            "data_sources_used": (
                "MOCK: Internal knowledge-base source references."
            ),
        },
    },
    "metadata": {
        "sections_generated": 7,
        "kb_files_used": 9,
    },
}


def generate_mock_report(report_request: dict[str, object]) -> dict[str, object]:
    """
    Return a mocked content-pipeline response shaped like the future real
    pipeline output.
    """
    mock_response = deepcopy(MOCK_CONTENT_PIPELINE_RESPONSE)
    mock_response["metadata"].update(
        {
            "report_period": report_request["report_period"],
            "markets": report_request["markets"],
            "selected_sections": report_request["sections"],
            "report_depth": report_request["report_depth"],
            "audience": report_request["audience"],
            "selected_model": report_request["model"],
            "temperature": report_request["temperature"],
            "mock": True,
        }
    )
    return mock_response


def iterate_mock_report(feedback_request: dict[str, object]) -> dict[str, object]:
    """
    Simulate the iterate stage by accepting original text, original inputs,
    and free-text feedback, then returning a revised mock report payload.
    """
    original_report_text = str(feedback_request["original_report_text"])
    original_inputs = dict(feedback_request["original_inputs"])
    feedback_text = str(feedback_request["feedback_text"]).strip()
    scope = str(feedback_request["scope"])
    target_section = str(feedback_request["target_section"])

    revised_response = generate_mock_report(original_inputs)
    revised_sections = dict(revised_response["report"]["sections"])

    iteration_note = (
        "MOCK ITERATION APPLIED\n"
        f"Scope: {scope}\n"
        f"Target section: {target_section}\n"
        f"Feedback: {feedback_text}\n"
        "Original inputs were provided to the iterate step."
    )

    if scope == "single_section" and target_section in revised_sections:
        revised_sections[target_section] = (
            f"{revised_sections[target_section]}\n\n{iteration_note}"
        )
    else:
        for section_name in revised_sections:
            revised_sections[section_name] = (
                f"{revised_sections[section_name]}\n\n{iteration_note}"
            )

    revised_response["report"]["sections"] = revised_sections
    revised_response["report"]["full_text"] = _assemble_report_from_sections(
        revised_sections
    )
    revised_response["report"]["word_count"] = _count_words(
        revised_response["report"]["full_text"]
    )
    revised_response["metadata"].update(
        {
            "iteration_applied": True,
            "feedback_scope": scope,
            "feedback_target_section": target_section,
            "feedback_text": feedback_text,
            "original_report_word_count": _count_words(original_report_text),
            "original_inputs": original_inputs,
            "mock": True,
        }
    )

    return revised_response


def _assemble_report_from_sections(sections: dict[str, str]) -> str:
    report_parts = ["BELIEVE MARKET INTELLIGENCE REPORT"]

    for section_name in SECTION_ORDER:
        section_text = sections.get(section_name)
        if not section_text:
            continue

        section_title = SECTION_TITLES[section_name]
        report_parts.append(f"## {section_title}\n{section_text}")

    return "\n\n".join(report_parts)


def _count_words(text: str) -> int:
    return len(text.split())
