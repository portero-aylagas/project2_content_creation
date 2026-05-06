"""Knowledge-base context selection and concatenation.

This module builds report-ready context strings from parsed KB data returned by
`document_processor.load_knowledge_base`.
"""

SUPPORTED_SECTIONS = {
    "market_trends",
    "platform_updates",
    "competition",
    "artist_economy",
    "opportunities",
}


def _get_required(mapping, key, context):
    """Return `mapping[key]` with a clearer error message if missing."""
    if not isinstance(mapping, dict):
        raise ValueError(f"{context} must be a dictionary.")

    if key not in mapping:
        available = ", ".join(sorted(str(k) for k in mapping.keys()))
        raise ValueError(
            f"Missing key '{key}' in {context}. Available keys: {available}"
        )

    return mapping[key]


def iter_dict(sel_sect):
    """Render a dictionary section as a simple key-value text block."""
    return "".join(f"{k} -- {v}\n\n" for k, v in sel_sect.items())


def filter_sections(kb, section, date, country=None):
    """Build context text for one internal section name.

    Args:
        kb (dict): Parsed knowledge-base dictionary.
        section (str): Internal section key expected by this module:
            `market_trends`, `platform_updates`, `competition`,
            `artist_economy`, or `opportunities`.
        date (str): Period key in the form `YYYY Month` (for example,
            `2026 March`).
        country (str | None): Required only for `market_trends`.

    Returns:
        str: Concatenated context for the requested section.
    """
    if section not in SUPPORTED_SECTIONS:
        supported = ", ".join(sorted(SUPPORTED_SECTIONS))
        raise ValueError(
            f"Unsupported section '{section}'. Supported sections: {supported}"
        )

    secondary = _get_required(kb, "secondary", "knowledge base root")
    primary = _get_required(kb, "primary", "knowledge base root")
    content = ""

    if section == "market_trends":
        # Market trends are stored by country under one date bucket.
        market_trends = _get_required(
            secondary, "market_trends_DE_UK_FR", "knowledge_base.secondary"
        )
        period_bucket = _get_required(
            market_trends, date, "knowledge_base.secondary.market_trends_DE_UK_FR"
        )
        if not country:
            raise ValueError(
                "Country is required for section 'market_trends'."
            )
        selected_section = _get_required(
            period_bucket,
            country,
            (
                "knowledge_base.secondary.market_trends_DE_UK_FR"
                f"['{date}']"
            ),
        )
        content += f"# Market trends for {country} in {date}:\n\n"
        content += selected_section

    elif section == "platform_updates":
        content += f"# Platform policy updates for {date}:\n\n"
        platform_updates = _get_required(
            secondary, "platform_policy_updates", "knowledge_base.secondary"
        )
        selected_section = _get_required(
            platform_updates,
            date,
            "knowledge_base.secondary.platform_policy_updates",
        )
        content += iter_dict(selected_section)

        content += f"# Streaming platforms landscape for {date}:\n\n"
        platform_landscape = _get_required(
            secondary, "streaming_platforms_landscape", "knowledge_base.secondary"
        )
        selected_section = _get_required(
            platform_landscape,
            date,
            "knowledge_base.secondary.streaming_platforms_landscape",
        )
        content += iter_dict(selected_section)

    elif section == "competition":
        content += f"# Believe's competitive positioning:\n\n"
        selected_section = _get_required(
            primary, "believe_competitive_positioning", "knowledge_base.primary"
        )
        content += iter_dict(selected_section)

        competitor_intel = _get_required(
            secondary, "competitor_intelligence", "knowledge_base.secondary"
        )
        selected_section = _get_required(
            competitor_intel,
            date,
            "knowledge_base.secondary.competitor_intelligence",
        )
        content += f"# Competition analysis for {date}:\n\n"
        content += iter_dict(selected_section)

    elif section == "artist_economy":
        artist_economy = _get_required(
            secondary, "independent_music_industry", "knowledge_base.secondary"
        )
        selected_section = _get_required(
            artist_economy,
            date,
            "knowledge_base.secondary.independent_music_industry",
        )
        content += f"# Artist economy for {date}:\n\n"
        content += iter_dict(selected_section)

    elif section == "opportunities":
        selected_section = _get_required(
            primary, "believe_company_profile", "knowledge_base.primary"
        )
        content += f"# Believe's company profile:\n\n"
        content += iter_dict(selected_section)

        content += f"# Market opportunities:\n\n"
        for f in secondary:
            secondary_source = _get_required(
                secondary, f, "knowledge_base.secondary"
            )
            selected_section = _get_required(
                secondary_source,
                date,
                f"knowledge_base.secondary.{f}",
            )
            content += f"# {f}:\n\n"
            content += iter_dict(selected_section)

    return content


def get_section_context(kb, sections, date, markets):
    """Build one combined context string from all selected sections.

    Args:
        kb (dict): Parsed KB dictionary from `document_processor`.
        sections (list[str]): Internal section names to include.
        date (str): Period key used in secondary KB files.
        markets (list[str]): Market labels used for `market_trends` context.

    Returns:
        str: Combined context text used by prompt generation.
    """
    if not isinstance(sections, list):
        raise ValueError("sections must be a list of section names.")

    if not isinstance(markets, list):
        raise ValueError("markets must be a list of market names.")

    content = ""
    for s in sections:
        content += "#######################################\n"
        if s == "market_trends":
            for c in markets:
                content += filter_sections(kb, s, date, c)
                content += "\n\n"
        else:
            content += filter_sections(kb, s, date)
            content += "\n\n"
    return content

if __name__ == "__main__":
    # Quick local check for context assembly.
    from document_processor import load_knowledge_base
    kb = load_knowledge_base()

    result = get_section_context(kb, ["market_trends", "opportunities"], "2026 March", ["UK"])
    print(result)
