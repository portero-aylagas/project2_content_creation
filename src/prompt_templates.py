from typing import Any, Dict, Mapping
import json
from pathlib import Path

# -----------------------------
# GLOBAL CONFIG
# -----------------------------

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

STYLES = {
    "thought_leadership": "insightful, expert-level, opinionated",
    "storytelling": "emotional, narrative-driven, engaging",
    "educational": "clear, structured, value-driven",
    "contrarian": "challenging assumptions, bold perspective",
    "minimalist": "concise, sharp, high-signal",
}

# -----------------------------
# TEMPLATE LOADER
# -----------------------------

def load_template(prompt_key: str) -> str:
    template_path = TEMPLATES_DIR / "prompt_generation.json"

    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if prompt_key not in data:
        raise KeyError(
            f"[PromptTemplates ERROR] Prompt '{prompt_key}' not found. "
            f"Available keys: {list(data.keys())}"
        )

    template_value = data[prompt_key]

    if isinstance(template_value, list):
        return "\n".join(str(line) for line in template_value)

    return str(template_value)


def load_prompt(prompt_key: str) -> str:
    """Backward-compatible alias for older callers."""
    return load_template(prompt_key)


# -----------------------------
# VALIDATION
# -----------------------------

def validate_inputs(
    metadata: Mapping[str, Any], required_fields: list[str] | None = None
) -> None:
    if required_fields is None:
        required_fields = ["context"]

    for field in required_fields:
        if field not in metadata:
            raise ValueError(f"[PromptTemplates ERROR] Missing required field: {field}")


# -----------------------------
# SECTION INSTRUCTIONS
# -----------------------------

def get_section_instructions(section: str) -> str:
    mapping = {
        "executive_summary": "- Synthesize the highest-value cross-market conclusions",
        "market_trends": "- Focus on macro patterns, shifts, and forward-looking signals",
        "platform_updates": "- Focus on product, policy, monetization, and discovery changes across platforms",
        "competitor_intelligence": "- Focus on competitive moves, positioning, and implications for Believe",
        "independent_artist_economy": "- Focus on indie artist economics, monetization pressure, and strategic relevance",
        "market_opportunities": "- Focus on actionable growth opportunities, prioritization, and trade-offs",
        "data_sources_used": "- List the sources used and keep the section factual and concise",
        "financial_analysis": "- Focus on revenue, margins, cost structure, and growth dynamics",
        "operations": "- Focus on execution, efficiency, and operational changes",
        "strategy": "- Focus on positioning, differentiation, and strategic direction",
        "portfolio": "- Focus on asset composition, shifts, and strategic implications",
    }

    return mapping.get(section, "- Provide high-quality, insight-driven analysis")


def _get_section_scope(metadata: Mapping[str, Any]) -> str:
    sections = metadata.get("sections")
    if isinstance(sections, list) and sections:
        return ", ".join(
            str(section_name).replace("_", " ").title()
            for section_name in sections
        )

    section = metadata.get("section", "")
    if section:
        return str(section).replace("_", " ").title()

    return "Selected Report Sections"


def _get_section_instruction_block(metadata: Mapping[str, Any]) -> str:
    sections = metadata.get("sections")

    if isinstance(sections, list) and sections:
        instructions = []
        for section_name in sections:
            instruction = get_section_instructions(str(section_name))
            if instruction not in instructions:
                instructions.append(instruction)
        return "\n".join(instructions)

    return get_section_instructions(str(metadata.get("section", "")))


def _get_length_instruction(report_depth: str) -> str:
    if "words" in str(report_depth).lower():
        return str(report_depth)

    length_map = {
        "short": "Keep the response concise and high-signal, around 150-250 words.",
        "standard": "Target a balanced level of detail, around 250-400 words.",
        "detailed": "Provide a more developed response, around 400-700 words.",
    }
    return length_map.get(
        str(report_depth),
        "Target a balanced level of detail, around 250-400 words.",
    )


# -----------------------------
# MAIN PROMPT BUILDER
# -----------------------------

def _format_prompt(template: str, values: Dict[str, Any]) -> str:
    try:
        return template.format(**values)
    except KeyError as exc:
        missing_key = exc.args[0]
        raise ValueError(
            f"Template placeholder '{missing_key}' is not supported by the "
            "current prompt payload."
        ) from exc


def build_section_prompt(metadata: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validate_inputs(metadata, required_fields=["combined_context"])

        prompt_key = str(metadata.get("prompt_type", "market_analysis"))
        template = load_template(prompt_key)

        style_desc = STYLES.get(
            str(metadata.get("style", "thought_leadership")),
            STYLES["thought_leadership"],
        )
        report_depth = str(metadata.get("report_depth", "standard"))
        audience = str(metadata.get("audience", ""))
        length_instruction = _get_length_instruction(report_depth)
        combined_context = str(metadata.get("combined_context", ""))

        prompt_values = {
            "combined_context": combined_context,
            "style_desc": style_desc,
            "report_depth": report_depth,
            "audience": audience,
            "length_instruction": length_instruction,
        }

        prompt = _format_prompt(template, prompt_values).strip()

        return {
            "section": "combined_report",
            "prompt": prompt,
            "max_tokens": int(metadata.get("max_tokens", 600)),
            "temperature": float(metadata.get("temperature", 0.2)),
            "prompt_type": prompt_key,
            "success": True,
        }

    except Exception as e:
        return {
            "section": "combined_report",
            "error": str(e),
            "success": False,
        }


def build_feedback_prompt(metadata: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validate_inputs(metadata)

        template = load_template("feedback_prompt")
        style = str(metadata.get("style", "thought_leadership"))
        style_desc = STYLES.get(style, STYLES["thought_leadership"])
        section_scope = _get_section_scope(metadata)
        section_instruction = _get_section_instruction_block(metadata)
        markets = metadata.get("markets", [])
        market_list = ", ".join(str(market) for market in markets)
        report_depth = str(metadata.get("report_depth", "standard"))
        audience = str(metadata.get("audience", ""))
        length_instruction = _get_length_instruction(report_depth)

        prompt_values = {
            "section": str(metadata.get("section", section_scope)),
            "section_scope": section_scope,
            "timeframe": str(metadata.get("month", "N/A")),
            "markets": market_list,
            "combined_context": str(metadata.get("context", "")),
            "context": str(metadata.get("context", "")),
            "user_feedback": str(
                metadata.get("user_feedback", metadata.get("feedback_text", ""))
            ),
            "style": style,
            "style_desc": style_desc,
            "section_instruction": section_instruction,
            "report_depth": report_depth,
            "audience": audience,
            "length_instruction": length_instruction,
        }

        prompt = _format_prompt(template, prompt_values).strip()

        return {
            "section": str(metadata["section"]),
            "prompt": prompt,
            "max_tokens": int(metadata.get("max_tokens", 600)),
            "temperature": float(metadata.get("temperature", 0.2)),
            "prompt_type": "feedback_prompt",
            "success": True,
        }

    except Exception as e:
        return {
            "section": str(metadata.get("section", "unknown")),
            "error": str(e),
            "success": False,
        }


def build_prompt(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Backward-compatible alias for the section prompt builder."""
    return build_section_prompt(metadata)
