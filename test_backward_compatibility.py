"""
Test script to verify that backward compatibility works correctly.
This script imports ApolloAgent from both the original agent.py and the new apollo_agent package.
"""

import asyncio

# Test importing from the original agent.py
print("Testing import from agent.py:")
from agent import ApolloAgent as AgentFromOriginal
print(f"Successfully imported ApolloAgent from agent.py: {AgentFromOriginal}")

# Test importing from the new apollo_agent package
print("\nTesting import from apollo_agent package:")
from apollo_agent import ApolloAgent as AgentFromPackage
print(f"Successfully imported ApolloAgent from apollo_agent package: {AgentFromPackage}")

# Verify they are the same class
print("\nVerifying they are the same class:")
print(f"AgentFromOriginal is AgentFromPackage: {AgentFromOriginal is AgentFromPackage}")

# Test creating instances
async def test_instances():
    print("\nTesting instance creation:")
    
    agent1 = AgentFromOriginal()
    print(f"Created instance from agent.py: {agent1}")
    
    agent2 = AgentFromPackage()
    print(f"Created instance from apollo_agent package: {agent2}")
    
    # Test a simple method
    print("\nTesting method calls:")
    result1 = await agent1.list_dir(".")
    print(f"list_dir result from agent.py instance: {result1['success'] if 'success' in result1 else 'OK'}")
    
    result2 = await agent2.list_dir(".")
    print(f"list_dir result from apollo_agent package instance: {result2['success'] if 'success' in result2 else 'OK'}")

if __name__ == "__main__":
    asyncio.run(test_instances())