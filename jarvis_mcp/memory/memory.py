"""Memory management for Jarvis MCP Server."""

import json
from pathlib import Path
from typing import Dict, List
from ..config import MEMORY_FILE


class MemoryManager:
    """Manage persistent memory storage."""
    
    def __init__(self, memory_file: Path = None):
        self.memory_file = memory_file or MEMORY_FILE
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> Dict:
        """Load memory from file."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return self._normalize(json.load(f))
            except (json.JSONDecodeError, IOError) as e:
                print(f"[Memory] Failed to load: {e}")
                return {"facts": [], "conversation_count": 0}
        return {"facts": [], "conversation_count": 0}
    
    def save(self, memory: Dict):
        """Save memory to file."""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self._normalize(memory), f, indent=2, ensure_ascii=False)
    
    def add_fact(self, fact: str):
        """Add a fact to memory."""
        memory = self.load()
        facts = memory.setdefault("facts", [])
        if not isinstance(facts, list):
            memory["facts"] = []
            facts = memory["facts"]
        if fact not in facts:
            facts.append(fact)
            self.save(memory)
    
    def get_facts(self) -> List[str]:
        """Get all facts from memory."""
        memory = self.load()
        return memory.get("facts", [])
    
    def clear_facts(self):
        """Clear all facts from memory."""
        memory = self.load()
        memory["facts"] = []
        self.save(memory)
    
    def increment_conversation_count(self):
        """Increment conversation counter."""
        memory = self.load()
        memory["conversation_count"] = memory.get("conversation_count", 0) + 1
        self.save(memory)
    
    def get_conversation_count(self) -> int:
        """Get conversation count."""
        memory = self.load()
        return memory.get("conversation_count", 0)
    
    def _normalize(self, memory: Dict) -> Dict:
        """Normalize memory dictionary."""
        if not isinstance(memory, dict):
            return {"facts": [], "conversation_count": 0}
        
        normalized = dict(memory)
        facts = normalized.get("facts")
        if not isinstance(facts, list):
            facts = []
        
        conversation_count = normalized.get("conversation_count", 0)
        try:
            conversation_count = int(conversation_count)
        except (TypeError, ValueError):
            conversation_count = 0
        
        normalized["facts"] = [str(fact) for fact in facts if str(fact).strip()]
        normalized["conversation_count"] = max(0, conversation_count)
        return normalized
    
    def get_memory_text(self) -> str:
        """Get memory as formatted text for prompts."""
        facts = self.get_facts()
        if facts:
            return "\n".join(f"- {fact}" for fact in facts)
        return "Nothing stored yet."
