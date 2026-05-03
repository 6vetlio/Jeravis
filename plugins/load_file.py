NAME = "load_file"
DESCRIPTION = "Load a file into Jarvis knowledge base"
TRIGGERS = ["learn from", "remember file", "load file", "add to knowledge"]

def execute(query: str, memory: dict) -> str:
    from core.knowledge import load_file
    # extract filepath from query
    import re
    path_match = re.search(r'[A-Za-z]:\\[\w\\.-]+|/[\w/.-]+', query)
    if path_match:
        filepath = path_match.group()
        load_file(filepath)
        return f"Loaded {filepath} into knowledge base."
    return "Provide a file path to load."
