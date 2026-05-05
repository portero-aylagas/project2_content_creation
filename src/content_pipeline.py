from __future__ import annotations

from datetime import date
from importlib import import_module


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

MOCK_SECTION_CONTENT = {
    "executive_summary": (
        "MOCK: Believe saw steady momentum across DE, UK, and FR, with the "
        "strongest opportunities coming from sharper local positioning, "
        "platform responsiveness, and better use of Premium Solutions."
    ),
    "market_trends": (
        "MOCK: Germany remains focused on digital restructuring, the UK "
        "continues to reward independent discovery mechanics, and France "
        "retains strong domestic-language demand with local editorial leverage."
    ),
    "platform_updates": (
        "MOCK: Spotify, Apple Music, Deezer, YouTube Music, and TikTok all "
        "require active monitoring because monetization and discovery dynamics "
        "continue to shift month by month."
    ),
    "competitor_intelligence": (
        "MOCK: AWAL, DistroKid, Virgin Music Group, and other distribution "
        "players remain the core watchlist for Believe's competitive response."
    ),
    "independent_artist_economy": (
        "MOCK: Independent artists continue to gain strategic relevance, but "
        "revenue concentration and platform thresholds remain structural risks."
    ),
    "market_opportunities": (
        "MOCK: The clearest opportunities are deeper Premium Solutions upsell, "
        "local editorial leverage, and better market-by-market positioning."
    ),
    "data_sources_used": (
        "MOCK: Internal knowledge-base material only. No live retrieval or "
        "external source refresh was used in this mocked response."
    ),
}


def generate_report(report_request: dict[str, object]) -> dict[str, object]:
    """
    Orchestrate report generation:
    1. ingest the full KB
    2. select context per section
    3. build prompts per section
    4. generate text per section
    5. assemble the final report
    """
    report_request = _validate_report_request(report_request)

    kb_data = _ingest_knowledge_base()
    generated_sections: dict[str, str] = {}
    kb_files_used: set[str] = set()

    for section_name in report_request["sections"]:
        context_payload = _select_section_context(
            section_name=section_name,
            markets=report_request["markets"],
            kb_data=kb_data,
        )
        prompt_payload = _build_section_prompt(
            section_name=section_name,
            context=context_payload["context"],
            report_request=report_request,
            report_template=_get_report_template(kb_data),
        )
        generation_payload = _generate_section_text(
            section_name=section_name,
            prompt=prompt_payload["prompt"],
            max_tokens=prompt_payload["max_tokens"],
            model=report_request["model"],
            temperature=report_request["temperature"],
        )

        generated_sections[section_name] = str(
            generation_payload["generated_text"]
        )
        kb_files_used.update(context_payload["sources_used"])

    full_text = _assemble_report(
        report_period=report_request["report_period"],
        markets=report_request["markets"],
        sections=generated_sections,
    )

    return {
        "report": {
            "full_text": full_text,
            "word_count": len(full_text.split()),
            "sections": generated_sections,
        },
        "metadata": {
            "generated_on": date.today().isoformat(),
            "sections_generated": len(generated_sections),
            "kb_files_used": sorted(kb_files_used),
        },
    }


def iterate_report(feedback_request: dict[str, object]) -> dict[str, object]:
    """
    Accept the original report text, the original inputs, and feedback, then
    regenerate either the whole report or a single section.
    """
    feedback_request = _validate_feedback_request(feedback_request)
    original_inputs = dict(feedback_request["original_inputs"])

    if feedback_request["scope"] == "single_section":
        original_inputs["sections"] = [feedback_request["target_section"]]

    revised_report = generate_report(original_inputs)
    revised_report["metadata"].update(
        {
            "iteration_applied": True,
            "feedback_text": feedback_request["feedback_text"],
            "feedback_scope": feedback_request["scope"],
            "feedback_target_section": feedback_request["target_section"],
        }
    )
    return revised_report


