# Jarvis MCP Server

Jarvis core functionality exposed as an MCP (Model Context Protocol) server for Windsurf, Cursor, and other MCP-compatible IDEs. Runs fully locally.

## Current State (April 2026)

- MCP server running at `c:\Users\svet\jarvis_mcp\server.py`
- Registered in Windsurf at `c:\Users\svet\.codeium\windsurf\mcp_config.json`
- Active model: `mistral-small:22b` (general), `deepseek-coder-v2:16b` (coding)
- ChromaDB knowledge base integrated into original Jarvis GUI
- Hardware: 2x RTX 4060 Ti (32GB VRAM total)

## Features

- **Multi-backend support**: Ollama, LM Studio, Vast.ai remote
- **Memory system**: Persistent fact storage across sessions
- **Personality learning**: Adapts behavior over time
- **Thinking visibility**: See model reasoning in real-time
- **PC control**: Execute PowerShell commands with safety features
- **Model routing**: Automatic model selection based on query type
- **ChromaDB knowledge base**: Semantic search over memory + conversation history
- **Safety features**: Sandbox mode, file protection, action confirmation

## Installation

### 1. Install Dependencies

```bash
pip install mcp ollama requests psutil Pillow
pip install chromadb sentence-transformers
```

### 2. Configure Backend

Edit `~/.jarvis_mcp/config.json` (created automatically on first run):

```json
{
  "backend": "ollama",
  "ollama_host": "http://127.0.0.1:11434",
  "lm_studio_host": "http://127.0.0.1:1234",
  "vast_ai_host": "",
  "models": {
    "default": "mistral-small:22b",
    "coding": "deepseek-coder-v2:16b",
    "tiny": "deepseek-r1:8b"
  },
  "memory_enabled": true,
  "personality_enabled": true,
  "pc_control_enabled": true,
  "safety_mode": true,
  "sandbox_mode": false,
  "thinking_visibility": true,
  "keep_alive": "5m",
  "retry_count": 3
}
```

### 3. Pull Models

```bash
ollama pull mistral-small:22b
ollama pull deepseek-coder-v2:16b
```

### 4. Configure Windsurf

Add to `c:\Users\svet\.codeium\windsurf\mcp_config.json`:

```json
{
  "mcpServers": {
    "jarvis": {
      "command": "python",
      "args": ["c:\\Users\\svet\\jarvis_mcp\\server.py"]
    }
  }
}
```

Note: Server is copied to `c:\Users\svet\jarvis_mcp\` to avoid Cyrillic path issues.

## Available MCP Tools (11 total)

- `chat` - Send message to model with streaming and thinking visibility
- `memory_add` - Add fact to persistent memory
- `memory_get` - Retrieve all memory facts
- `memory_clear` - Clear all memory
- `personality_get` - Get personality traits
- `personality_add` - Add personality trait
- `pc_execute` - Execute PowerShell command with safety checks
- `pc_screenshot` - Take screenshot
- `model_list` - List available Ollama models
- `config_get` - Get current configuration
- `config_set` - Set configuration value at runtime

## ChromaDB Knowledge Base (Jarvis GUI)

Integrated into the original Jarvis GUI (`assistant_gui.py`):

- On startup: loads `memory.json` facts and `conversation_history.txt` into ChromaDB
- On every query: searches knowledge base and injects relevant context before LLM call
- Runtime learning: say `"learn from C:\path\to\file.txt"` to ingest any file

Knowledge base stored at: `c:\Users\svet\Documents\GitHub\Жаравиз\jarvis_knowledge\`

## Model Routing

- **Coding queries** (code, script, function, python, debug, implement, error, bug) → `deepseek-coder-v2:16b`
- **Tiny queries** (single word < 15 chars) → tiny model
- **Default** → `mistral-small:22b`

## Safety Features

- **Sandbox mode**: Simulate commands without execution
- **File protection**: Blocks dangerous file operations
- **Action logging**: Logs all PC commands
- **Configurable safety**: Toggle safety mode in config

## File Locations

- MCP Config: `~/.jarvis_mcp/config.json`
- MCP Memory: `~/.jarvis_mcp/memory.json`
- MCP Personality: `~/.jarvis_mcp/personality.txt`
- Windsurf MCP Config: `c:\Users\svet\.codeium\windsurf\mcp_config.json`
- Knowledge Base: `c:\Users\svet\Documents\GitHub\Жаравиз\jarvis_knowledge\`
- Server (no Cyrillic): `c:\Users\svet\jarvis_mcp\`

## Troubleshooting

**MCP server not appearing in Windsurf:**
- Edit `c:\Users\svet\.codeium\windsurf\mcp_config.json` directly (not `settings.json`)
- Path must not contain Cyrillic characters — use `c:\Users\svet\jarvis_mcp\`

**Kimi K2.6:cloud error 403:**
- Cloud model requires authentication. Use local models instead (mistral-small:22b)

**Backend not responding:**
- Check if Ollama is running: `ollama serve`
- Verify host URL in config with `config_get` tool

**ChromaDB knowledge base not loading:**
- Check `jarvis_knowledge/` directory exists in Jarvis project root
- Errors are non-fatal — Jarvis will continue without knowledge context

## License

Personal project for local AI assistant development.
