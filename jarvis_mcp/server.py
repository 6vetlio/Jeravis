"""Jarvis MCP Server - Main entry point."""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: mcp package not installed. Run: pip install mcp")
    sys.exit(1)

from jarvis_mcp.config import load_config, CONFIG_DIR
from jarvis_mcp.backends import OllamaBackend, LMStudioBackend, VastAIBackend
from jarvis_mcp.memory import MemoryManager, PersonalityManager
from jarvis_mcp.pc_control import PCControlExecutor


class JarvisMCPServer:
    """Jarvis MCP Server implementation."""
    
    def __init__(self):
        self.config = load_config()
        self.backend = self._init_backend()
        self.memory = MemoryManager()
        self.personality = PersonalityManager()
        self.pc_control = PCControlExecutor(
            safety_mode=self.config.get("safety_mode", True),
            sandbox_mode=self.config.get("sandbox_mode", False)
        )
        self.server = Server("jarvis-mcp")
        self._register_tools()
    
    def _init_backend(self):
        """Initialize the appropriate model backend."""
        backend_type = self.config.get("backend", "ollama")
        
        if backend_type == "ollama":
            host = self.config.get("ollama_host", "http://127.0.0.1:11434")
            return OllamaBackend(host)
        elif backend_type == "lm_studio":
            host = self.config.get("lm_studio_host", "http://127.0.0.1:1234")
            return LMStudioBackend(host)
        elif backend_type == "vast_ai":
            host = self.config.get("vast_ai_host", "")
            if not host:
                print("[Warning] Vast.ai host not configured, falling back to Ollama")
                return OllamaBackend(self.config.get("ollama_host", "http://127.0.0.1:11434"))
            return VastAIBackend(host)
        else:
            print(f"[Warning] Unknown backend {backend_type}, using Ollama")
            return OllamaBackend(self.config.get("ollama_host", "http://127.0.0.1:11434"))
    
    def _register_tools(self):
        """Register MCP tools."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="chat",
                    description="Send a message to the AI model with streaming support",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "description": "User message"},
                            "model": {"type": "string", "description": "Model to use (optional)"},
                            "stream": {"type": "boolean", "description": "Stream response (default: true)"}
                        },
                        "required": ["message"]
                    }
                ),
                Tool(
                    name="memory_add",
                    description="Add a fact to memory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "fact": {"type": "string", "description": "Fact to remember"}
                        },
                        "required": ["fact"]
                    }
                ),
                Tool(
                    name="memory_get",
                    description="Get all facts from memory",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="memory_clear",
                    description="Clear all facts from memory",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="personality_get",
                    description="Get personality traits",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="personality_add",
                    description="Add a personality trait",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "trait": {"type": "string", "description": "Personality trait to add"}
                        },
                        "required": ["trait"]
                    }
                ),
                Tool(
                    name="pc_execute",
                    description="Execute a PowerShell command on the local machine",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "PowerShell command to execute"}
                        },
                        "required": ["command"]
                    }
                ),
                Tool(
                    name="pc_screenshot",
                    description="Take a screenshot",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="model_list",
                    description="List available models",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="config_get",
                    description="Get current configuration",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="config_set",
                    description="Set a configuration value",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "key": {"type": "string", "description": "Configuration key"},
                            "value": {"type": "string", "description": "Configuration value"}
                        },
                        "required": ["key", "value"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            try:
                if name == "chat":
                    return await self._handle_chat(arguments)
                elif name == "memory_add":
                    return await self._handle_memory_add(arguments)
                elif name == "memory_get":
                    return await self._handle_memory_get(arguments)
                elif name == "memory_clear":
                    return await self._handle_memory_clear(arguments)
                elif name == "personality_get":
                    return await self._handle_personality_get(arguments)
                elif name == "personality_add":
                    return await self._handle_personality_add(arguments)
                elif name == "pc_execute":
                    return await self._handle_pc_execute(arguments)
                elif name == "pc_screenshot":
                    return await self._handle_pc_screenshot(arguments)
                elif name == "model_list":
                    return await self._handle_model_list(arguments)
                elif name == "config_get":
                    return await self._handle_config_get(arguments)
                elif name == "config_set":
                    return await self._handle_config_set(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {e}")]
    
    async def _handle_chat(self, arguments: Dict[str, Any]) -> List[TextContent]:
        message = arguments.get("message", "")
        model = arguments.get("model")
        stream = arguments.get("stream", True)
        
        if not message:
            return [TextContent(type="text", text="Error: message is required")]
        
        if not model:
            model = self._select_model(message)
        
        system = self._build_system_prompt(model)
        messages = [{"role": "system", "content": system}, {"role": "user", "content": message}]
        
        chunks = []
        def chunk_callback(content: str):
            chunks.append(content)
        
        try:
            response = self.backend.chat(
                model=model, messages=messages, stream=stream,
                options={"temperature": 0.7, "num_predict": 1024},
                keep_alive=self.config.get("keep_alive", "5m"),
                chunk_callback=chunk_callback if stream else None
            )
            
            thinking, clean_response = self._extract_thinking(response)
            output = ""
            if thinking:
                output += f"<thinking>\n{thinking}\n</thinking>\n\n"
            output += clean_response
            
            self.memory.increment_conversation_count()
            return [TextContent(type="text", text=output)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {e}")]
    
    def _select_model(self, query: str) -> str:
        models = self.config.get("models", {})
        coding_keywords = ["code", "script", "function", "python", "debug", "implement", "error", "bug"]
        lowered = query.lower()
        
        if any(keyword in lowered for keyword in coding_keywords):
            return models.get("coding", models.get("default", "deepseek-r1:32b"))
        if len(query.strip().split()) == 1 and len(query) < 15:
            return models.get("tiny", models.get("default", "deepseek-r1:8b"))
        return models.get("default", "deepseek-r1:32b")
    
    def _build_system_prompt(self, model: str) -> str:
        system = """You are Jarvis. You are direct, confident, and occasionally dry-humored. You are NOT a customer service bot.

