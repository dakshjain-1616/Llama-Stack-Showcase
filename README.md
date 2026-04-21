# 🦙 Llama Stack Showcase

> 🤖 **Autonomously built using [NEO](https://heyneo.com) — Your Autonomous AI Engineering Agent**
>
> [![VS Code Extension](https://img.shields.io/badge/VS%20Code-NEO%20Extension-007ACC?logo=visual-studio-code&logoColor=white)](https://marketplace.visualstudio.com/items?itemName=NeoResearchInc.heyneo) [![Cursor Extension](https://img.shields.io/badge/Cursor-NEO%20Extension-000000?logo=cursor&logoColor=white)](https://marketplace.cursorapi.com/items/?itemName=NeoResearchInc.heyneo)

<p align="center">
  <img src="assets/infographic.svg" alt="Llama Stack Showcase Architecture" width="820" />
</p>

Interactive agents powered by Meta's Llama-4-Scout via Together AI, featuring live log streaming and real-time execution visualization.

## ✨ New Features

### 1. Conversation History & Export

Every run from the Research, Code, and Pipeline tabs is automatically recorded to an in-memory, FIFO-capped (50 entries) history. A new **📋 History** tab shows the scrollable list and lets you export all entries to a JSON file with one click.

In the UI, open the **📋 History** tab and click **⬇️ Download JSON** to save the file, or **🗑️ Clear History** to reset.

### 2. Per-Run Model + Temperature Selection

Each agent tab now has a **⚙️ Model & Temperature** accordion with:

- **Model dropdown** (default `meta-llama/Llama-4-Scout-17B-16E-Instruct`, plus `Llama-3.3-70B-Instruct-Turbo` and `Llama-3.1-8B-Instruct-Turbo`)
- **Temperature slider** (0.0 – 1.5, step 0.1, default 0.7)

A fresh `LlamaStackClient(model=..., temperature=...)` is constructed per run, so you can switch models mid-session without restarting the app.

---

## Overview

This project demonstrates agentic workflows using the Llama Stack framework with Together AI's Llama-4-Scout model. It includes three interactive agents:

- **🔍 Research Agent**: Web search and synthesis with DuckDuckGo
- **💻 Code Agent**: Code generation with self-correction and execution
- **🔄 Pipeline Agent**: Combined search + code execution workflow

All agents feature **live log streaming** to visualize each step in real-time.

## Project Structure

```
llama-stack-showcase/
├── src/
│   ├── __init__.py
│   ├── client.py          # LlamaStackClient for Together AI
│   ├── ui.py              # Gradio UI with streaming support
│   └── tools/
│       ├── __init__.py
│       ├── search.py      # DuckDuckGo web search
│       ├── execute.py     # Safe code execution
│       └── file_io.py     # Sandboxed file operations
├── demos/
│   ├── __init__.py
│   ├── research_agent.py  # Research agent with generator interface
│   ├── code_agent.py      # Code generation with self-correction
│   └── pipeline_agent.py  # Combined pipeline agent
├── docs/
│   ├── ARCHITECTURE.md    # Architecture documentation
│   ├── API.md            # API reference
│   ├── demo_video_script.md
│   └── huggingface-spaces.md
├── app.py                # HuggingFace Spaces entry point
├── requirements.txt
├── .env.example
└── README.md
```

## Setup Instructions

### 1. Clone and Install

```bash
git clone <repository-url>
cd llama-stack-showcase

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Together AI API key
TOGETHER_API_KEY=your_api_key_here
LLAMA_STACK_ENDPOINT=https://api.together.xyz/v1
DEFAULT_MODEL=meta-llama/Llama-4-Scout-17B-16E-Instruct
```

### 3. Run Locally

```bash
python app.py
```

The UI will be available at `http://localhost:7860`

## Llama Stack vs Direct API Comparison

| Feature | Llama Stack | Direct API |
|---------|-------------|------------|
| **Abstraction Level** | High-level agent framework | Low-level HTTP requests |
| **Tool Integration** | Built-in tool calling | Manual implementation |
| **Streaming** | Native generator support | Manual chunk handling |
| **Safety** | Sandboxed execution | User-managed |
| **Self-Correction** | Built-in iteration loops | Custom logic required |
| **Setup Complexity** | Single client initialization | Manual auth, headers, parsing |
| **Code Lines** | ~50 for full agent | ~200+ for equivalent |

**Recommendation**: Use Llama Stack for rapid agent development; use Direct API for fine-grained control.

## Usage Examples

The Research, Code, and Pipeline agents are accessible through the Gradio UI tabs, each streaming live log events and yielding a final result.

## Architecture

The project follows a layered architecture:

```
┌─────────────────────────────────────────┐
│           Gradio UI Layer             │
│    (src/ui.py - Streaming Interface)   │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│          Agent Layer                  │
│  (demos/research_agent.py, etc.)      │
│  - Generator interfaces               │
│  - Step event yielding                │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│          Client Layer                 │
│    (src/client.py - Together AI)      │
│  - Llama-4-Scout integration          │
│  - Tool calling support                 │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│          Tools Layer                  │
│  (src/tools/search.py, etc.)          │
│  - DuckDuckGo search                  │
│  - Code execution (sandboxed)         │
│  - File I/O (workspace only)          │
└─────────────────────────────────────────┘
```

### Streaming Flow

1. **User Input** → Gradio UI captures query
2. **Agent.run()** → Generator yields step events
3. **Log Callback** → Each step logs to streaming textbox
4. **Tool Execution** → Tools log their operations
5. **Final Result** → Formatted output displayed

## Deployment

### HuggingFace Spaces

1. Create a new Space at [huggingface.co/spaces](https://huggingface.co/spaces)
2. Select "Gradio" as the SDK
3. Upload files or connect GitHub repository
4. Set environment variable `TOGETHER_API_KEY` in Space settings
5. Deploy!

See `docs/huggingface-spaces.md` for detailed instructions.

### GitHub Repository

```bash
# Initialize git
git init
git add .
git commit -m "Initial commit: Llama Stack Showcase"

# Add remote and push
git remote add origin <your-repo-url>
git push -u origin main
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TOGETHER_API_KEY` | Together AI API key | Yes |
| `LLAMA_STACK_ENDPOINT` | API endpoint URL | No (default: https://api.together.xyz/v1) |
| `DEFAULT_MODEL` | Model identifier | No (default: meta-llama/Llama-4-Scout-17B-16E-Instruct) |

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Please ensure:
- Code follows PEP 8 style
- All tests pass (`python -m pytest`)
- New features include documentation

## Acknowledgments

- [Meta Llama Stack](https://github.com/meta-llama/llama-stack)
- [Together AI](https://together.ai)
- [Gradio](https://gradio.app)
