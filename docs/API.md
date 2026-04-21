# API Reference

## Client API

### LlamaStackClient

Main client for Together AI's Llama-4-Scout model.

```python
from src.client import LlamaStackClient, create_client

# Initialize client
client = LlamaStackClient(
    api_key="your_api_key",  # or set TOGETHER_API_KEY env var
    base_url="https://api.together.xyz/v1",
    model="meta-llama/Llama-4-Scout-17B-16E-Instruct",
    temperature=0.7,
    max_tokens=4096
)

# Or use factory function
client = create_client(api_key="your_api_key")
```

#### Methods

##### chat()

Send a chat completion request.

```python
response = client.chat(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    tools=None,  # Optional: list of tool definitions
    tool_choice="auto",  # "auto", "none", or specific tool
    stream=False  # Set True for streaming
)

# Response format
{
    "success": True,
    "content": "Hello! How can I help you today?",
    "role": "assistant",
    "finish_reason": "stop",
    "tool_calls": [...]  # If tools were called
}
```

##### simple_chat()

Convenience method for simple queries.

```python
response = client.simple_chat(
    prompt="What is the capital of France?",
    system_prompt="You are a geography expert."  # Optional
)
# Returns: "The capital of France is Paris."
```

##### chat_with_tools()

Chat with tool calling support, yields step events.

```python
for event in client.chat_with_tools(
    system_prompt="You are a helpful assistant.",
    user_prompt="Search for Python tutorials",
    tools=[...],  # List of tool definitions
    logger_callback=lambda msg: print(msg)
):
    print(event)
    # {"step": "tool_call", "tool_name": "web_search", ...}
    # {"step": "reasoning", "content": "..."}
```

## Tools API

### WebSearchTool

DuckDuckGo web search with logging callbacks.

```python
from src.tools import WebSearchTool, create_search_tool

# Initialize
tool = create_search_tool(
    logger_callback=lambda msg: print(msg)  # Optional
)

# Or with explicit callback
tool = WebSearchTool(
    logger_callback=lambda msg: print(msg)
)

# Search
results = tool.search(
    query="Python programming",
    max_results=5,
    region="wt-wt",
    safesearch="moderate"
)

# Results format
[
    {
        "index": 1,
        "title": "Python Programming Language",
        "href": "https://python.org",
        "body": "Python is a programming language..."
    },
    ...
]
```

### CodeExecutionTool

Safe Python code execution with timeout and validation.

```python
from src.tools import CodeExecutionTool, create_execution_tool

# Initialize
tool = create_execution_tool(
    logger_callback=lambda msg: print(msg),
    timeout=30  # seconds
)

# Execute code
result = tool.execute(
    code="print('Hello, World!')",
    language="python",
    capture_output=True
)

# Result format
{
    "success": True,
    "stdout": "Hello, World!\n",
    "stderr": "",
    "returncode": 0
}
```

**Security Features:**
- 30-second timeout (configurable)
- Blocks dangerous imports (os.system, subprocess, etc.)
- Sandboxed to temporary files
- No network access from executed code

### FileIOTool

Sandboxed file operations restricted to workspace/.

```python
from src.tools import FileIOTool, create_file_io_tool

# Initialize
tool = create_file_io_tool(
    logger_callback=lambda msg: print(msg),
    workspace_dir="workspace"  # Default
)

# Read file
result = tool.read_file("data.txt")
# Returns: {"success": True, "content": "...", "size": 123}

# Write file
result = tool.write_file("output.txt", "Hello, World!")
# Returns: {"success": True, "path": "...", "size": 13}

# List files
result = tool.list_files(".")
# Returns: {"success": True, "files": [...], "count": 5}

# Delete file
result = tool.delete_file("old.txt")
# Returns: {"success": True, "path": "..."}
```

**Security Features:**
- All paths resolved relative to workspace/
- Path traversal protection
- Cannot access files outside workspace

## Agent API

All agents implement a generator interface yielding step events.

### ResearchAgent

Web research and synthesis agent.

```python
from demos import ResearchAgent
from src.tools import create_search_tool
from src.client import create_client

# Initialize
agent = ResearchAgent(
    client=create_client(),  # Optional
    search_tool=create_search_tool(),  # Optional
    max_search_results=5
)

# Run with streaming
for event in agent.run("What are the latest AI developments?"):
    if event["type"] == "log":
        print(event["message"])
        # → starting research: 'What are the latest AI developments?'
        # → tool called: web_search('What are the latest AI developments?')
        # ← result: 5 hits
        # → model reasoning: synthesizing findings...
        # ← model reasoning: generated summary (1234 chars)
        # ✓ research complete
    elif event["type"] == "result":
        print(event["content"])
        # {
        #   "query": "What are the latest AI developments?",
        #   "summary": "...",
        #   "sources": [...],
        #   "findings_count": 5
        # }
```

### CodeGenerationAgent

Code generation with self-correction.

