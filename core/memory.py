"""Memory management for Jarvis AI Assistant."""

import json
import os
from config import MEMORY_FILE, PERSONALITY_FILE, AUTONOMOUS_PROMPTS_FILE


def normalize_memory(memory):
    """Normalize memory dictionary to ensure valid structure."""
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


def load_memory():
    """Load memory from file or return default structure."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return normalize_memory(json.load(f))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"[Memory warning] Failed to load memory: {e}")
    return {"facts": [], "conversation_count": 0}


def save_memory(memory):
    """Save memory to file (merge with existing to preserve data)."""
    existing = load_memory()
    # Merge facts, avoiding duplicates
    existing_facts = set(existing.get("facts", []))
    new_facts = set(memory.get("facts", []))
    merged_facts = list(existing_facts.union(new_facts))
    
    merged_memory = {
        "facts": merged_facts,
        "conversation_count": max(existing.get("conversation_count", 0), memory.get("conversation_count", 0))
    }
    
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(merged_memory, f, indent=2, ensure_ascii=False)


def add_memory_fact(fact: str, memory: dict):
    """Add a fact to memory."""
    facts = memory.setdefault("facts", [])
    if not isinstance(facts, list):
        memory["facts"] = []
        facts = memory["facts"]
    if fact not in facts:
        facts.append(fact)
        save_memory(memory)


def load_personality():
    """Load personality traits from file."""
    if os.path.exists(PERSONALITY_FILE):
        try:
            with open(PERSONALITY_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except (OSError, UnicodeDecodeError) as e:
            print(f"[Personality warning] Failed to load personality: {e}")
    return ""


def save_personality_trait(trait: str):
    """Save a personality trait (append with timestamp to preserve history)."""
    current = load_personality()
    traits = current.split("\n") if current else []
    trait = trait.strip()
    if trait and trait not in traits:
        timestamp = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        traits.append(f"[{timestamp}] {trait}")
        with open(PERSONALITY_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(traits))
        print(f"[Personality] Added: {trait}")


def load_key_moments(limit=5):
    """Load recent key moments from conversation history."""
    from config import CONVERSATION_HISTORY_FILE
    key_moments = []
    if os.path.exists(CONVERSATION_HISTORY_FILE):
        try:
            with open(CONVERSATION_HISTORY_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line in lines:
                if "[KEY MOMENT]" in line:
                    key_moments.append(line.strip())
        except (OSError, UnicodeDecodeError) as e:
            print(f"[Key moments warning] Failed to load: {e}")
    return key_moments[-limit:] if key_moments else []


def load_autonomous_prompts():
    """Load autonomous thinking prompts."""
    if os.path.exists(AUTONOMOUS_PROMPTS_FILE):
        try:
            with open(AUTONOMOUS_PROMPTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"[Autonomous prompts warning] Failed to load: {e}")
    return {
        "proactive": "Think about what you could do to help the user.",
        "reactive": "Analyze the current context and suggest next steps.",
        "creative": "Come up with creative ideas or suggestions."
    }


def load_voice_commands():
    """Load custom voice commands."""
    from config import VOICE_COMMANDS_FILE
    if os.path.exists(VOICE_COMMANDS_FILE):
        try:
            with open(VOICE_COMMANDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"[Voice commands warning] Failed to load: {e}")
    return {}


def save_conversation_to_history(query, response, is_key_moment, reason, thinking_text=""):
    """Save conversation entry to history file."""
    from config import CONVERSATION_HISTORY_FILE
    timestamp = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CONVERSATION_HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] User: {query}\n")
        if thinking_text:
            f.write(f"[{timestamp}] Thinking: {thinking_text}\n")
        f.write(f"[{timestamp}] Jarvis: {response}\n")
        if is_key_moment:
            f.write(f"[{timestamp}] [KEY MOMENT] {reason}\n")
        f.write("-" * 50 + "\n")
