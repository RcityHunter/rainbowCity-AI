import asyncio
import os
import sys
import logging
import pytest
from dotenv import load_dotenv
from datetime import datetime

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the necessary modules
from app.services.memory_service import MemoryService
from app.models.memory_models import MemoryQuery, MemoryType
from app.db import query, create, update, delete, get_db

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@pytest.mark.asyncio
async def test_search_memories():
    """Test the search_memories method to ensure it properly handles different return types"""
    try:
        # Create a test memory
        user_id = "test_user_" + datetime.now().strftime("%Y%m%d%H%M%S")
        memory_data = {
            "user_id": user_id,
            "content": "This is a test memory",
            "memory_type": MemoryType.USER_MEMORY.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Create the memory in the database
        logger.info(f"Creating test memory for user {user_id}")
        create_result = await create('memory', memory_data)
        logger.info(f"Create result: {create_result}")
        
        # Create a query to search for the memory
        query_params = MemoryQuery(
            user_id=user_id,
            limit=10,
            sort_by="recency",
            use_vector_search=False
        )
        
        # Search for the memory
        logger.info(f"Searching for memories for user {user_id}")
        search_results = await MemoryService.search_memories(query_params)
        
        # Verify the results
        logger.info(f"Search results type: {type(search_results)}")
        logger.info(f"Found {len(search_results)} memories")
        
        # Check that the results are a list
        assert isinstance(search_results, list), f"Expected list but got {type(search_results)}"
        
        # Check that we found at least one memory
        assert len(search_results) > 0, "No memories found"
        
        # Check that the memory content matches
        found = False
        for memory in search_results:
            if memory.get('content') == "This is a test memory":
                found = True
                break
        
        assert found, "Test memory not found in search results"
        
        # Clean up - delete the test memory
        for memory in search_results:
            if memory.get('user_id') == user_id:
                await delete('memory', {'id': memory.get('id')})
        
        logger.info("Test completed successfully")
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_search_memories())
