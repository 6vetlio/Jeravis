"""DuckDuckGo web search plugin for Jarvis."""

from duckduckgo_search import DDGS

NAME = "web_search"
DESCRIPTION = "Search the web using DuckDuckGo instant answers"
TRIGGERS = ["search", "look up", "find", "google"]

def execute(query: str, memory: dict) -> str:
    """Execute web search query."""
    try:
        # Extract search term from query
        search_term = query.lower()
        for trigger in TRIGGERS:
            if trigger in search_term:
                # Remove trigger and common words to get the actual search term
                search_term = search_term.replace(trigger, "").replace("for", "").replace("about", "")
                search_term = search_term.strip()
                break
        
        if not search_term or len(search_term) < 2:
            return None
        
        # Search using DuckDuckGo
        ddgs = DDGS()
        results = list(ddgs.text(search_term, max_results=3))
        
        if results:
            response = f"Found {len(results)} results for '{search_term}':\n\n"
            for i, result in enumerate(results, 1):
                response += f"{i}. {result.get('title', 'No title')}\n"
                response += f"   {result.get('body', 'No description')[:200]}...\n"
                response += f"   {result.get('href', 'No URL')}\n\n"
            return response
        else:
            return f"No results found for '{search_term}'."
    except Exception as e:
        return f"Search failed: {str(e)}"
