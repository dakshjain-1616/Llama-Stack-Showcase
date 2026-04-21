"""
File I/O Tool with Step Logging Callbacks

Provides file operations with logging callbacks for streaming
progress updates to the UI. All operations are sandboxed to workspace/.
"""

import os
import json
from typing import Callable, Dict, Any, Optional, List
from pathlib import Path


class FileIOTool:
    """
    File I/O tool that yields step events during file operations.
    All operations are restricted to a sandboxed workspace directory.
    """
    
    def __init__(
        self, 
        logger_callback: Optional[Callable[[str], None]] = None,
        workspace_dir: str = "workspace"
    ):
        """
        Initialize the file I/O tool.
        
        Args:
            logger_callback: Optional callback function for logging steps
            workspace_dir: Directory to sandbox all file operations to
        """
        self.logger_callback = logger_callback
        self.workspace_dir = Path(workspace_dir).resolve()
        # Ensure workspace exists
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
    
    def _log(self, message: str) -> None:
        """Internal logging helper that calls the callback if provided."""
        if self.logger_callback:
            self.logger_callback(message)
    
    def _resolve_path(self, filepath: str) -> Path:
        """
        Resolve a path relative to the workspace directory.
        Prevents directory traversal attacks.
        
        Args:
            filepath: Relative or absolute path
            
        Returns:
            Resolved Path object within workspace
        """
        # Convert to Path and resolve
        path = Path(filepath)
        
        # If absolute, check if it's within workspace
        if path.is_absolute():
            try:
                path.relative_to(self.workspace_dir)
                return path
            except ValueError:
                # Path is outside workspace, force into workspace
                return self.workspace_dir / path.name
        else:
            # Relative path, resolve within workspace
            return (self.workspace_dir / path).resolve()
    
    def _is_safe_path(self, path: Path) -> bool:
        """
        Check if a path is within the workspace directory.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is within workspace
        """
        try:
            path.relative_to(self.workspace_dir)
            return True
        except ValueError:
            return False
    
    def read_file(self, filepath: str) -> Dict[str, Any]:
        """
        Read a file and return its contents.
        
        Args:
            filepath: Path to file (relative to workspace)
            
        Returns:
            Dictionary with file contents or error
        """
        self._log(f"→ tool called: read_file('{filepath}')")
        
        try:
            resolved_path = self._resolve_path(filepath)
            
            if not self._is_safe_path(resolved_path):
                error_msg = f"Access denied: path outside workspace"
                self._log(f"← error: {error_msg}")
                return {"success": False, "error": error_msg}
            
            if not resolved_path.exists():
                error_msg = f"File not found: {filepath}"
                self._log(f"← error: {error_msg}")
                return {"success": False, "error": error_msg}
            
            if not resolved_path.is_file():
                error_msg = f"Not a file: {filepath}"
                self._log(f"← error: {error_msg}")
                return {"success": False, "error": error_msg}
            
            # Read file
            content = resolved_path.read_text(encoding='utf-8')
            
            # Log success with size
            size = len(content)
            self._log(f"← result: read {size} bytes from {filepath}")
            
            return {
                "success": True,
                "content": content,
                "path": str(resolved_path),
                "size": size
            }
            
        except Exception as e:
            error_msg = f"Read error: {str(e)}"
            self._log(f"← error: {error_msg}")
            return {"success": False, "error": error_msg}
    
    def write_file(self, filepath: str, content: str) -> Dict[str, Any]:
        """
        Write content to a file.
        
        Args:
            filepath: Path to file (relative to workspace)
            content: Content to write
            
        Returns:
            Dictionary with write result
        """
        content_preview = content[:50].replace('\n', ' ')
        if len(content) > 50:
            content_preview += "..."
        self._log(f"→ tool called: write_file('{filepath}', '{content_preview}')")
        
        try:
            resolved_path = self._resolve_path(filepath)
            
            if not self._is_safe_path(resolved_path):
                error_msg = f"Access denied: path outside workspace"
                self._log(f"← error: {error_msg}")
                return {"success": False, "error": error_msg}
            
            # Ensure parent directory exists
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            resolved_path.write_text(content, encoding='utf-8')
            
            size = len(content)
            self._log(f"← result: wrote {size} bytes to {filepath}")
            
            return {
                "success": True,
                "path": str(resolved_path),
                "size": size
            }
            
        except Exception as e:
            error_msg = f"Write error: {str(e)}"
            self._log(f"← error: {error_msg}")
            return {"success": False, "error": error_msg}
    
    def list_files(self, directory: str = ".") -> Dict[str, Any]:
        """
        List files in a directory.
        
        Args:
            directory: Directory path (relative to workspace)
            
        Returns:
            Dictionary with file list
        """
        self._log(f"→ tool called: list_files('{directory}')")
        
        try:
            resolved_path = self._resolve_path(directory)
            
            if not self._is_safe_path(resolved_path):
                error_msg = f"Access denied: path outside workspace"
                self._log(f"← error: {error_msg}")
                return {"success": False, "error": error_msg}
            
            if not resolved_path.exists():
                error_msg = f"Directory not found: {directory}"
                self._log(f"← error: {error_msg}")
                return {"success": False, "error": error_msg}
            
            if not resolved_path.is_dir():
                error_msg = f"Not a directory: {directory}"
                self._log(f"← error: {error_msg}")
                return {"success": False, "error": error_msg}
            
            # List files
            files = []
            for item in resolved_path.iterdir():
                file_info = {
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                }
                files.append(file_info)
            
            self._log(f"← result: found {len(files)} items in {directory}")
            
            return {
                "success": True,
                "path": str(resolved_path),
                "files": files,
                "count": len(files)
            }
            
        except Exception as e:
            error_msg = f"List error: {str(e)}"
            self._log(f"← error: {error_msg}")
            return {"success": False, "error": error_msg}
    
    def delete_file(self, filepath: str) -> Dict[str, Any]:
        """
        Delete a file.
        
        Args:
            filepath: Path to file (relative to workspace)
            
        Returns:
            Dictionary with deletion result
        """
        self._log(f"→ tool called: delete_file('{filepath}')")
        
        try:
            resolved_path = self._resolve_path(filepath)
            
            if not self._is_safe_path(resolved_path):
                error_msg = f"Access denied: path outside workspace"
                self._log(f"← error: {error_msg}")
                return {"success": False, "error": error_msg}
            
            if not resolved_path.exists():
                error_msg = f"File not found: {filepath}"
                self._log(f"← error: {error_msg}")
                return {"success": False, "error": error_msg}
            
            if resolved_path.is_dir():
                error_msg = f"Cannot delete directory: {filepath}"
                self._log(f"← error: {error_msg}")
                return {"success": False, "error": error_msg}
            
            # Delete file
            resolved_path.unlink()
            
            self._log(f"← result: deleted {filepath}")
            
            return {
                "success": True,
                "path": str(resolved_path)
            }
            
        except Exception as e:
            error_msg = f"Delete error: {str(e)}"
            self._log(f"← error: {error_msg}")
            return {"success": False, "error": error_msg}


def create_file_io_tool(
    logger_callback: Optional[Callable[[str], None]] = None,
    workspace_dir: str = "workspace"
) -> FileIOTool:
    """
    Factory function to create a file I/O tool instance.
    
    Args:
        logger_callback: Optional callback for logging steps
        workspace_dir: Directory to sandbox operations to
        
    Returns:
        Configured FileIOTool instance
    """
    return FileIOTool(logger_callback, workspace_dir)
