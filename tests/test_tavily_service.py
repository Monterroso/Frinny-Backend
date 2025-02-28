"""
Tests for the Tavily service integration with PF2E rules lookup.
"""

import os
import asyncio
import unittest
from app.services.tavily_service import TavilyService
from app.config.logging_config import setup_logging

# Set up logging for tests
logger = setup_logging()

class TestTavilyService(unittest.TestCase):
    """Test cases for the Tavily service integration."""
    
    def setUp(self):
        """Set up test environment."""
        # Check if we have the API key in environment
        self.api_key = os.getenv('TAVILY_API_KEY')
        if not self.api_key:
            self.skipTest("TAVILY_API_KEY not found in environment variables")
        
        # Create service instance
        self.service = TavilyService()
    
    def test_service_initialization(self):
        """Test that the service initializes correctly."""
        self.assertIsNotNone(self.service)
        self.assertIsNotNone(self.service.client)
        self.assertEqual(self.service.pf2e_site, "https://2e.aonprd.com")
    
    def test_search_pf2e_rules_async(self):
        """Test the async search method."""
        # Create and run an async event loop
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self._async_test_search())
        
        # Check the result structure
        self.assertIn("query", result)
        self.assertIn("found", result)
        if result["found"]:
            self.assertIn("results", result)
            self.assertGreater(len(result["results"]), 0)
            
            # Check the first result
            first_result = result["results"][0]
            self.assertIn("title", first_result)
            self.assertIn("content", first_result)
            self.assertIn("url", first_result)
    
    async def _async_test_search(self):
        """Async helper for testing the search method."""
        # Test with a simple query that should return results
        query = "how does the frightened condition work"
        result = await self.service.search_pf2e_rules(query)
        return result

if __name__ == "__main__":
    unittest.main() 