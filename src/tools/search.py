"""
Web Search Tool with Step Logging Callbacks

Provides web search functionality using DuckDuckGo with logging callbacks
for streaming progress updates to the UI.
"""

from typing import Callable, List, Dict, Any, Optional
try:
    from ddgs import DDGS
except ImportError:  # fallback to older package name
    from duckduckgo_search import DDGS
import json


class WebSearchTool:
    """
    Web search tool that yields step events during search operations.
    """
    
    def __init__(self, logger_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize the web search tool.
        
        Args:
            logger_callback: Optional callback function for logging steps
        """
        self.logger_callback = logger_callback
        self.ddgs = DDGS()
    
    def _log(self, message: str) -> None:
        """Internal logging helper that calls the callback if provided."""
        if self.logger_callback:
            self.logger_callback(message)
    
    def search(
        self, 
        query: str, 
        max_results: int = 5,
        region: str = "wt-wt",
        safesearch: str = "moderate"
    ) -> List[Dict[str, Any]]:
        """
        Perform a web search and return results.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            region: Region for search results
            safesearch: Safe search setting
            
        Returns:
            List of search result dictionaries
        """
        # Log the search call
        self._log(f"→ tool called: web_search('{query}')")
        
        try:
            # Perform the search
            results = list(self.ddgs.text(
                query,
                region=region,
                safesearch=safesearch,
                max_results=max_results
            ))
            
            # Log the result count
            self._log(f"← result: {len(results)} hits")
            
            # Format results
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_result = {
                    "index": i,
                    "title": result.get("title", "No title"),
                    "href": result.get("href", ""),
                    "body": result.get("body", "No description")
                }
                formatted_results.append(formatted_result)
                
                # Log each result briefly
                self._log(f"  [{i}] {formatted_result['title'][:60]}...")
            
            return formatted_results
            
        except Exception as e:
            error_msg = f"Search error: {str(e)}"
            self._log(f"← error: {error_msg}")
            return [{"error": error_msg}]
    
    def search_with_context(
        self, 
        query: str, 
        context: Optional[str] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Perform a contextual web search with additional logging.
        
        Args:
            query: Search query string
            context: Additional context for the search
            max_results: Maximum number of results
            
        Returns:
            Dictionary containing search results and metadata
        """
        if context:
            self._log(f"→ context provided: {context[:100]}...")
        
        results = self.search(query, max_results)
        
        return {
            "query": query,
            "context": context,
            "results": results,
            "count": len(results)
        }


def create_search_tool(logger_callback: Optional[Callable[[str], None]] = None) -> WebSearchTool:
    """
    Factory function to create a web search tool instance.
    
    Args:
        logger_callback: Optional callback for logging steps
        
    Returns:
        Configured WebSearchTool instance
    """
    return WebSearchTool(logger_callback)
