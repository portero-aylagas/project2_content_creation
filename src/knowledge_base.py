"""Knowledge-base context selection and concatenation.

This module builds report-ready context strings from parsed KB data returned by
`document_processor.load_knowledge_base`.
"""

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
    
    content = ""

    if section == "market_trends":
        # Market trends are stored by country under one date bucket.
        selected_section = kb["secondary"]["market_trends_DE_UK_FR"][date][country]
        content += f"# Market trends for {country} in {date}:\n\n"
        content += selected_section
        
    elif section == "platform_updates":
        content += f"# Platform policy updates for {date}:\n\n"
        selected_section = kb["secondary"]["platform_policy_updates"][date]
        content += iter_dict(selected_section)
        
        content += f"# Streaming platforms landscape for {date}:\n\n"
        selected_section = kb["secondary"]["streaming_platforms_landscape"][date]      
        content += iter_dict(selected_section)

    elif section == "competition":
        content += f"# Believe's competitive positioning:\n\n"
        selected_section = kb["primary"]["believe_competitive_positioning"]
        content += iter_dict(selected_section)
        
        selected_section = kb["secondary"]["competitor_intelligence"][date]      
        content += f"# Competition analysis for {date}:\n\n"
        content += iter_dict(selected_section)

    elif section == "artist_economy":
        selected_section = kb["secondary"]["independent_music_industry"][date]
        content += f"# Artist economy for {date}:\n\n"
        content += iter_dict(selected_section)
        
    elif section == "opportunities":
        selected_section = kb["primary"]["believe_company_profile"]
        content += f"# Believe's company profile:\n\n"
        content += iter_dict(selected_section)

        content += f"# Market opportunities:\n\n"
        for f in kb["secondary"]:
            selected_section = kb["secondary"][f][date]
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
