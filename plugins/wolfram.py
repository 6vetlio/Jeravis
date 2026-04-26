"""Wolfram Alpha plugin for Jarvis."""

import wolframalpha

NAME = "wolfram"
DESCRIPTION = "Query Wolfram Alpha for computational answers"
TRIGGERS = ["calculate", "solve", "compute", "wolfram", "math"]

def execute(query: str, memory: dict) -> str:
    """Execute Wolfram Alpha query."""
    try:
        # Load API key from config
        import os
        api_key_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "api_keys.json")
        
        if not os.path.exists(api_key_file):
            return "Wolfram Alpha requires an API key. Add it to api_keys.json as 'wolfram_alpha_key'."
        
        import json
        with open(api_key_file, 'r') as f:
            api_keys = json.load(f)
        
        wolfram_key = api_keys.get("wolfram_alpha_key")
        if not wolfram_key:
            return "Wolfram Alpha API key not found in api_keys.json"
        
        # Extract query term
        search_term = query.lower()
        for trigger in TRIGGERS:
            if trigger in search_term:
                search_term = search_term.replace(trigger, "").replace("the", "")
                search_term = search_term.strip()
                break
        
        if not search_term or len(search_term) < 2:
            return None
        
        # Query Wolfram Alpha
        client = wolframalpha.Client(wolfram_key)
        res = client.query(search_term)
        
        # Get the primary answer
        if res.results:
            answer = next(res.results).text
            return f"Wolfram Alpha: {answer}"
        else:
            return f"Wolfram Alpha couldn't find an answer for '{search_term}'."
    except Exception as e:
        return f"Wolfram Alpha query failed: {str(e)}"
