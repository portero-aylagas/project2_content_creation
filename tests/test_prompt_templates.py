from pathlib import Path

import pytest

from prompt_templates import (
    _format_prompt,
    _get_length_instruction,
    _get_section_scope,
    _render_section_feedback,
    build_feedback_prompt,
    build_section_prompt,
    validate_inputs,
)


def test_validate_inputs_raises_for_missing_required_field() -> None:
    with pytest.raises(ValueError, match="Missing required field"):
        validate_inputs({"x": 1}, required_fields=["combined_context"])


def test_get_section_scope_uses_sections_list() -> None:
    scope = _get_section_scope({"sections": ["market_trends", "platform_updates"]})
    assert scope == "Market Trends, Platform Updates"


def test_get_length_instruction_preserves_word_ranges() -> None:
    assert _get_length_instruction("standard: 500-700 words") == "standard: 500-700 words"
    assert "150-250 words" in _get_length_instruction("short")


def test_render_section_feedback_dict_formatting() -> None:
    text = _render_section_feedback({"market_trends": "Make it more concrete"})
    assert "- Market Trends: Make it more concrete" in text


def test_format_prompt_raises_for_missing_placeholder() -> None:
    with pytest.raises(ValueError, match="placeholder"):
        _format_prompt("Hello {name}", {"other": "x"})


def test_build_section_prompt_success() -> None:
    payload = build_section_prompt(
        {
            "combined_context": "Context line",
            "report_depth": "standard: 500-700 words",
            "audience": "executive",
            "style": "thought_leadership",
        }
    )
    assert payload["success"] is True
    assert payload["section"] == "combined_report"
    assert "prompt" in payload and isinstance(payload["prompt"], str)
    assert len(payload["prompt"]) > 0


def test_build_section_prompt_missing_context_returns_error() -> None:
    payload = build_section_prompt(
        {
            "report_depth": "standard: 500-700 words",
            "audience": "executive",
            "style": "thought_leadership",
        }
    )
    assert payload["success"] is False
    assert "error" in payload


def test_build_feedback_prompt_success() -> None:
    payload = build_feedback_prompt(
        {
            "section": "combined_report",
            "sections": ["market_trends"],
            "original_prompt": "Original prompt",
            "generated_content": "Generated content",
            "general_feedback": "Tighten recommendations.",
            "section_feedback": {"market_trends": "Use more numbers"},
            "report_depth": "standard: 500-700 words",
            "audience": "executive",
            "style": "thought_leadership",
        }
    )
    assert payload["success"] is True
    assert payload["prompt_type"] == "feedback_prompt"
    assert "prompt" in payload and isinstance(payload["prompt"], str)
    assert len(payload["prompt"]) > 0


def test_build_feedback_prompt_missing_required_returns_error() -> None:
    payload = build_feedback_prompt(
        {
            "section": "combined_report",
            "generated_content": "Generated content only",
        }
    )
    assert payload["success"] is False
    assert "error" in payload
