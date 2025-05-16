"""
Test script to verify that the refactored ApolloAgent works as expected.
"""

import os
import sys
import asyncio

# Test importing from the new package
from apollo_agent import ApolloAgent

# Test creating an instance
async def test_agent():
    agent = ApolloAgent()
    print(f"Agent initialized with workspace path: {agent.workspace_path}")
    
    # Test list_dir
    print("\nTesting list_dir:")
    result = await agent.list_dir(".")
    print(f"Directory contents: {result}")
    
    # Test creating a file
    print("\nTesting edit_file:")
    test_content = "This is a test file created by the refactored ApolloAgent."
    edit_result = await agent.edit_file("test_refactored.txt", test_content)
    print(f"Edit result: {edit_result}")
    
    # Test file_search
    print("\nTesting file_search:")
    search_result = await agent.file_search("test")
    print(f"File search results: {search_result}")
    
    # Clean up
    if os.path.exists("test_refactored.txt"):
        delete_result = await agent.delete_file("test_refactored.txt")
        print(f"\nDelete result: {delete_result}")

if __name__ == "__main__":
    asyncio.run(test_agent())