HARD RULES — never break these:
- NEVER end a response with "How can I help you?" or "Let me know if you need anything" or any variation. Ever.
- NEVER apologize unless you actually did something wrong
- NEVER ask the user what they need — they will tell you
- NEVER say "Great question!" or "Certainly!" or "Of course!"
- If you have nothing to add, say nothing. Don't pad responses.

REASONING REQUIREMENT:
Before your final answer, you MUST output two reasoning sections:
1. <thinking>Analysis: What did the user specifically mean?</thinking>
2. <thinking>Reasoning: Why is this the correct answer?</thinking>
Then provide your final response.

HOW TO RESPOND:
- Answer what was asked, then stop
- Have opinions, express them
- Push back when something is wrong or stupid
- Match the user's energy — if they're casual, be casual
- Humor is fine, sycophancy is not

"""
        system += f"Current date and time: {datetime.now().strftime('%A, %B %d %Y %H:%M')}\n\n"
        
        if self.config.get("personality_enabled", True):
            personality = self.personality.get_personality_text()
            system += f"Your learned personality traits:\n{personality}\n\n"
        
        if self.config.get("memory_enabled", True):
            memory = self.memory.get_memory_text()
            system += f"What you know about the user:\n{memory}\n"
        
        system += f"\nYou are currently running on: {model}"
        return system
    
    def _extract_thinking(self, response: str) -> tuple:
        thinking_match = re.search(r'<thinking>(.*?)</thinking>', response, re.DOTALL | re.IGNORECASE)
        if thinking_match:
            thinking_content = thinking_match.group(1).strip()
            clean_response = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL | re.IGNORECASE).strip()
            return thinking_content, clean_response
        return None, response
    
    async def _handle_memory_add(self, arguments: Dict[str, Any]) -> List[TextContent]:
        fact = arguments.get("fact", "")
        if not fact:
            return [TextContent(type="text", text="Error: fact is required")]
        self.memory.add_fact(fact)
        return [TextContent(type="text", text=f"Added to memory: {fact}")]
    
    async def _handle_memory_get(self, arguments: Dict[str, Any]) -> List[TextContent]:
        facts = self.memory.get_facts()
        if facts:
            return [TextContent(type="text", text="Memory:\n" + "\n".join(f"- {f}" for f in facts))]
        return [TextContent(type="text", text="Memory is empty.")]
    
    async def _handle_memory_clear(self, arguments: Dict[str, Any]) -> List[TextContent]:
        self.memory.clear_facts()
        return [TextContent(type="text", text="Memory cleared.")]
    
    async def _handle_personality_get(self, arguments: Dict[str, Any]) -> List[TextContent]:
        traits = self.personality.get_traits()
        if traits:
            return [TextContent(type="text", text="Personality traits:\n" + "\n".join(f"- {t}" for t in traits))]
        return [TextContent(type="text", text="No personality traits learned yet.")]
    
    async def _handle_personality_add(self, arguments: Dict[str, Any]) -> List[TextContent]:
        trait = arguments.get("trait", "")
        if not trait:
            return [TextContent(type="text", text="Error: trait is required")]
        self.personality.add_trait(trait)
        return [TextContent(type="text", text=f"Added personality trait: {trait}")]
    
    async def _handle_pc_execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        if not self.config.get("pc_control_enabled", True):
            return [TextContent(type="text", text="PC control is disabled.")]
        
        command = arguments.get("command", "")
        if not command:
            return [TextContent(type="text", text="Error: command is required")]
        
        result = self.pc_control.execute(command)
        return [TextContent(type="text", text=f"Result:\n{result}")]
    
    async def _handle_pc_screenshot(self, arguments: Dict[str, Any]) -> List[TextContent]:
        if not self.config.get("pc_control_enabled", True):
            return [TextContent(type="text", text="PC control is disabled.")]
        
        screenshot_path = self.pc_control.take_screenshot()
        if screenshot_path:
            return [TextContent(type="text", text=f"Screenshot saved: {screenshot_path}")]
        return [TextContent(type="text", text="Failed to take screenshot.")]
    
    async def _handle_model_list(self, arguments: Dict[str, Any]) -> List[TextContent]:
        models = self.backend.list_models()
        if models:
            return [TextContent(type="text", text="Available models:\n" + "\n".join(f"- {m}" for m in models))]
        return [TextContent(type="text", text="No models available.")]
    
    async def _handle_config_get(self, arguments: Dict[str, Any]) -> List[TextContent]:
        return [TextContent(type="text", text=json.dumps(self.config, indent=2))]
    
    async def _handle_config_set(self, arguments: Dict[str, Any]) -> List[TextContent]:
        key = arguments.get("key", "")
        value = arguments.get("value", "")
        if not key:
            return [TextContent(type="text", text="Error: key is required")]
        
        from jarvis_mcp.config import set_config_value
        set_config_value(key, value)
        self.config = load_config()
        return [TextContent(type="text", text=f"Set {key} = {value}")]


async def main():
    """Main entry point."""
    server = JarvisMCPServer()
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(read_stream, write_stream, server.server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
