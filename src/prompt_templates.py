from typing import Dict, Any

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
# MAIN PROMPT BUILDER
# -----------------------------

def build_prompt(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input:
    {
        "section": "market_trends",
        "context": "...",
        "month": "May",
        "year": "2025",
        "markets": ["DE","UK","FR"],
        "style": "contrarian",
        "temperature": 0.5
    }
    """

    try:
        validate_inputs(metadata)

        style = metadata.get("style", "thought_leadership")
        style_desc = STYLES.get(style, STYLES["thought_leadership"])

        prompt = f"""
You are a senior market intelligence analyst.

SECTION: {metadata['section']}
TIMEFRAME: {metadata.get('month', 'N/A')}
MARKETS: {', '.join(metadata.get('markets', []))}

----------------------------------------
CONTEXT
----------------------------------------
{metadata['context']}

----------------------------------------
INSTRUCTIONS
----------------------------------------
- Write in a {style_desc} tone
- Be specific and insight-driven
- Avoid generic statements
- Use real implications, not summaries

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
            "temperature": metadata.get("temperature", 0.2)  # ✅ NEW
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
- Remove generic phring
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
            "temperature": 0.2  # ✅ keep refinement deterministic
        }

    except Exception as e:
        return {
            "section": section,
            "error": str(e),
            "success": False
        }