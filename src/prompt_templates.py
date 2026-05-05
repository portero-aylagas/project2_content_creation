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

    return data[prompt_key]


def load_prompt(prompt_key: str) -> str:
    """Backward-compatible alias for older callers."""
    return load_template(prompt_key)


# -----------------------------
# VALIDATION
# -----------------------------

def validate_inputs(metadata: Mapping[str, Any]) -> None:
    required_fields = ["section", "context"]

    for field in required_fields:
        if field not in metadata:
            raise ValueError(f"[PromptTemplates ERROR] Missing required field: {field}")


# -----------------------------
# CONTEXT PARSER
# -----------------------------

def parse_structured_context(context: object) -> Dict[str, str]:
    if isinstance(context, dict):
        return {str(key): str(value) for key, value in context.items()}

    if not isinstance(context, str):
        return {"context": str(context)}

    sections = {}
    current_section = None
    buffer = []

    for line in context.split("\n"):
        line = line.strip()

        if line.startswith("###"):
            if current_section:
                sections[current_section] = "\n".join(buffer).strip()
                buffer = []

            current_section = line.replace("###", "").strip()

        elif current_section:
            buffer.append(line)

    if current_section:
        sections[current_section] = "\n".join(buffer).strip()

    return sections


def _render_report_template(report_template: object) -> str:
    if report_template is None:
        return ""

    if isinstance(report_template, str):
        return report_template.strip()

    if isinstance(report_template, dict):
        if not report_template:
            return ""
        return json.dumps(report_template, indent=2, ensure_ascii=False)

    return str(report_template).strip()


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
        validate_inputs(metadata)

        prompt_key = str(metadata.get("prompt_type", "market_analysis"))
        template = load_template(prompt_key)

        style = str(metadata.get("style", "thought_leadership"))
        style_desc = STYLES.get(style, STYLES["thought_leadership"])

        structured_context = parse_structured_context(metadata["context"])
        structured_block = "".join(
            f"\n### {section_name}\n{content}\n"
            for section_name, content in structured_context.items()
        ).strip()

        section_instruction = get_section_instructions(str(metadata["section"]))
        report_template_block = _render_report_template(
            metadata.get("report_template")
        )
        markets = metadata.get("markets", [])
        market_list = ", ".join(str(market) for market in markets)

        prompt_values = {
            "section": str(metadata["section"]),
            "timeframe": str(metadata.get("month", "N/A")),
            "markets": market_list,
            "structured_block": structured_block or str(metadata.get("context", "")),
            "style_desc": style_desc,
            "section_instruction": section_instruction,
            "context": str(metadata.get("context", "")),
            "report_template": metadata.get("report_template", ""),
            "report_template_block": report_template_block,
            "report_depth": str(metadata.get("report_depth", "")),
            "audience": str(metadata.get("audience", "")),
            "year": str(metadata.get("year", "")),
        }

        prompt = _format_prompt(template, prompt_values).strip()

        return {
            "section": str(metadata["section"]),
            "prompt": prompt,
            "max_tokens": int(metadata.get("max_tokens", 600)),
            "temperature": float(metadata.get("temperature", 0.2)),
            "prompt_type": prompt_key,
            "success": True,
        }

    except Exception as e:
        return {
            "section": str(metadata.get("section", "unknown")),
            "error": str(e),
            "success": False,
        }


def build_feedback_prompt(metadata: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validate_inputs(metadata)

        template = load_template("feedback_prompt")
        style = str(metadata.get("style", "thought_leadership"))
        style_desc = STYLES.get(style, STYLES["thought_leadership"])
        section_instruction = get_section_instructions(str(metadata["section"]))
        markets = metadata.get("markets", [])
        market_list = ", ".join(str(market) for market in markets)

        prompt_values = {
            "section": str(metadata["section"]),
            "timeframe": str(metadata.get("month", "N/A")),
            "markets": market_list,
            "context": str(metadata.get("context", "")),
            "user_feedback": str(
                metadata.get("user_feedback", metadata.get("feedback_text", ""))
            ),
            "style_desc": style_desc,
            "section_instruction": section_instruction,
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
