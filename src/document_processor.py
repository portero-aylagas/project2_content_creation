from pathlib import Path

def load_knowledge_base():
    """Load metadata for knowledge base folders into a nested dictionary.

    Each top-level key is a folder name in knowledge_base (for example, "primary" or "secondary").
    Each folder value is a dictionary mapping file names to empty string values.
    """
    base_path = Path("knowledge_base")

    knowledge = {}

    for folder in base_path.iterdir():
        knowledge[folder.name] = {}
        for file in folder.iterdir():
            knowledge[folder.name][file.name[:-3]] = read_file_base(file)

    return knowledge

def read_file_base(file):
    """Parse a markdown file and return a dictionary of sections.
    
    Args:
        file: Path to a markdown file
        
    Returns:
        Dictionary where keys are section names (heading text) and values are 
        the text content of that section. Content before the first heading is 
        stored under the "Header" key.
    """
    sections = {}
    current_section = "Header" # Default section for content before the first heading
    current_content = []
    
    with open(file, 'r', encoding='utf-8') as f:
        for line in f:
            # Check if line is a markdown heading
            if line.startswith('#'):
                # Save previous section
                sections[current_section] = '\n'.join(current_content).strip()
                
                # Extract section name (remove leading #'s and whitespace)
                current_section = line.lstrip('#').strip()
                current_content = []
            else:
                # Add line to current section content
                current_content.append(line.rstrip())
    
    # Save the last section
    sections[current_section] = '\n'.join(current_content).strip()
    
    return sections

if __name__ == "__main__":
    file = Path("test_file.md")
    dict_file = read_file_base(file)
    print(dict_file)

    # knowledge_base = load_knowledge_base()
    # print(knowledge_base)