```python
from demos import CodeGenerationAgent
from src.tools import create_execution_tool
from src.client import create_client

# Initialize
agent = CodeGenerationAgent(
    client=create_client(),  # Optional
    execution_tool=create_execution_tool(),  # Optional
    max_iterations=3
)

# Run with streaming
for event in agent.run(
    task="Calculate fibonacci sequence up to 100",
    language="python"
):
    if event["type"] == "log":
        print(event["message"])
        # → starting code generation: 'Calculate fibonacci...'
        # → language: python
        # → iteration 1/3
        # → model reasoning: generating initial code...
        # ← model reasoning: generated code (234 chars)
        # → tool called: execute_code('...')
        # ← execution successful (exit code: 0)
        # ✓ code execution successful
        # ✓ code generation complete (1 iterations)
    elif event["type"] == "result":
        print(event["content"])
        # {
        #   "task": "Calculate fibonacci sequence up to 100",
        #   "language": "python",
        #   "code": "def fibonacci...",
        #   "success": True,
        #   "iterations": 1,
        #   "stdout": "0 1 1 2 3 5...",
        #   "stderr": ""
        # }
```

### PipelineAgent

Combined search + code execution pipeline.

```python
from demos import PipelineAgent
from src.tools import create_search_tool, create_execution_tool
from src.client import create_client

# Initialize
agent = PipelineAgent(
    client=create_client(),  # Optional
    search_tool=create_search_tool(),  # Optional
    execution_tool=create_execution_tool(),  # Optional
    max_search_results=5
)

# Run with streaming
for event in agent.run("Fetch weather data and analyze trends"):
    if event["type"] == "log":
        print(event["message"])
        # → starting pipeline: 'Fetch weather data...'
        # → phase 1: gathering information via search...
        # → tool called: web_search('Fetch weather data...')
        # ← result: 5 hits
        # → phase 2: generating code from search results...
        # ← model reasoning: generated code (567 chars)
        # → phase 3: executing generated code...
        # → tool called: execute_code('...')
        # ← execution successful (exit code: 0)
        # → phase 4: synthesizing final output...
        # ← model reasoning: final synthesis complete
        # ✓ pipeline complete
    elif event["type"] == "result":
        print(event["content"])
        # {
        #   "query": "Fetch weather data and analyze trends",
        #   "final_output": "Pipeline Results...",
        #   "success": True,
        #   "search_count": 5,
        #   "code_length": 567,
        #   "execution_stdout": "Temperature data..."
        # }
```

## UI API

### LlamaStackUI

Gradio interface with streaming support.

```python
from src.ui import LlamaStackUI, create_ui

# Create UI instance
ui = LlamaStackUI()

# Or use factory function
demo = create_ui()

# Launch
demo.launch(
    server_name="0.0.0.0",
    server_port=7860,
    share=False
)
```

#### Generator Methods

All return `Iterator[Tuple[str, str]]` of (logs, output).

```python
# Research tab
for logs, output in ui.run_research("What is machine learning?"):
    print(f"Logs: {logs}")
    print(f"Output: {output}")

# Code tab
for logs, output in ui.run_code(
    task="Sort a list of numbers",
    language="python"
):
    print(f"Logs: {logs}")
    print(f"Output: {output}")

# Pipeline tab
for logs, output in ui.run_pipeline("Analyze stock market trends"):
    print(f"Logs: {logs}")
    print(f"Output: {output}")
```

## Event Types

All agents yield events with this structure:

### Log Event

```python
{
    "type": "log",
    "message": "→ tool called: web_search('query')"
}
```

Common log prefixes:
- `→` - Action starting
- `←` - Result received
- `✓` - Success/completion
- `✗` - Failure

### Result Event

```python
{
    "type": "result",
    "content": {...}  # Agent-specific result structure
}
```

### Error Event

```python
{
    "type": "log",
    "message": "← error: Description of error"
}
```

## Factory Functions

Convenience functions for creating components:

```python
from src.client import create_client
from src.tools import create_search_tool, create_execution_tool, create_file_io_tool
from demos import create_research_agent, create_code_agent, create_pipeline_agent
from src.ui import create_ui

# Create components
client = create_client(api_key="...")
search_tool = create_search_tool()
execution_tool = create_execution_tool(timeout=30)
file_io_tool = create_file_io_tool(workspace_dir="workspace")

# Create agents
research_agent = create_research_agent(client, search_tool)
code_agent = create_code_agent(client, execution_tool)
pipeline_agent = create_pipeline_agent(client, search_tool, execution_tool)

# Create UI
ui = create_ui()
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TOGETHER_API_KEY` | Together AI API key | Required |
| `LLAMA_STACK_ENDPOINT` | API endpoint | `https://api.together.xyz/v1` |
| `DEFAULT_MODEL` | Model identifier | `meta-llama/Llama-4-Scout-17B-16E-Instruct` |

## Error Handling

All components use consistent error handling:

```python
try:
    result = operation()
except Exception as e:
    # Logged as: ← error: {message}
    yield {"type": "log", "message": f"← error: {str(e)}"}
    yield {"type": "result", "content": {"success": False, "error": str(e)}}
```

## Type Hints

Full type hints for all public APIs:

```python
from typing import Iterator, Dict, Any, Optional, Callable, List, Tuple

def run(self, query: str) -> Iterator[Dict[str, Any]]: ...
def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]: ...
def execute(self, code: str, language: str = "python") -> Dict[str, Any]: ...
def run_research(self, query: str) -> Iterator[Tuple[str, str]]: ...
```
