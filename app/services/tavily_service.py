"""
Tavily search service for PF2E rules lookup.
This service handles interactions with the Tavily API to search Pathfinder 2E rules from the Archives of Nethys.
"""

import os
from typing import Dict, List, Optional
from tavily import TavilyClient
from app.config.logging_config import get_logger

# Get module logger
logger = get_logger(__name__)

class TavilyService:
    """
    Service for searching Pathfinder 2E rules using Tavily API.
    This service encapsulates all Tavily API interactions for searching the Archives of Nethys website.
    """
    
    def __init__(self):
        """Initialize the Tavily service with API credentials from environment variables."""
        self.api_key = os.getenv('TAVILY_API_KEY')
        if not self.api_key:
            logger.warning("TAVILY_API_KEY not found in environment variables. Tavily search will not function.")
        self.client = TavilyClient(api_key=self.api_key) if self.api_key else None
        self.pf2e_site = "https://2e.aonprd.com"
    
    async def search_pf2e_rules(self, query: str) -> Dict:
        """
        Search for Pathfinder 2E rules using Tavily API.
        
        Args:
            query: The rules query to search for
            
        Returns:
            Dictionary containing search results with content and source URLs
        """
        if not self.client:
            logger.error("Tavily client is not initialized. Check TAVILY_API_KEY environment variable.")
            return {
                "found": False,
                "message": "Search service is not available. Please contact the administrator.",
                "error": "Tavily API key not configured"
            }
        
        try:
            # Append "pathfinder 2e" to the query to improve relevance
            search_query = f"{query} pathfinder 2e"
            logger.info(f"Searching Tavily for: {search_query} on {self.pf2e_site}")
            
            # Set up search parameters to focus on the PF2E Archives of Nethys site
            search_params = {
                "query": search_query,
                "include_domains": [self.pf2e_site],
                "search_depth": "advanced",
                "max_results": 5
            }
            
            # Execute the search
            response = self.client.search(**search_params)
            
            # Process and format the results
            results = []
            found = False
            
            if response and "results" in response:
                for result in response["results"]:
                    results.append({
                        "title": result.get("title", "Untitled"),
                        "content": result.get("content", "No content available"),
                        "url": result.get("url", ""),
                        "score": result.get("score", 0)
                    })
                found = len(results) > 0
            
            return {
                "query": query,
                "found": found,
                "results": results,
                "suggested_topics": ["Basic rules", "Combat", "Skills", "Spells", "Character creation"] if not found else []
            }
            
        except Exception as e:
            logger.error(f"Error searching Tavily API: {str(e)}")
            return {
                "found": False,
                "message": f"Error occurred during search: {str(e)}",
                "error": str(e)
            }

# Create a singleton instance for global use
tavily_service = TavilyService() 