def _ingest_knowledge_base() -> dict[str, object]:
    module = import_module("document_processor")
    processor = getattr(module, "process_markdown_files", None)

    if not callable(processor):
        raise RuntimeError(
            "document_processor.py must expose process_markdown_files()."
        )

    kb_data = processor()
    if not isinstance(kb_data, dict):
        raise TypeError(
            "document_processor.process_markdown_files() must return a dict."
        )

    return kb_data


def _select_section_context(
    section_name: str,
    markets: list[str],
    kb_data: dict[str, object],
) -> dict[str, object]:
    module = import_module("knowledge_base")
    selector = getattr(module, "get_section_context", None)

    if not callable(selector):
        raise RuntimeError(
            "knowledge_base.py must expose get_section_context()."
        )

    payload = selector(
        {
            "section": section_name,
            "markets": markets,
            "kb_data": kb_data,
        }
    )
    _require_keys(payload, ("context", "sources_used"), "knowledge_base")
    return payload


def _build_section_prompt(
    section_name: str,
    context: str,
    report_request: dict[str, object],
    report_template: object,
) -> dict[str, object]:
    module = import_module("prompt_templates")
    builder = getattr(module, "build_section_prompt", None)

    if not callable(builder):
        raise RuntimeError(
            "prompt_templates.py must expose build_section_prompt()."
        )

    payload = builder(
        {
            "section": section_name,
            "context": context,
            "month": report_request["report_period"],
            "markets": report_request["markets"],
            "report_depth": report_request["report_depth"],
            "audience": report_request["audience"],
            "report_template": report_template,
        }
    )
    _require_keys(payload, ("prompt", "max_tokens"), "prompt_templates")
    return payload


def _generate_section_text(
    section_name: str,
    prompt: str,
    max_tokens: object,
    model: str,
    temperature: float,
) -> dict[str, object]:
    module = import_module("llm_integration")
    generator = getattr(module, "generate_section", None)

    if not callable(generator):
        raise RuntimeError(
            "llm_integration.py must expose generate_section()."
        )

    payload = generator(
        {
            "section": section_name,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "model": model,
            "temperature": temperature,
        }
    )
    _require_keys(payload, ("generated_text",), "llm_integration")
    return payload


def _get_report_template(kb_data: dict[str, object]) -> object:
    primary_kb = kb_data.get("primary", {})
    if not isinstance(primary_kb, dict):
        return {}
    return primary_kb.get("believe_report_template", {})


def _assemble_report(
    report_period: str,
    markets: list[str],
    sections: dict[str, str],
) -> str:
    report_parts = [
        "BELIEVE MARKET INTELLIGENCE REPORT",
        f"Month: {report_period}",
        f"Generated: {date.today().isoformat()}",
        f"Markets: {' | '.join(markets)}",
        "━━━━━━━━━━━━━━━",
    ]

    for section_name in SECTION_ORDER:
        section_text = sections.get(section_name)
        if not section_text:
            continue

        report_parts.append(
            f"## {SECTION_TITLES.get(section_name, section_name)}\n"
            f"{section_text}"
        )

    return "\n\n".join(report_parts)


def _validate_report_request(
    report_request: dict[str, object],
) -> dict[str, object]:
    required_fields = (
        "month",
        "year",
        "report_period",
        "markets",
        "sections",
        "report_depth",
        "audience",
        "model",
        "temperature",
    )

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

    return {
        "month": str(report_request["month"]),
        "year": str(report_request["year"]),
        "report_period": str(report_request["report_period"]),
        "markets": markets,
        "sections": sections,
        "report_depth": str(report_request["report_depth"]),
        "audience": str(report_request["audience"]),
        "model": str(report_request["model"]),
        "temperature": float(report_request["temperature"]),
    }


