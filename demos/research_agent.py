"""
Research Agent with Generator Interface

Provides a research agent that uses web search to gather information
and synthesize answers. Yields step events for streaming to the UI.
"""

import json
from typing import Iterator, Dict, Any, Optional, Callable, List
from dataclasses import dataclass


@dataclass
class ResearchResult:
    """Result of a research query."""
    query: str
    findings: List[Dict[str, Any]]
    summary: str
    sources: List[str]


class ResearchAgent:
    """
    Research agent that performs web searches and synthesizes information.
    
    Uses a generator interface to yield step events for live streaming.
    """
    
    def __init__(
        self,
        client=None,
        search_tool=None,
        max_search_results: int = 5
    ):
        """
        Initialize the research agent.
        
        Args:
            client: LlamaStackClient instance
            search_tool: WebSearchTool instance
            max_search_results: Maximum search results per query
        """
        self.client = client
        self.search_tool = search_tool
        self.max_search_results = max_search_results
        self.logs: List[str] = []
    
    def _log(self, message: str) -> None:
        """Log a message and store it."""
        self.logs.append(message)
    
    def run(self, query: str) -> Iterator[Dict[str, Any]]:
        """
        Run the research agent with the given query.
        
        Yields step events like:
        - {"type": "log", "message": "→ tool called: web_search('...')"}
        - {"type": "log", "message": "← result: N hits"}
        - {"type": "log", "message": "→ model reasoning: ..."}
        - {"type": "result", "content": final_result}
        
        Args:
            query: Research query
            
        Yields:
            Step event dictionaries
        """
        self.logs = []
        
        # Initial log
        self._log(f"→ starting research: '{query}'")
        yield {"type": "log", "message": self.logs[-1]}
        
        # Step 1: Perform web search
        if self.search_tool:
            # Set up callback to capture search tool logs
            search_logs = []
            def search_callback(msg: str):
                search_logs.append(msg)
                self._log(msg)
            
            # Temporarily set callback
            original_callback = self.search_tool.logger_callback
            self.search_tool.logger_callback = search_callback
            
            try:
                results = self.search_tool.search(query, max_results=self.max_search_results)
            finally:
                self.search_tool.logger_callback = original_callback
            
            # Yield search logs
            for log_msg in search_logs:
                yield {"type": "log", "message": log_msg}
        else:
            # Mock search results for demo
            self._log(f"→ tool called: web_search('{query}')")
            yield {"type": "log", "message": self.logs[-1]}
            
            results = [
                {
                    "index": 1,
                    "title": f"Result for: {query}",
                    "href": "https://example.com/result1",
                    "body": f"This is a sample search result about {query}."
                },
                {
                    "index": 2,
                    "title": f"Another result about {query}",
                    "href": "https://example.com/result2",
                    "body": f"More information related to {query}."
                }
            ]
            self._log(f"← result: {len(results)} hits")
            yield {"type": "log", "message": self.logs[-1]}
        
        # Step 2: Model reasoning/synthesis
        self._log("→ model reasoning: synthesizing findings...")
        yield {"type": "log", "message": self.logs[-1]}
        
        # Build context from search results
        context_parts = []
        sources = []
        for result in results:
            if "error" not in result:
                context_parts.append(f"[{result['index']}] {result['title']}: {result['body']}")
                sources.append(result.get('href', ''))
        
        context = "\n".join(context_parts)
        
        # Generate summary using client if available
        if self.client:
            system_prompt = """You are a research assistant. Synthesize the provided search results into a clear, concise summary. 
Include key findings and cite the sources. Be factual and objective."""
            
            user_prompt = f"""Query: {query}

Search Results:
{context}

Please provide a comprehensive summary of these findings."""
            
            try:
                summary = self.client.simple_chat(user_prompt, system_prompt)
                self._log(f"← model reasoning: generated summary ({len(summary)} chars)")
                yield {"type": "log", "message": self.logs[-1]}
            except Exception as e:
                summary = f"Error generating summary: {str(e)}"
                self._log(f"← error: {summary}")
                yield {"type": "log", "message": self.logs[-1]}
        else:
            # Mock summary for demo
            summary = f"Based on the search results for '{query}', here are the key findings:\n\n"
            for result in results:
                if "error" not in result:
                    summary += f"• {result['title']}: {result['body'][:100]}...\n"
            
            self._log(f"← model reasoning: generated summary ({len(summary)} chars)")
            yield {"type": "log", "message": self.logs[-1]}
        
        # Final result
        research_result = ResearchResult(
            query=query,
            findings=results,
            summary=summary,
            sources=[s for s in sources if s]
        )
        
        self._log("✓ research complete")
        yield {"type": "log", "message": self.logs[-1]}
        
        # Yield final result
        yield {
            "type": "result",
            "content": {
                "query": research_result.query,
                "summary": research_result.summary,
                "sources": research_result.sources,
                "findings_count": len(research_result.findings)
            }
        }
    
    def get_logs(self) -> List[str]:
        """Get all accumulated logs."""
        return self.logs.copy()


def create_research_agent(client=None, search_tool=None) -> ResearchAgent:
    """
    Factory function to create a ResearchAgent instance.
    
    Args:
        client: LlamaStackClient instance
        search_tool: WebSearchTool instance
        
    Returns:
        Configured ResearchAgent instance
    """
    return ResearchAgent(client=client, search_tool=search_tool)
