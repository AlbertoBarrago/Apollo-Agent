"""
Test script to verify that the 'print' tool redirection works correctly.
"""

import asyncio
from apollo_agent import ApolloAgent

async def test_print_tool():
    agent = ApolloAgent(workspace_path="./workspace")
    print("Testing 'print' tool redirection...")
    
    # Simulate a tool call for 'print'
    tool_call = type('obj', (object,), {
        'function': type('obj', (object,), {
            'name': 'print',
            'arguments': '{"text": "Hello from print tool!"}'
        }),
        'id': 'test-call-id'
    })
    
    # Execute the tool call directly
    result = await agent._execute_tool_call(tool_call)
    print(f"Tool call result: {result}")
    
    # Test through the chat interface
    response = await agent.chat("Hello")
    print(f"Chat response: {response}")

if __name__ == "__main__":
    asyncio.run(test_print_tool())