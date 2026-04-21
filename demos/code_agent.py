"""
Code Generation Agent with Generator Interface

Provides a code generation agent that generates, executes, and
self-corrects code. Yields step events for streaming to the UI.
"""

import json
from typing import Iterator, Dict, Any, Optional, Callable, List
from dataclasses import dataclass


@dataclass
class CodeResult:
    """Result of code generation and execution."""
    task: str
    code: str
    language: str
    execution_result: Optional[Dict[str, Any]]
    iterations: int
    success: bool


class CodeGenerationAgent:
    """
    Code generation agent that generates and executes code.
    
    Uses a generator interface to yield step events for live streaming.
    Supports self-correction through multiple iterations.
    """
    
    def __init__(
        self,
        client=None,
        execution_tool=None,
        max_iterations: int = 3
    ):
        """
        Initialize the code generation agent.
        
        Args:
            client: LlamaStackClient instance
            execution_tool: CodeExecutionTool instance
            max_iterations: Maximum self-correction iterations
        """
        self.client = client
        self.execution_tool = execution_tool
        self.max_iterations = max_iterations
        self.logs: List[str] = []
    
    def _log(self, message: str) -> None:
        """Log a message and store it."""
        self.logs.append(message)
    
    def run(self, task: str, language: str = "python") -> Iterator[Dict[str, Any]]:
        """
        Run the code generation agent with the given task.
        
        Yields step events like:
        - {"type": "log", "message": "→ generating code for: ..."}
        - {"type": "log", "message": "→ executing code..."}
        - {"type": "log", "message": "← execution failed, attempting correction..."}
        - {"type": "result", "content": final_result}
        
        Args:
            task: Code generation task description
            language: Programming language (default: python)
            
        Yields:
            Step event dictionaries
        """
        self.logs = []
        
        # Initial log
        self._log(f"→ starting code generation: '{task}'")
        yield {"type": "log", "message": self.logs[-1]}
        
        self._log(f"→ language: {language}")
        yield {"type": "log", "message": self.logs[-1]}
        
        # Iteration loop for self-correction
        current_code = None
        execution_result = None
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            self._log(f"→ iteration {iteration}/{self.max_iterations}")
            yield {"type": "log", "message": self.logs[-1]}
            
            # Step 1: Generate code
            if current_code is None:
                self._log("→ model reasoning: generating initial code...")
                yield {"type": "log", "message": self.logs[-1]}
                
                if self.client:
                    system_prompt = f"""You are an expert programmer. Generate {language} code to solve the given task.
Return ONLY the code, no explanations. The code should be complete and runnable."""
                    
                    try:
                        current_code = self.client.simple_chat(task, system_prompt)
                        # Clean up code (remove markdown if present)
                        current_code = self._clean_code(current_code)
                        self._log(f"← model reasoning: generated code ({len(current_code)} chars)")
                        yield {"type": "log", "message": self.logs[-1]}
                    except Exception as e:
                        error_msg = f"Error generating code: {str(e)}"
                        self._log(f"← error: {error_msg}")
                        yield {"type": "log", "message": self.logs[-1]}
                        yield {"type": "result", "content": {"success": False, "error": error_msg}}
                        return
                else:
                    # Mock code for demo
                    current_code = self._generate_mock_code(task, language)
                    self._log(f"← model reasoning: generated code ({len(current_code)} chars)")
                    yield {"type": "log", "message": self.logs[-1]}
            else:
                # Self-correction iteration
                self._log("→ model reasoning: correcting code based on errors...")
                yield {"type": "log", "message": self.logs[-1]}
                
                error_context = execution_result.get("stderr", "Unknown error")
                correction_prompt = f"""The previous code had errors:

```
{current_code}
```

Error:
{error_context}

Please fix the code and return ONLY the corrected code."""
                
                if self.client:
                    try:
                        current_code = self.client.simple_chat(correction_prompt)
                        current_code = self._clean_code(current_code)
                        self._log(f"← model reasoning: generated corrected code ({len(current_code)} chars)")
                        yield {"type": "log", "message": self.logs[-1]}
                    except Exception as e:
                        self._log(f"← error: {str(e)}")
                        yield {"type": "log", "message": self.logs[-1]}
                        break
                else:
                    self._log("← model reasoning: mock correction applied")
                    yield {"type": "log", "message": self.logs[-1]}
            
            # Step 2: Execute code
            if self.execution_tool:
                exec_logs = []
                def exec_callback(msg: str):
                    exec_logs.append(msg)
                    self._log(msg)
                
                original_callback = self.execution_tool.logger_callback
                self.execution_tool.logger_callback = exec_callback
                
                try:
                    execution_result = self.execution_tool.execute(current_code, language)
                finally:
                    self.execution_tool.logger_callback = original_callback
                
                # Yield execution logs
                for log_msg in exec_logs:
                    yield {"type": "log", "message": log_msg}
            else:
                # Mock execution for demo
                self._log("→ tool called: execute_code('...')")
                yield {"type": "log", "message": self.logs[-1]}
                
                execution_result = {
                    "success": True,
                    "stdout": "Mock execution output",
                    "stderr": "",
                    "returncode": 0
                }
                self._log("← execution successful (exit code: 0)")
                yield {"type": "log", "message": self.logs[-1]}
            
            # Check if successful
            if execution_result.get("success"):
                self._log("✓ code execution successful")
                yield {"type": "log", "message": self.logs[-1]}
                break
            else:
                self._log("✗ execution failed, will attempt correction")
                yield {"type": "log", "message": self.logs[-1]}
        
        # Final result
        code_result = CodeResult(
            task=task,
            code=current_code,
            language=language,
            execution_result=execution_result,
            iterations=iteration,
            success=execution_result.get("success", False)
        )
        
        self._log(f"✓ code generation complete ({iteration} iterations)")
        yield {"type": "log", "message": self.logs[-1]}
        
        yield {
            "type": "result",
            "content": {
                "task": code_result.task,
                "language": code_result.language,
                "code": code_result.code,
                "success": code_result.success,
                "iterations": code_result.iterations,
                "stdout": execution_result.get("stdout", "") if execution_result else "",
                "stderr": execution_result.get("stderr", "") if execution_result else ""
            }
        }
    
    def _clean_code(self, code: str) -> str:
        """Clean up code by removing markdown formatting."""
        # Remove markdown code blocks
        if code.startswith("```"):
            lines = code.split("\n")
            # Remove first line (```python or ```)
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)
        return code.strip()
    
    def _generate_mock_code(self, task: str, language: str) -> str:
        """Generate mock code for demo purposes."""
        if language.lower() == "python":
            return f'''# Generated code for: {task}
def main():
    print("Executing: {task}")
    # Implementation would go here
    result = "Task completed successfully"
    return result

if __name__ == "__main__":
    output = main()
    print(f"Result: {{output}}")
'''
        else:
            return f"// Code for {task} in {language}\nconsole.log('Hello World');"
    
    def get_logs(self) -> List[str]:
        """Get all accumulated logs."""
        return self.logs.copy()


def create_code_agent(client=None, execution_tool=None) -> CodeGenerationAgent:
    """
    Factory function to create a CodeGenerationAgent instance.
    
    Args:
        client: LlamaStackClient instance
        execution_tool: CodeExecutionTool instance
        
    Returns:
        Configured CodeGenerationAgent instance
    """
    return CodeGenerationAgent(client=client, execution_tool=execution_tool)
