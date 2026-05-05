def iter_dict(sel_sect):
    return "".join(f"{k} -- {v}\n\n" for k, v in sel_sect.items())

def filter_sections(kb, section, date, country=None):
    
    content = ""

    if section == "market_trends":
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
    from document_processor import load_knowledge_base
    kb = load_knowledge_base()

    result = get_section_context(kb, ["market_trends", "opportunities"], "2026 March", ["UK"])
    print(result)