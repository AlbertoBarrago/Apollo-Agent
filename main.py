"""
ApolloAgent is a custom AI agent that implements various functions for code assistance.
Author: Alberto Barrago
License: BSD 3-Clause License - 2025

This file provides backward compatibility for existing code that imports ApolloAgent from here.
The actual implementation has been moved to the apollo package.
"""

import asyncio
import tracemalloc
from apollo import ApolloAgent

if __name__ == "__main__":
    # Enable tracemalloc for memory allocation tracking
    tracemalloc.start()
    asyncio.run(ApolloAgent.chat_terminal())
