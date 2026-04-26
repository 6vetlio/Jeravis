"""Core modules for Jarvis AI Assistant."""

from .memory import (
    load_memory, save_memory, add_memory_fact,
    load_personality, save_personality_trait,
    load_key_moments, load_autonomous_prompts,
    load_voice_commands, save_conversation_to_history
)

from .ollama import (
    ask_ollama, ask_external_api,
    select_model_for_query, extract_thinking_content,
    check_ollama_running, start_ollama, unload_all_models,
    load_api_keys, is_coding_query, is_weather_query
)

from .skills import (
    handle_direct_query, get_weather_response,
    get_location_response, is_weather_query,
    is_location_query, load_plugins, check_plugins
)

from .pc_control import (
    execute_pc_action, parse_pc_actions,
    process_response, take_screenshot,
    execute_powershell_command
)

__all__ = [
    # Memory
    'load_memory', 'save_memory', 'add_memory_fact',
    'load_personality', 'save_personality_trait',
    'load_key_moments', 'load_autonomous_prompts',
    'load_voice_commands', 'save_conversation_to_history',
    # Ollama
    'ask_ollama', 'ask_external_api',
    'select_model_for_query', 'extract_thinking_content',
    'check_ollama_running', 'start_ollama', 'unload_all_models',
    'load_api_keys', 'is_coding_query', 'is_weather_query',
    # Skills
    'handle_direct_query', 'get_weather_response',
    'get_location_response', 'is_weather_query',
    'is_location_query', 'load_plugins', 'check_plugins',
    # PC Control
    'execute_pc_action', 'parse_pc_actions',
    'process_response', 'take_screenshot',
    'execute_powershell_command',
]
