"""
Gradio UI with Live Log Streaming

Provides a Gradio interface with tabs (Research, Code, Pipeline, History)
supporting live log streaming, per-run model/temperature selection,
and conversation history export.
"""

import os
import json
import tempfile
from typing import Iterator, Tuple, Optional
import gradio as gr

# Import tools
from .tools import create_search_tool, create_execution_tool, create_file_io_tool
from .history import ConversationHistory

# Import agents
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from demos import ResearchAgent, CodeGenerationAgent, PipelineAgent

# Import client
try:
    from .client import create_client, LlamaStackClient
except ImportError:
    create_client = None
    LlamaStackClient = None


MODEL_CHOICES = [
    "meta-llama/Llama-4-Scout-17B-16E-Instruct",
    "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "meta-llama/Llama-3.1-8B-Instruct-Turbo",
]
DEFAULT_MODEL = MODEL_CHOICES[0]
DEFAULT_TEMPERATURE = 0.7


class LlamaStackUI:
    """
    Gradio UI for Llama Stack Showcase with live log streaming,
    per-run model/temperature, and conversation history.
    """

    def __init__(self):
        """Initialize the UI and its components."""
        self.client = None
        self.search_tool = None
        self.execution_tool = None
        self.file_io_tool = None
        self.research_agent = None
        self.code_agent = None
        self.pipeline_agent = None
        self.history = ConversationHistory(max_entries=50)

        # Initialize tools and agents
        self._initialize_components()

    def _initialize_components(self):
        """Initialize all tools and agents."""
        try:
            if create_client:
                self.client = create_client()
        except Exception:
            pass

        self.search_tool = create_search_tool()
        self.execution_tool = create_execution_tool()
        self.file_io_tool = create_file_io_tool()

        self.research_agent = ResearchAgent(
            client=self.client,
            search_tool=self.search_tool
        )
        self.code_agent = CodeGenerationAgent(
            client=self.client,
            execution_tool=self.execution_tool
        )
        self.pipeline_agent = PipelineAgent(
            client=self.client,
            search_tool=self.search_tool,
            execution_tool=self.execution_tool
        )

    def _build_client(self, model: Optional[str], temperature: Optional[float]):
        """Build a fresh LlamaStackClient per run, falling back to self.client on error."""
        if LlamaStackClient is None:
            return self.client
        try:
            return LlamaStackClient(
                model=model or DEFAULT_MODEL,
                temperature=float(temperature) if temperature is not None else DEFAULT_TEMPERATURE,
            )
        except Exception:
            return self.client

    def run_research(
        self,
        query: str,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> Iterator[Tuple[str, str]]:
        """Run the research agent and yield (log, output) tuples."""
        if not query.strip():
            yield "Please enter a query", ""
            return

        logs = []
        final_result = None
        client = self._build_client(model, temperature)

        agent = ResearchAgent(client=client, search_tool=self.search_tool)

        for event in agent.run(query):
            if event.get("type") == "log":
                logs.append(event.get("message", ""))
                yield "\n".join(logs), "Processing..."
            elif event.get("type") == "result":
                content = event.get("content", {})
                final_result = self._format_research_result(content)

        log_text = "\n".join(logs)
        output = final_result or "No result generated"
        # Record to history
        try:
            self.history.add(
                tab="research",
                query=query,
                result_summary=output,
                logs=log_text,
                model=model,
                temperature=temperature,
            )
        except Exception:
            pass
        yield log_text, output

    def run_code(
        self,
        task: str,
        language: str = "python",
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> Iterator[Tuple[str, str]]:
        """Run the code generation agent."""
        if not task.strip():
            yield "Please enter a task", ""
            return

        logs = []
        final_result = None
        client = self._build_client(model, temperature)

        agent = CodeGenerationAgent(client=client, execution_tool=self.execution_tool)

        for event in agent.run(task, language):
            if event.get("type") == "log":
                logs.append(event.get("message", ""))
                yield "\n".join(logs), "Processing..."
            elif event.get("type") == "result":
                content = event.get("content", {})
                final_result = self._format_code_result(content)

        log_text = "\n".join(logs)
        output = final_result or "No result generated"
        try:
            self.history.add(
                tab="code",
                query=task,
                result_summary=output,
                logs=log_text,
                model=model,
                temperature=temperature,
            )
        except Exception:
            pass
        yield log_text, output

    def run_pipeline(
        self,
        query: str,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> Iterator[Tuple[str, str]]:
        """Run the pipeline agent."""
        if not query.strip():
            yield "Please enter a query", ""
            return

        logs = []
        final_result = None
        client = self._build_client(model, temperature)

        agent = PipelineAgent(
            client=client,
            search_tool=self.search_tool,
            execution_tool=self.execution_tool,
        )

        for event in agent.run(query):
            if event.get("type") == "log":
                logs.append(event.get("message", ""))
                yield "\n".join(logs), "Processing..."
            elif event.get("type") == "result":
                content = event.get("content", {})
                final_result = self._format_pipeline_result(content)

        log_text = "\n".join(logs)
        output = final_result or "No result generated"
        try:
            self.history.add(
                tab="pipeline",
                query=query,
                result_summary=output,
                logs=log_text,
                model=model,
                temperature=temperature,
            )
        except Exception:
            pass
        yield log_text, output

    def _format_research_result(self, content: dict) -> str:
        result = f"""## Research Results

**Query:** {content.get('query', 'N/A')}

**Summary:**
{content.get('summary', 'No summary available')}

**Sources Found:** {content.get('findings_count', 0)}
"""
        if content.get('sources'):
            result += "\n**References:**\n"
            for i, source in enumerate(content['sources'][:5], 1):
                result += f"{i}. {source}\n"
        return result

    def _format_code_result(self, content: dict) -> str:
        result = f"""## Code Generation Results

**Task:** {content.get('task', 'N/A')}
**Language:** {content.get('language', 'python')}
**Success:** {'✓' if content.get('success') else '✗'}
**Iterations:** {content.get('iterations', 0)}

### Generated Code:
```python
{content.get('code', 'No code generated')}
```
"""
        if content.get('stdout'):
            result += f"\n### Output:\n```\n{content['stdout']}\n```\n"
        if content.get('stderr'):
            result += f"\n### Errors:\n```\n{content['stderr']}\n```\n"
        return result

    def _format_pipeline_result(self, content: dict) -> str:
        result = f"""## Pipeline Results

**Query:** {content.get('query', 'N/A')}
**Success:** {'✓' if content.get('success') else '✗'}

**Search Results:** {content.get('search_count', 0)} sources found
**Code Length:** {content.get('code_length', 0)} characters

### Final Output:
{content.get('final_output', 'No output available')}
"""
        if content.get('execution_stdout'):
            result += f"\n### Execution Output:\n```\n{content['execution_stdout']}\n```\n"
        return result

    def _render_history(self) -> str:
        return self.history.format_display()

    def _export_history_file(self) -> str:
        """Export history to a temp JSON file and return its path for download."""
        tmp_dir = tempfile.mkdtemp(prefix="llama_history_")
        path = os.path.join(tmp_dir, "conversation_history.json")
        self.history.export_json(path)
        return path

    def _clear_history(self) -> str:
        self.history.clear()
        return self._render_history()

    def _build_controls(self):
        """Build shared model/temperature controls inside an Accordion."""
        with gr.Accordion("⚙️ Model & Temperature", open=False):
            model_dd = gr.Dropdown(
                choices=MODEL_CHOICES,
                value=DEFAULT_MODEL,
                label="Model",
            )
            temp_slider = gr.Slider(
                minimum=0.0,
                maximum=1.5,
                value=DEFAULT_TEMPERATURE,
                step=0.1,
                label="Temperature",
            )
        return model_dd, temp_slider

    def create_interface(self) -> gr.Blocks:
        """Create and return the Gradio interface."""
        # In Gradio 6.x theme should be passed to launch(); we store it on the
        # Blocks instance so create_ui() consumers can forward it.
        with gr.Blocks(title="Llama Stack Showcase") as demo:
            demo._theme = gr.themes.Soft()
            gr.Markdown("""
            # 🦙 Llama Stack Showcase

            Interactive agents powered by Llama via Together AI.
            Watch live logs as agents search, generate code, and execute tasks.
            """)

            with gr.Tabs():
                # Research Tab
                with gr.TabItem("🔍 Research"):
                    gr.Markdown("Search the web and synthesize findings.")
                    research_input = gr.Textbox(
                        label="Research Query",
                        placeholder="Enter your research question...",
                        lines=2,
                    )
                    research_model, research_temp = self._build_controls()
                    with gr.Row():
                        research_run_btn = gr.Button("Run Research", variant="primary")
                        research_clear_btn = gr.Button("Clear")
                    with gr.Row():
                        with gr.Column(scale=1):
                            research_log = gr.Textbox(
                                label="Live Logs", lines=15, max_lines=30,
                                autoscroll=True, interactive=False,
                            )
                        with gr.Column(scale=2):
                            research_output = gr.Markdown(label="Results")
                    research_run_btn.click(
                        fn=self.run_research,
                        inputs=[research_input, research_model, research_temp],
                        outputs=[research_log, research_output],
                    )
                    research_clear_btn.click(fn=lambda: ("", ""), outputs=[research_log, research_output])

                # Code Tab
                with gr.TabItem("💻 Code"):
                    gr.Markdown("Generate and execute code with self-correction.")
                    code_input = gr.Textbox(
                        label="Task Description",
                        placeholder="Describe what code you need...",
                        lines=3,
                    )
                    code_language = gr.Dropdown(choices=["python"], value="python", label="Language")
                    code_model, code_temp = self._build_controls()
                    with gr.Row():
                        code_run_btn = gr.Button("Generate & Run", variant="primary")
                        code_clear_btn = gr.Button("Clear")
                    with gr.Row():
                        with gr.Column(scale=1):
                            code_log = gr.Textbox(
                                label="Live Logs", lines=15, max_lines=30,
                                autoscroll=True, interactive=False,
                            )
                        with gr.Column(scale=2):
                            code_output = gr.Markdown(label="Results")
                    code_run_btn.click(
                        fn=self.run_code,
                        inputs=[code_input, code_language, code_model, code_temp],
                        outputs=[code_log, code_output],
                    )
                    code_clear_btn.click(fn=lambda: ("", ""), outputs=[code_log, code_output])

                # Pipeline Tab
                with gr.TabItem("🔄 Pipeline"):
                    gr.Markdown("Search + generate + execute in one workflow.")
                    pipeline_input = gr.Textbox(
                        label="Pipeline Query",
                        placeholder="Describe what to search for and process...",
                        lines=2,
                    )
                    pipeline_model, pipeline_temp = self._build_controls()
                    with gr.Row():
                        pipeline_run_btn = gr.Button("Run Pipeline", variant="primary")
                        pipeline_clear_btn = gr.Button("Clear")
                    with gr.Row():
                        with gr.Column(scale=1):
                            pipeline_log = gr.Textbox(
                                label="Live Logs", lines=15, max_lines=30,
                                autoscroll=True, interactive=False,
                            )
                        with gr.Column(scale=2):
                            pipeline_output = gr.Markdown(label="Results")
                    pipeline_run_btn.click(
                        fn=self.run_pipeline,
                        inputs=[pipeline_input, pipeline_model, pipeline_temp],
                        outputs=[pipeline_log, pipeline_output],
                    )
                    pipeline_clear_btn.click(fn=lambda: ("", ""), outputs=[pipeline_log, pipeline_output])

                # History Tab
                with gr.TabItem("📋 History"):
                    gr.Markdown("Past runs across all tabs (capped at 50, FIFO).")
                    history_view = gr.Markdown(value=self._render_history())
                    with gr.Row():
                        refresh_btn = gr.Button("🔄 Refresh", variant="secondary")
                        clear_btn = gr.Button("🗑️ Clear History")
                        download_btn = gr.Button("⬇️ Download JSON", variant="primary")
                    download_file = gr.File(label="Exported history", interactive=False)

                    refresh_btn.click(fn=self._render_history, outputs=[history_view])
                    clear_btn.click(fn=self._clear_history, outputs=[history_view])
                    download_btn.click(fn=self._export_history_file, outputs=[download_file])

            gr.Markdown("""
            ---
            Powered by [Llama Stack](https://github.com/meta-llama/llama-stack)
            and [Together AI](https://together.ai)
            """)

        return demo


def create_ui() -> gr.Blocks:
    """Factory function to create the Gradio UI."""
    ui = LlamaStackUI()
    return ui.create_interface()


if __name__ == "__main__":
    demo = create_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860, theme=getattr(demo, "_theme", None))
