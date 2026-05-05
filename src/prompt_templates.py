from typing import Dict, Any
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
    "minimalist": "concise, sharp, high-signal"
}

# -----------------------------
# TEMPLATE LOADER (UPDATED)
# -----------------------------

def load_prompt(prompt_key: str) -> str:
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


# -----------------------------
# VALIDATION
# -----------------------------

def validate_inputs(metadata: Dict[str, Any]):
    required_fields = ["section", "context"]

    for field in required_fields:
        if field not in metadata:
            raise ValueError(f"[PromptTemplates ERROR] Missing required field: {field}")


# -----------------------------
# CONTEXT PARSER
# -----------------------------

def parse_structured_context(context: str) -> Dict[str, str]:
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


# -----------------------------
# SECTION INSTRUCTIONS
# -----------------------------

def get_section_instructions(section: str) -> str:
    mapping = {
        "market_trends": "- Focus on macro patterns, shifts, and forward-looking signals",
        "financial_analysis": "- Focus on revenue, margins, cost structure, and growth dynamics",
        "operations": "- Focus on execution, efficiency, and operational changes",
        "strategy": "- Focus on positioning, differentiation, and strategic direction",
        "portfolio": "- Focus on asset composition, shifts, and strategic implications"
    }

    return mapping.get(section, "- Provide high-quality, insight-driven analysis")


# -----------------------------
# MAIN PROMPT BUILDER
# -----------------------------

def build_prompt(metadata: Dict[str, Any]) -> Dict[str, Any]:

    try:
        validate_inputs(metadata)

        # 🔥 NEW: dynamic prompt selection
        prompt_key = metadata.get("prompt_type", "market_analysis")
        template = load_prompt(prompt_key)

        style = metadata.get("style", "thought_leadership")
        style_desc = STYLES.get(style, STYLES["thought_leadership"])

        structured_context = parse_structured_context(metadata["context"])

        structured_block = ""
        for section_name, content in structured_context.items():
            structured_block += f"\n### {section_name}\n{content}\n"

        section_instruction = get_section_instructions(metadata["section"])

        # 🔥 SAFE FORMATTING (supports prompts WITHOUT variables)
        try:
            prompt = template.format(
                section=metadata["section"],
                timeframe=metadata.get("month", "N/A"),
                markets=", ".join(metadata.get("markets", [])),
                structured_block=structured_block,
                style_desc=style_desc,
                section_instruction=section_instruction,
                context=metadata.get("context", "")
            )
        except KeyError:
            # If template has no placeholders → use raw template
            prompt = template

        return {
            "section": metadata["section"],
            "prompt": prompt.strip(),
            "max_tokens": metadata.get("max_tokens", 600),
            "temperature": metadata.get("temperature", 0.2),
            "prompt_type": prompt_key,
            "success": True
        }

    except Exception as e:
        return {
            "section": metadata.get("section", "unknown"),
            "error": str(e),
            "success": False
        }