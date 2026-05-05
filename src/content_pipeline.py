from __future__ import annotations

from datetime import date
from importlib import import_module


def generate_report(report_request: dict[str, object]) -> dict[str, object]:
    """
    Load the knowledge base and return the combined text selected from the
    knowledge-base layer based on the UI inputs.
    """
    report_request = _validate_report_request(report_request)
    kb_data = _ingest_knowledge_base()
    # print ( "############################## KB DATA ####################################")
    # print(kb_data)

    context_payload = _select_context(report_request, kb_data)
    print ( "############################## REPORT REQUEST ####################################")
    print(report_request)
    print ( "############################## CONTEXT PAYLOAD ####################################")
    print(context_payload)
    print ( "########################## END OF CONTEXT PAYLOAD ####################################")
    print ( "###########################################################################################")
    return {
        "report": {
            "full_text": context_payload["context"],
            "word_count": len(context_payload["context"].split()),
            "sections": report_request["sections"],
        },
        "metadata": {
            "generated_on": date.today().isoformat(),
            "sections_selected": report_request["sections"],
            "markets_selected": report_request["markets"],
            "report_period": report_request["report_period"],
            "sections_used": context_payload["sections_used"],
        },
    }


def iterate_report(feedback_request: dict[str, object]) -> dict[str, object]:
    """
    Rebuild the selected knowledge-base context from the original inputs.

    Feedback is still accepted by the UI, but this pipeline version only
    returns the regenerated combined context from the selected KB sections.
    """
    original_inputs = _validate_report_request(
        dict(feedback_request.get("original_inputs", {}))
    )
    regenerated_report = generate_report(original_inputs)
    regenerated_report["metadata"]["feedback_text"] = str(
        feedback_request.get("feedback_text", "")
    )
    return regenerated_report


def _ingest_knowledge_base() -> dict[str, object]:
    module = import_module("document_processor")
    processor = getattr(module, "load_knowledge_base", None)

    if not callable(processor):
        raise RuntimeError(
            "document_processor.py must expose load_knowledge_base()."
        )

    kb_data = processor()
    if not isinstance(kb_data, dict):
        raise TypeError(
            "document_processor.load_knowledge_base() must return a dict."
        )

    return kb_data


def _select_context(
    report_request: dict[str, object],
    kb_data: dict[str, object],
) -> dict[str, object]:
    module = import_module("knowledge_base")
    selector = getattr(module, "get_section_context", None)

    if not callable(selector):
        raise RuntimeError(
            "knowledge_base.py must expose get_section_context()."
        )

    kb_period = _build_kb_period(report_request)
    payload = selector(
        kb_data=kb_data,
        sections=report_request["sections"],
        date=kb_period,
        markets=report_request["markets"],
    )
    _require_keys(payload, ("context", "sections_used"), "knowledge_base")
    return payload


def _build_kb_period(report_request: dict[str, object]) -> str:
    return f"{report_request['year']} {report_request['month']}"


def _validate_report_request(
    report_request: dict[str, object],
) -> dict[str, object]:
    required_fields = (
        "month",
        "year",
        "report_period",
        "markets",
        "sections",
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
        "report_depth": str(report_request.get("report_depth", "")),
        "audience": str(report_request.get("audience", "")),
        "style": str(report_request.get("style", "")),
        "model": str(report_request.get("model", "")),
        "temperature": float(report_request.get("temperature", 0.0)),
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
