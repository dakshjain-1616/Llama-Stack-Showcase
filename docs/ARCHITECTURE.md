# Architecture Documentation

## System Overview

The Llama Stack Showcase implements a layered architecture for building and visualizing agentic workflows powered by Meta's Llama-4-Scout model via Together AI.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Gradio UI (src/ui.py)                 │   │
│  │  • Four-tab interface (Research, Code, Pipeline,   │   │
│  │    History) + per-tab Model/Temperature accordion  │   │
│  │  • Streaming log panels with real-time updates     │   │
│  │  • Generator-based event handling                  │   │
│  │  • ConversationHistory (FIFO, 50 entries, JSON     │   │
│  │    export) via src/history.py                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Agent Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Research   │  │    Code     │  │      Pipeline       │ │
│  │   Agent     │  │    Agent    │  │       Agent         │ │
│  │             │  │             │  │                     │ │
│  │ • Web search│  │ • Code gen  │  │ • Search + Code     │ │
│  │ • Synthesis │  │ • Execute   │  │ • Combined workflow │ │
│  │ • Reporting │  │ • Self-corr │  │ • End-to-end        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                             │
│  Common Pattern: Generator interface yielding step events    │
│  for (log_update, output) tuples → Gradio streaming        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Client Layer                              │
│              src/client.py - LlamaStackClient               │
│                                                             │
│  • Together AI API integration                               │
│  • Llama-4-Scout model (meta-llama/Llama-4-Scout-17B-16E)   │
│  • Tool calling support                                      │
│  • Streaming response handling                               │
│  • Error handling and retries                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Tools Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Search    │  │   Execute   │  │      File I/O       │ │
│  │    Tool     │  │    Tool     │  │       Tool          │ │
│  │             │  │             │  │                     │ │
│  │ • DuckDuckGo│  │ • Python    │  │ • Read/Write        │ │
│  │ • Web API   │  │ • Subprocess│  │ • List/Delete       │ │
│  │ • Results   │  │ • Timeout   │  │ • Sandboxed         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                             │
│  All tools implement logger_callback for step streaming      │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Gradio UI (src/ui.py)

**Responsibilities:**
- User interface with three tabs
- Real-time log streaming via `gr.Textbox` with generator-based updates
- Generator function integration for live updates
- Result formatting and display

**Key Classes:**
- `LlamaStackUI`: Main UI controller
- Generator methods: `run_research()`, `run_code()`, `run_pipeline()`

**Streaming Pattern:**
```python
def run_research(self, query: str) -> Iterator[Tuple[str, str]]:
    logs = []
    for event in agent.run(query):
        if event["type"] == "log":
            logs.append(event["message"])
            yield "\n".join(logs), "Processing..."
        elif event["type"] == "result":
            yield "\n".join(logs), formatted_result
```

### 2. Agent Layer (demos/)

**Common Interface:**
All agents implement a generator pattern:
```python
def run(self, query: str) -> Iterator[Dict[str, Any]]:
    yield {"type": "log", "message": "→ step description"}
    # ... do work ...
    yield {"type": "log", "message": "← result"}
    yield {"type": "result", "content": {...}}
```

**ResearchAgent:**
- Performs web searches using DuckDuckGo
- Synthesizes findings into markdown reports
- Yields search progress and final summary

**CodeGenerationAgent:**
- Generates Python code from task descriptions
- Executes code in sandboxed environment
- Self-corrects on errors (up to max_iterations)
- Yields generation, execution, and correction steps

**PipelineAgent:**
- Combines search + code generation + execution
- Four-phase workflow: Search → Generate → Execute → Synthesize
- Yields phase transitions and intermediate results

### 3. Client Layer (src/client.py)

**LlamaStackClient:**
- Wraps Together AI's OpenAI-compatible API
- Model: `meta-llama/Llama-4-Scout-17B-16E-Instruct`
- Supports tool calling with `chat_with_tools()`
- Handles streaming responses

**Key Methods:**
- `chat()`: Basic chat completion
- `chat_with_tools()`: Tool-augmented chat with step logging
- `simple_chat()`: Convenience method for simple queries

### 4. Tools Layer (src/tools/)

