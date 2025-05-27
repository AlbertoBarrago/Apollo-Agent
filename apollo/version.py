"""
Version information for ApolloAgent.

This module contains version information and metadata for the ApolloAgent package,
similar to what package.json provides in JavaScript projects.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

__version__ = "0.1.0"

__title__ = "ApolloAgent"
__description__ = (
    "A custom AI agent that implements various functions for code assistance"
)
__author__ = "Alberto Barrago"
__author_email__ = "albertobarrago@gmail.com"
__license__ = "BSD 3-Clause License"
__copyright__ = "Copyright 2024 Alberto Barrago"

__repository__ = "https://github.com/AlbertoBarrago/Apollo-Agent"
__keywords__ = ["ai", "agent", "code-assistant", "llm", "ollama"]
__status__ = "Development"

__requires__ = [
    "ollama",
    "beautifulsoup4",
    "requests",
    "google-generativeai",
    "transformers",
    "torch",
    "accelerate",
    "python-dotenv",
]

__python_requires__ = ">=3.8"
