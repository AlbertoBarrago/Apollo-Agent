"""
ApolloAgent is a custom AI agent that implements various functions for code assistance.
Author: Alberto Barrago
License: MIT - 2025

This file provides backward compatibility for existing code that imports ApolloAgent from here.
The actual implementation has been moved to the apollo_agent package.
"""

# Re-export ApolloAgent from the new package
from apollo_agent import ApolloAgent

# For backward compatibility, keep the original imports
import asyncio

# Example usage
if __name__ == "__main__":
    asyncio.run(ApolloAgent.chat_terminal())