**WebSearchTool:**
- DuckDuckGo integration via `duckduckgo-search` library
- Configurable max_results, region, safesearch
- Logs: "→ tool called: web_search('...')", "← result: N hits"

**CodeExecutionTool:**
- Subprocess-based Python execution
- 10-second timeout default (configurable via constructor)
- Security validation (blocks dangerous imports and builtins like `eval`, `exec`, `subprocess`, `os.system`, `socket`, `requests`, etc.)
- Sandboxed to temporary files

**FileIOTool:**
- Read/write/list/delete operations
- Sandboxed to `workspace/` directory
- Path traversal protection
- Logs all operations with results

## Data Flow

### Research Flow
```
User Query → ResearchAgent.run()
    ↓
→ tool called: web_search('query')
    ↓
WebSearchTool.search() → DuckDuckGo API
    ↓
← result: N hits
    ↓
→ model reasoning: synthesizing findings...
    ↓
LlamaStackClient.simple_chat() → Together AI
    ↓
← model reasoning: generated summary
    ↓
✓ research complete
    ↓
Yield final result → Gradio UI
```

### Code Generation Flow
```
Task Description → CodeGenerationAgent.run()
    ↓
→ iteration 1/3
    ↓
→ model reasoning: generating initial code...
    ↓
LlamaStackClient.simple_chat() → Together AI
    ↓
← model reasoning: generated code (X chars)
    ↓
→ tool called: execute_code('...')
    ↓
CodeExecutionTool.execute() → Subprocess
    ↓
← execution successful/failed
    ↓
[If failed] → model reasoning: correcting code...
    ↓
[Repeat up to max_iterations]
    ↓
✓ code generation complete
    ↓
Yield final result → Gradio UI
```

### Pipeline Flow
```
Query → PipelineAgent.run()
    ↓
→ phase 1: gathering information via search...
    ↓
[Research phase - same as ResearchAgent]
    ↓
→ phase 2: generating code from search results...
    ↓
[Code generation phase]
    ↓
→ phase 3: executing generated code...
    ↓
[Execution phase - same as CodeAgent]
    ↓
→ phase 4: synthesizing final output...
    ↓
✓ pipeline complete
    ↓
Yield final result → Gradio UI
```

## Security Considerations

### Code Execution Safety
- **Timeout**: All code execution limited by a configurable timeout (default 10 seconds)
- **Sandbox**: Execution in temporary files, not main process
- **Import Validation**: Blocks dangerous imports (os.system, subprocess, etc.)
- **No Network**: Executed code cannot make network requests

### File I/O Safety
- **Workspace Restriction**: All file operations limited to `workspace/` directory
- **Path Traversal Protection**: Resolves and validates all paths
- **No Delete Outside**: Cannot delete files outside workspace

### API Key Security
- Environment variable based (`TOGETHER_API_KEY`)
- Never logged or exposed in UI
- `.env` file support with `.env.example` template

## Extension Points

### Adding New Tools
1. Create new file in `src/tools/`
2. Implement class with `logger_callback` parameter
3. Add to `src/tools/__init__.py`
4. Import and use in agents

### Adding New Agents
1. Create new file in `demos/`
2. Implement generator interface (`run()` method)
3. Yield step events with `{"type": "log", "message": ...}`
4. Add to `demos/__init__.py`
5. Add UI tab in `src/ui.py`

### Customizing UI
- Modify `LlamaStackUI.create_interface()` for layout changes
- Add new generator methods for new agents
- Use `gr.Textbox` with generator yields for live log display

## Performance Considerations

- **Streaming**: Generator pattern prevents blocking UI
- **Timeouts**: All external calls have timeouts
- **Caching**: Consider caching search results for repeated queries
- **Async**: Future versions could use async/await for better concurrency

## Error Handling

All components follow consistent error handling:
1. Try operation
2. Log error with `← error: message`
3. Yield error event
4. Return partial results or graceful failure

Example:
```python
try:
    result = operation()
except Exception as e:
    self._log(f"← error: {str(e)}")
    yield {"type": "log", "message": self.logs[-1]}
    yield {"type": "result", "content": {"success": False, "error": str(e)}}
```
