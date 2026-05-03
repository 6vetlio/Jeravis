"""Personality management for Jarvis MCP Server."""

from pathlib import Path
from typing import List
from ..config import PERSONALITY_FILE


class PersonalityManager:
    """Manage personality traits."""
    
    def __init__(self, personality_file: Path = None):
        self.personality_file = personality_file or PERSONALITY_FILE
        self.personality_file.parent.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> str:
        """Load personality traits from file."""
        if self.personality_file.exists():
            try:
                with open(self.personality_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except IOError as e:
                print(f"[Personality] Failed to load: {e}")
        return ""
    
    def add_trait(self, trait: str):
        """Add a personality trait with timestamp."""
        current = self.load()
        traits = current.split("\n") if current else []
        trait = trait.strip()
        if trait and trait not in traits:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            traits.append(f"[{timestamp}] {trait}")
            with open(self.personality_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(traits))
    
    def get_traits(self) -> List[str]:
        """Get all personality traits."""
        content = self.load()
        if content:
            return [line.strip() for line in content.split("\n") if line.strip()]
        return []
    
    def clear_traits(self):
        """Clear all personality traits."""
        if self.personality_file.exists():
            self.personality_file.unlink()
    
    def get_personality_text(self) -> str:
        """Get personality as formatted text for prompts."""
        traits = self.get_traits()
        if traits:
            return "\n".join(f"- {trait}" for trait in traits)
        return "No personality traits learned yet."
