from typing import Dict, Any
import re

# -----------------------------
# GLOBAL STYLES CONFIG
# -----------------------------

STYLES = {
    "thought_leadership": "insightful, expert-level, opinionated",
    "storytelling": "emotional, narrative-driven, engaging",
    "educational": "clear, structured, value-driven",
    "contrarian": "challenging assumptions, bold perspective",
    "minimalist": "concise, sharp, high-signal"
}

# -----------------------------
# VALIDATION HELPER
# -----------------------------

def validate_inputs(metadata: Dict[str, Any]):
    required_fields = ["section", "context"]

    for field in required_fields:
        if field not in metadata:
            raise ValueError(f"[PromptTemplates ERROR] Missing required field: {field}")

# -----------------------------
# STRUCTURED CONTEXT PARSER
# -----------------------------

def parse_structured_context(context: str) -> Dict[str, str]:
    """
    Parses markdown sections like:
    ### Overview
    ### Financials
    """

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
# SECTION-SPECIFIC INSTRUCTIONS
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

        style = metadata.get("style", "thought_leadership")
        style_desc = STYLES.get(style, STYLES["thought_leadership"])

        # Parse structured markdown context
        structured_context = parse_structured_context(metadata["context"])

        # Build structured input block
        structured_block = ""
        for section_name, content in structured_context.items():
            structured_block += f"\n### {section_name}\n{content}\n"

        # Section-specific instruction
        section_instruction = get_section_instructions(metadata["section"])

        prompt = f"""
You are a senior market intelligence analyst.

SECTION TO WRITE: {metadata['section']}
TIMEFRAME: {metadata.get('month', 'N/A')}
MARKETS: {', '.join(metadata.get('markets', []))}

----------------------------------------
STRUCTURED INPUT DATA
----------------------------------------
{structured_block}

----------------------------------------
INSTRUCTIONS
----------------------------------------
- Write in a {style_desc} tone
{section_instruction}
- Focus ONLY on the requested section: {metadata['section']}
- Extract insights from the most relevant sub-sections
- Do NOT summarize everything — prioritize relevance
- Be specific and insight-driven
- Avoid generic statements
- Highlight implications and trends

Length: 200–250 words

----------------------------------------
OUTPUT
----------------------------------------
Structured paragraph with clear insights
"""

        return {
            "section": metadata["section"],
            "prompt": prompt.strip(),
            "max_tokens": metadata.get("max_tokens", 600),
            "temperature": metadata.get("temperature", 0.2)
        }

    except Exception as e:
        return {
            "section": metadata.get("section", "unknown"),
            "error": str(e),
            "success": False
        }

# -----------------------------
# REFINEMENT PROMPT
# -----------------------------

def build_refinement_prompt(section: str, draft: str) -> Dict[str, Any]:

    try:
        prompt = f"""
You are improving a report section.

SECTION: {section}

TASK:
- Remove generic phrasing
- Increase specificity
- Strengthen insight quality

CONTENT:
{draft}

OUTPUT:
Improved version only
"""

        return {
            "section": section,
            "prompt": prompt.strip(),
            "max_tokens": 400,
            "temperature": 0.2  # deterministic refinement
        }

    except Exception as e:
        return {
            "section": section,
            "error": str(e),
            "success": False
        }