def _validate_feedback_request(
    feedback_request: dict[str, object],
) -> dict[str, object]:
    required_fields = (
        "original_report_text",
        "original_inputs",
        "feedback_text",
        "scope",
        "target_section",
    )

    missing_fields = [
        field for field in required_fields if field not in feedback_request
    ]
    if missing_fields:
        raise ValueError(
            "Feedback request is missing required fields: "
            + ", ".join(missing_fields)
        )

    original_inputs = feedback_request["original_inputs"]
    if not isinstance(original_inputs, dict):
        raise TypeError(
            "Feedback field 'original_inputs' must be a dict payload."
        )

    scope = str(feedback_request["scope"])
    if scope not in {"full_report", "single_section"}:
        raise ValueError("Feedback scope must be 'full_report' or 'single_section'.")

    target_section = str(feedback_request["target_section"])
    if target_section and target_section not in SECTION_ORDER:
        raise ValueError(f"Unknown feedback target section: {target_section}")

    return {
        "original_report_text": str(feedback_request["original_report_text"]),
        "original_inputs": _validate_report_request(original_inputs),
        "feedback_text": str(feedback_request["feedback_text"]),
        "scope": scope,
        "target_section": target_section,
    }


def _require_keys(
    payload: object,
    required_keys: tuple[str, ...],
    step_name: str,
) -> None:
    if not isinstance(payload, dict):
        raise TypeError(f"{step_name} must return a dict payload.")

    missing_keys = [key for key in required_keys if key not in payload]
    if missing_keys:
        raise KeyError(
            f"{step_name} returned an incomplete payload. Missing keys: "
            + ", ".join(missing_keys)
        )


def generate_mock_report(report_request: dict[str, object]) -> dict[str, object]:
    """
    UI compatibility wrapper.
    """
    report_request = _validate_report_request(report_request)
    sections = {
        section_name: _build_mock_section_text(section_name, report_request)
        for section_name in report_request["sections"]
    }
    full_text = _assemble_report(
        report_period=report_request["report_period"],
        markets=report_request["markets"],
        sections=sections,
    )
    return {
        "report": {
            "full_text": full_text,
            "word_count": len(full_text.split()),
            "sections": sections,
        },
        "metadata": {
            "generated_on": date.today().isoformat(),
            "sections_generated": len(sections),
            "kb_files_used": [],
            "mock": True,
            "report_request": report_request,
        },
    }


def iterate_mock_report(feedback_request: dict[str, object]) -> dict[str, object]:
    """
    UI compatibility wrapper.
    """
    original_inputs = _validate_report_request(
        dict(feedback_request.get("original_inputs", {}))
    )
    general_feedback = str(feedback_request.get("general_feedback", "")).strip()
    section_feedback = feedback_request.get("section_feedback", {})

    if not isinstance(section_feedback, dict):
        section_feedback = {}

    revised_response = generate_mock_report(original_inputs)
    revised_sections = dict(revised_response["report"]["sections"])

    if general_feedback:
        for section_name in revised_sections:
            revised_sections[section_name] = (
                f"{revised_sections[section_name]}\n\n"
                f"MOCK REVISION NOTE: Applied general feedback -> "
                f"{general_feedback}"
            )

    for section_name, feedback_text in section_feedback.items():
        if section_name in revised_sections and str(feedback_text).strip():
            revised_sections[section_name] = (
                f"{revised_sections[section_name]}\n\n"
                f"MOCK REVISION NOTE: Applied section feedback -> "
                f"{str(feedback_text).strip()}"
            )

    revised_response["report"]["sections"] = revised_sections
    revised_response["report"]["full_text"] = _assemble_report(
        report_period=original_inputs["report_period"],
        markets=original_inputs["markets"],
        sections=revised_sections,
    )
    revised_response["report"]["word_count"] = len(
        revised_response["report"]["full_text"].split()
    )
    revised_response["metadata"].update(
        {
            "iteration_applied": True,
            "feedback_text": str(feedback_request.get("feedback_text", "")),
            "general_feedback": general_feedback,
            "section_feedback": section_feedback,
        }
    )
    return revised_response


def _build_mock_section_text(
    section_name: str,
    report_request: dict[str, object],
) -> str:
    base_text = MOCK_SECTION_CONTENT.get(
        section_name,
        "MOCK: Section content placeholder.",
    )

    return (
        f"{base_text}\n\n"
        f"Mock settings: depth={report_request['report_depth']}, "
        f"audience={report_request['audience']}, "
        f"style={report_request.get('style', '')}."
    )
