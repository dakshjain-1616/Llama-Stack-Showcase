"""
Pipeline Agent with Generator Interface

Provides a pipeline agent that combines search + code execution.
Yields step events for streaming to the UI.
"""

import json
from typing import Iterator, Dict, Any, Optional, Callable, List
from dataclasses import dataclass


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""
    query: str
    search_results: List[Dict[str, Any]]
    generated_code: str
    execution_result: Optional[Dict[str, Any]]
    final_output: str
    success: bool


class PipelineAgent:
    """
    Pipeline agent that combines web search with code generation and execution.
    
    Workflow:
    1. Search for information related to the query
    2. Generate code based on search results
    3. Execute the generated code
    4. Return combined results
    
    Uses a generator interface to yield step events for live streaming.
    """
    
    def __init__(
        self,
        client=None,
        search_tool=None,
        execution_tool=None,
        max_search_results: int = 5
    ):
        """
        Initialize the pipeline agent.
        
        Args:
            client: LlamaStackClient instance
            search_tool: WebSearchTool instance
            execution_tool: CodeExecutionTool instance
            max_search_results: Maximum search results per query
        """
        self.client = client
        self.search_tool = search_tool
        self.execution_tool = execution_tool
        self.max_search_results = max_search_results
        self.logs: List[str] = []
    
    def _log(self, message: str) -> None:
        """Log a message and store it."""
        self.logs.append(message)
    
    def run(self, query: str) -> Iterator[Dict[str, Any]]:
        """
        Run the pipeline agent with the given query.
        
        Yields step events like:
        - {"type": "log", "message": "→ phase 1: searching..."}
        - {"type": "log", "message": "→ tool called: web_search('...')"}
        - {"type": "log", "message": "→ phase 2: generating code..."}
        - {"type": "log", "message": "→ phase 3: executing..."}
        - {"type": "result", "content": final_result}
        
        Args:
            query: Pipeline query (describes what to search for and process)
            
        Yields:
            Step event dictionaries
        """
        self.logs = []
        
        # Initial log
        self._log(f"→ starting pipeline: '{query}'")
        yield {"type": "log", "message": self.logs[-1]}
        
        # Phase 1: Search
        self._log("→ phase 1: gathering information via search...")
        yield {"type": "log", "message": self.logs[-1]}
        
        search_results = []
        if self.search_tool:
            search_logs = []
            def search_callback(msg: str):
                search_logs.append(msg)
                self._log(msg)
            
            original_callback = self.search_tool.logger_callback
            self.search_tool.logger_callback = search_callback
            
            try:
                search_results = self.search_tool.search(query, max_results=self.max_search_results)
            finally:
                self.search_tool.logger_callback = original_callback
            
            for log_msg in search_logs:
                yield {"type": "log", "message": log_msg}
        else:
            # Mock search
            self._log(f"→ tool called: web_search('{query}')")
            yield {"type": "log", "message": self.logs[-1]}
            
            search_results = [
                {"index": 1, "title": f"Data source for {query}", "href": "https://example.com/data", "body": f"Sample data about {query}"}
            ]
            self._log(f"← result: {len(search_results)} hits")
            yield {"type": "log", "message": self.logs[-1]}
        
        # Phase 2: Generate code based on search results
        self._log("→ phase 2: generating code from search results...")
        yield {"type": "log", "message": self.logs[-1]}
        
        # Build context from search results
        context_parts = []
        for result in search_results:
            if "error" not in result:
                context_parts.append(f"[{result['index']}] {result['title']}: {result['body']}")
        
        context = "\n".join(context_parts)
        
        generated_code = None
        if self.client:
            system_prompt = """You are a data processing expert. Based on the search results provided,
generate Python code that processes or analyzes this information. Return ONLY the code, no explanations."""
            
            user_prompt = f"""Task: {query}

Search Results:
{context}

Generate Python code to process this information:"""
            
            try:
                generated_code = self.client.simple_chat(user_prompt, system_prompt)
                generated_code = self._clean_code(generated_code)
                self._log(f"← model reasoning: generated code ({len(generated_code)} chars)")
                yield {"type": "log", "message": self.logs[-1]}
            except Exception as e:
                self._log(f"← error: {str(e)}")
                yield {"type": "log", "message": self.logs[-1]}
                generated_code = self._generate_mock_pipeline_code(query)
        else:
            generated_code = self._generate_mock_pipeline_code(query)
            self._log(f"← model reasoning: generated code ({len(generated_code)} chars)")
            yield {"type": "log", "message": self.logs[-1]}
        
        # Phase 3: Execute code
        self._log("→ phase 3: executing generated code...")
        yield {"type": "log", "message": self.logs[-1]}
        
        execution_result = None
        if self.execution_tool:
            exec_logs = []
            def exec_callback(msg: str):
                exec_logs.append(msg)
                self._log(msg)
            
            original_callback = self.execution_tool.logger_callback
            self.execution_tool.logger_callback = exec_callback
            
            try:
                execution_result = self.execution_tool.execute(generated_code, "python")
            finally:
                self.execution_tool.logger_callback = original_callback
            
            for log_msg in exec_logs:
                yield {"type": "log", "message": log_msg}
        else:
            self._log("→ tool called: execute_code('...')")
            yield {"type": "log", "message": self.logs[-1]}
            
            execution_result = {
                "success": True,
                "stdout": f"Processed data for: {query}",
                "stderr": "",
                "returncode": 0
            }
            self._log("← execution successful (exit code: 0)")
            yield {"type": "log", "message": self.logs[-1]}
        
        # Phase 4: Synthesize final output
        self._log("→ phase 4: synthesizing final output...")
        yield {"type": "log", "message": self.logs[-1]}
        
        stdout = execution_result.get("stdout", "") if execution_result else ""
        final_output = f"""Pipeline Results for: {query}

Search Summary:
- Found {len(search_results)} relevant sources
- Key information gathered from web search

Code Execution:
{stdout}

Status: {'✓ Success' if execution_result and execution_result.get('success') else '✗ Failed'}"""
        
        self._log("← model reasoning: final synthesis complete")
        yield {"type": "log", "message": self.logs[-1]}
        
        # Final result
        pipeline_result = PipelineResult(
            query=query,
            search_results=search_results,
            generated_code=generated_code,
            execution_result=execution_result,
            final_output=final_output,
            success=execution_result.get("success", False) if execution_result else False
        )
        
        self._log("✓ pipeline complete")
        yield {"type": "log", "message": self.logs[-1]}
        
        yield {
            "type": "result",
            "content": {
                "query": pipeline_result.query,
                "final_output": pipeline_result.final_output,
                "success": pipeline_result.success,
                "search_count": len(pipeline_result.search_results),
                "code_length": len(pipeline_result.generated_code),
                "execution_stdout": stdout
            }
        }
    
    def _clean_code(self, code: str) -> str:
        """Clean up code by removing markdown formatting."""
        if code.startswith("```"):
            lines = code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)
        return code.strip()
    
    def _generate_mock_pipeline_code(self, query: str) -> str:
        """Generate mock pipeline code for demo purposes."""
        return f'''# Pipeline code for: {query}
def process_data():
    """Process data based on search results."""
    print(f"Processing: {query}")
    
    # Simulate data processing
    data = {{"query": "{query}", "status": "processed"}}
    
    # Output results
    print(f"Results: {{data}}")
    return data

if __name__ == "__main__":
    result = process_data()
    print(f"Final output: {{result}}")
'''
    
    def get_logs(self) -> List[str]:
        """Get all accumulated logs."""
        return self.logs.copy()


def create_pipeline_agent(client=None, search_tool=None, execution_tool=None) -> PipelineAgent:
    """
    Factory function to create a PipelineAgent instance.
    
    Args:
        client: LlamaStackClient instance
        search_tool: WebSearchTool instance
        execution_tool: CodeExecutionTool instance
        
    Returns:
        Configured PipelineAgent instance
    """
    return PipelineAgent(client=client, search_tool=search_tool, execution_tool=execution_tool)
