"""
Demos Package

Provides agent implementations for different use cases:
- research_agent: Web research with search tools
- code_agent: Code generation with execution
- pipeline_agent: Combined search + code execution pipeline
"""

from .research_agent import ResearchAgent
from .code_agent import CodeGenerationAgent
from .pipeline_agent import PipelineAgent

__all__ = [
    "ResearchAgent",
    "CodeGenerationAgent",
    "PipelineAgent"
]
