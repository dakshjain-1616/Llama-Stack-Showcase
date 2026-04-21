"""
Code Execution Tool with Step Logging Callbacks

Provides safe code execution functionality with logging callbacks
for streaming progress updates to the UI.
"""

import subprocess
import tempfile
import os
import sys
from typing import Callable, Dict, Any, Optional, List
from pathlib import Path
import json


class CodeExecutionTool:
    """
    Code execution tool that yields step events during execution.
    Supports Python code execution with safety constraints.
    """
    
    def __init__(
        self, 
        logger_callback: Optional[Callable[[str], None]] = None,
        timeout: int = 10,
        allowed_imports: Optional[List[str]] = None
    ):
        """
        Initialize the code execution tool.
        
        Args:
            logger_callback: Optional callback function for logging steps
            timeout: Maximum execution time in seconds
            allowed_imports: List of allowed import modules (None = common safe ones)
        """
        self.logger_callback = logger_callback
        self.timeout = timeout
        self.allowed_imports = allowed_imports or [
            "os", "sys", "json", "math", "random", "datetime", 
            "collections", "itertools", "functools", "re", "string",
            "typing", "pathlib", "hashlib", "base64", "uuid"
        ]
    
    def _log(self, message: str) -> None:
        """Internal logging helper that calls the callback if provided."""
        if self.logger_callback:
            self.logger_callback(message)
    
    def _validate_code(self, code: str) -> tuple[bool, str]:
        """
        Validate code for safety before execution.
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for dangerous imports and functions
        dangerous_patterns = [
            "__import__", "eval(", "exec(", "compile(", 
            "open(", "file(", "subprocess", "os.system", "os.popen",
            "os.spawn", "os.fork", "os.kill", "os.remove", "os.rmdir",
            "shutil.rmtree", "import socket",
            "import urllib", "import requests", "import ftplib"
        ]
        
        for pattern in dangerous_patterns:
            if pattern in code:
                return False, f"Security violation: '{pattern}' is not allowed"
        
        return True, ""
    
    def execute(
        self, 
        code: str, 
        language: str = "python",
        capture_output: bool = True
    ) -> Dict[str, Any]:
        """
        Execute code safely and return results.
        
        Args:
            code: Code to execute
            language: Programming language (currently only 'python' supported)
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            Dictionary with execution results
        """
        # Log the execution call
        code_preview = code[:100].replace('\n', ' ')
        if len(code) > 100:
            code_preview += "..."
        self._log(f"→ tool called: execute_code('{code_preview}')")
        self._log(f"→ language: {language}")
        
        if language.lower() != "python":
            error_msg = f"Language '{language}' not supported. Only Python is supported."
            self._log(f"← error: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "stdout": "",
                "stderr": error_msg,
                "returncode": -1
            }
        
        # Validate code
        is_valid, error_msg = self._validate_code(code)
        if not is_valid:
            self._log(f"← validation error: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "stdout": "",
                "stderr": error_msg,
                "returncode": -1
            }
        
        self._log("→ validating code... [PASS]")
        
        try:
            # Create temporary file for execution
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            self._log(f"→ executing in sandbox (timeout: {self.timeout}s)...")
            
            # Execute with timeout
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=capture_output,
                text=True,
                timeout=self.timeout,
                cwd=str(Path(temp_file).parent)
            )
            
            # Clean up temp file
            try:
                os.remove(temp_file)
            except:
                pass
            
            # Log results
            if result.returncode == 0:
                self._log(f"← execution successful (exit code: 0)")
                if result.stdout:
                    stdout_preview = result.stdout[:200].replace('\n', ' ')
                    if len(result.stdout) > 200:
                        stdout_preview += "..."
                    self._log(f"← stdout: {stdout_preview}")
            else:
                self._log(f"← execution failed (exit code: {result.returncode})")
                if result.stderr:
                    stderr_preview = result.stderr[:200].replace('\n', ' ')
                    if len(result.stderr) > 200:
                        stderr_preview += "..."
                    self._log(f"← stderr: {stderr_preview}")
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            self._log(f"← error: Execution timed out after {self.timeout}s")
            # Clean up temp file
            try:
                os.remove(temp_file)
            except:
                pass
            return {
                "success": False,
                "error": f"Execution timed out after {self.timeout} seconds",
                "stdout": "",
                "stderr": f"Timeout after {self.timeout}s",
                "returncode": -1
            }
            
        except Exception as e:
            self._log(f"← error: {str(e)}")
            # Clean up temp file
            try:
                os.remove(temp_file)
            except:
                pass
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }


def create_execution_tool(
    logger_callback: Optional[Callable[[str], None]] = None,
    timeout: int = 10
):
    """
    Factory function to create a code execution tool instance.
    
    Args:
        logger_callback: Optional callback for logging steps
        timeout: Maximum execution time in seconds
        
    Returns:
        Configured CodeExecutionTool instance
    """
    return CodeExecutionTool(logger_callback, timeout)
