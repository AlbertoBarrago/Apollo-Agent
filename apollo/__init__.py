"""
ApolloAgent package initialization.
This file ensures backward compatibility by re-exporting the ApolloAgent class.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

from apollo.agent import ApolloAgent
from apollo.version import (
    __version__,
    __title__,
    __description__,
    __author__,
    __license__,
)


__all__ = ["ApolloAgent"]
