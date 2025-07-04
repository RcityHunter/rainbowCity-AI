"""
Test script to verify the fix for the 'list' object has no attribute 'items' error
in the memory service.
"""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Override SurrealDB URL to match the Docker container port
os.environ["SURREAL_URL"] = "ws://localhost:8080"

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the necessary modules
from app.db import query, get_db
from app.models.memory_models import MemoryQuery, MemoryType
from app.services.memory_service import MemoryService

async def test_query_result_handling():
    """
    Test that the query function properly handles different return types
    and that the memory service can handle both list and dictionary results.
    """
    try:
        # Connect to the database
        db = await get_db()
        if db is None:
            logger.error("Failed to connect to database")
            return False
        
        logger.info("Testing direct database query...")
        
        # Test a direct query that might return a list or a dictionary
        result = await query('memory', {}, limit=5)
        
        # Check the result type
        logger.info(f"Query result type: {type(result)}")
        if isinstance(result, list):
            logger.info(f"Result is a list with {len(result)} items")
            if len(result) > 0:
                logger.info(f"First item type: {type(result[0])}")
        elif isinstance(result, dict):
            logger.info("Result is a dictionary")
            logger.info(f"Keys: {result.keys()}")
        else:
            logger.info(f"Result is of type: {type(result)}")
        
        # Now test the memory service search function
        logger.info("\nTesting memory service search_memories...")
        
        # Create a simple query
        memory_query = MemoryQuery(
            limit=5,
            sort_by="recency",
            use_vector_search=False
        )
        
        # Call the search_memories method
        memories = await MemoryService.search_memories(memory_query)
        
        # Check the result
        logger.info(f"search_memories result type: {type(memories)}")
        logger.info(f"Found {len(memories)} memories")
        
        # Verify that the result is always a list
        assert isinstance(memories, list), f"Expected list but got {type(memories)}"
        
        logger.info("Test completed successfully - the fix is working!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_query_result_handling())
    sys.exit(0 if success else 1)
