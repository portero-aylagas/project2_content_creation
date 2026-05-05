"""Knowledge base ingestion utilities.

This module reads markdown files from the local `knowledge_base/` directory and
parses heading hierarchies into nested dictionaries.
"""

from pathlib import Path

def load_knowledge_base():
    """Load all knowledge-base markdown files into a nested dictionary.

    Returns:
        dict: Structure grouped by folder name (`primary`, `secondary`) and file
        stem, with each value containing parsed markdown content from
        `read_file_base`.
    """
    base_path = Path("knowledge_base")

    knowledge = {}

    for folder in base_path.iterdir():
        knowledge[folder.name] = {}
        for file in folder.iterdir():
            knowledge[folder.name][file.name[:-3]] = read_file_base(file)

    return knowledge

def read_file_base(file_path):
    """Parse a markdown file into nested section dictionaries by heading level.

    Args:
        file_path (Path): Path to a markdown file.

    Returns:
        dict | str: Nested structure keyed by headings. Leaf values are strings
        when no deeper headings exist.
    """
    def parse(lines, level):
        """Recursively parse lines for the current heading level."""
        # Check if there are any headings at this level
        has_heading = any(
            line.strip().startswith("#" * level) and not line.strip().startswith("#" * (level + 1))
            for line in lines
        )

        # If no headings → return raw content
        if not has_heading:
            return "\n".join(line.strip() for line in lines).strip()

        result = {}
        i = 0

        while i < len(lines):
            line = lines[i].rstrip()

            if line.startswith("#" * level) and not line.startswith("#" * (level + 1)):
                title = line[level:].strip()
                i += 1

                # Collect this section's block
                block = []
                while i < len(lines):
                    next_line = lines[i]
                    if next_line.strip().startswith("#" * level) and not next_line.strip().startswith("#" * (level + 1)):
                        break
                    block.append(next_line)
                    i += 1

                result[title] = parse(block, level + 1)

            else:
                i += 1

        return result

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    return parse(lines, 1)

if __name__ == "__main__":
    # Quick local check: parse and load the KB structure.
    kb = load_knowledge_base()
