"""
Llama Stack Client for Together AI

Provides a client interface for Together AI's Llama-4-Scout model
with streaming support for agent workflows.
"""

import os
import json
from typing import Iterator, Dict, Any, Optional, List, Callable
from dataclasses import dataclass


@dataclass
class Message:
    """Represents a message in the conversation."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None


class LlamaStackClient:
    """
    Client for Together AI's Llama-4-Scout model.
    
    This client provides a simple interface for chat completions
    with optional tool calling support.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        """
        Initialize the Llama Stack client.

        Defaults to OpenRouter (OpenAI-compatible) using OPENROUTER_API_KEY.
        Falls back to TOGETHER_API_KEY / Together AI if OPENROUTER_API_KEY is unset.
        Override via LLAMA_BASE_URL / LLAMA_MODEL env vars or explicit args.
        """
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        together_key = os.getenv("TOGETHER_API_KEY")
        local_flag = os.getenv("LLAMA_LOCAL", "").lower() in ("1", "true", "yes")

        if local_flag or (not api_key and not openrouter_key and not together_key):
            self.api_key = api_key or "local"
            default_base = os.getenv("LLAMA_BASE_URL") or "http://localhost:11434/v1"
            default_model = os.getenv("LLAMA_MODEL") or "llama3.2"
        elif api_key:
            self.api_key = api_key
            default_base = "https://openrouter.ai/api/v1"
            default_model = "meta-llama/llama-4-scout"
        elif openrouter_key:
            self.api_key = openrouter_key
            default_base = "https://openrouter.ai/api/v1"
            default_model = "meta-llama/llama-4-scout"
        else:
            self.api_key = together_key
            default_base = "https://api.together.xyz/v1"
            default_model = "meta-llama/Llama-4-Scout-17B-16E-Instruct"

        self.base_url = base_url or os.getenv("LLAMA_BASE_URL") or default_base
        self.model = model or os.getenv("LLAMA_MODEL") or default_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Try to import openai client (Together AI uses OpenAI-compatible API)
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        except ImportError:
            self.client = None
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto",
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Send a chat completion request.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            tools: Optional list of tool definitions
            tool_choice: Tool choice strategy ("auto", "none", or specific tool)
            stream: Whether to stream the response
            
        Returns:
            Response dictionary
        """
        if self.client is None:
            raise ImportError("OpenAI client not available. Install with: pip install openai")
        
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream
        }
        
        if tools:
            params["tools"] = tools
            params["tool_choice"] = tool_choice
        
        try:
            response = self.client.chat.completions.create(**params)
            
            if stream:
                return self._handle_streaming_response(response)
            else:
                return self._format_response(response)
                
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    def _handle_streaming_response(self, response) -> Iterator[str]:
        """Handle streaming response chunks."""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def _format_response(self, response) -> Dict[str, Any]:
        """Format the API response into a standard dictionary."""
        if not response.choices:
            return {
                "error": "No response choices available",
                "success": False
            }
        
        choice = response.choices[0]
        message = choice.message
        
        result = {
            "success": True,
            "content": message.content or "",
            "role": message.role,
            "finish_reason": choice.finish_reason
        }
        
        # Include tool calls if present
        if hasattr(message, 'tool_calls') and message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]
        
        return result
    
    def chat_with_tools(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: List[Dict],
        logger_callback: Optional[Callable[[str], None]] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Chat with tool calling support, yielding step events.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            tools: List of available tools
            logger_callback: Optional callback for logging
            
        Yields:
            Step event dictionaries
        """
        def log(msg: str):
            if logger_callback:
                logger_callback(msg)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        log("→ model reasoning: processing request...")
        
        # Initial request
        response = self.chat(messages, tools=tools)
        
        if "error" in response:
            log(f"← error: {response['error']}")
            yield {"step": "error", "content": response["error"]}
            return
        
        # Check for tool calls
        if "tool_calls" in response and response["tool_calls"]:
            for tool_call in response["tool_calls"]:
                func = tool_call["function"]
                log(f"→ tool call requested: {func['name']}({func['arguments']})")
                
                yield {
                    "step": "tool_call",
                    "tool_name": func["name"],
                    "arguments": func["arguments"],
                    "call_id": tool_call["id"]
                }
            
            # Add assistant response to messages
            messages.append({
                "role": "assistant",
                "content": response.get("content", ""),
                "tool_calls": response.get("tool_calls", [])
            })
            
            # In a real implementation, we'd execute tools and continue the conversation
            # For now, yield the model's reasoning
            if response.get("content"):
                log(f"← model reasoning: {response['content'][:200]}...")
                yield {
                    "step": "reasoning",
                    "content": response["content"]
                }
        else:
            # No tool calls, just content
            content = response.get("content", "")
            log(f"← model response: {content[:200]}...")
            yield {
                "step": "response",
                "content": content
            }
    
    def simple_chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Simple chat without streaming.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Response content as string
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.chat(messages)
        
        if "error" in response:
            return f"Error: {response['error']}"
        
        return response.get("content", "")


def create_client(
    api_key: Optional[str] = None,
    model: str = "meta-llama/Llama-4-Scout-17B-16E-Instruct"
) -> LlamaStackClient:
    """
    Factory function to create a LlamaStackClient instance.
    
    Args:
        api_key: Together AI API key
        model: Model identifier
        
    Returns:
        Configured LlamaStackClient instance
    """
    return LlamaStackClient(api_key=api_key, model=model)
