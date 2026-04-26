"""Wikipedia search plugin for Jarvis."""

import wikipedia

NAME = "wikipedia"
DESCRIPTION = "Search Wikipedia for summaries"
TRIGGERS = ["wiki", "wikipedia", "what is", "who is", "define"]

def execute(query: str, memory: dict) -> str:
    """Execute Wikipedia search."""
    try:
        # Extract search term
        search_term = query.lower()
        for trigger in TRIGGERS:
            if trigger in search_term:
                search_term = search_term.replace(trigger, "").replace("the", "").replace("a", "").replace("an", "")
                search_term = search_term.strip()
                break
        
        if not search_term or len(search_term) < 2:
            return None
        
        # Search Wikipedia
        wikipedia.set_lang("en")
        results = wikipedia.search(search_term, results=3)
        
        if results:
            response = f"Found {len(results)} Wikipedia results for '{search_term}':\n\n"
            for title in results[:2]:  # Get top 2 results
                try:
                    page = wikipedia.page(title, auto_suggest=False)
                    summary = wikipedia.summary(title, sentences=3)
                    response += f"{title}:\n{summary}\n\n"
                except wikipedia.exceptions.PageError:
                    continue
                except wikipedia.exceptions.DisambiguationError as e:
                    response += f"{title}: Disambiguation - {str(e.options[:3])}\n\n"
            return response
        else:
            return f"No Wikipedia results found for '{search_term}'."
    except Exception as e:
        return f"Wikipedia search failed: {str(e)}"
