"""Command-line interface for ApolloAgent.

This module provides the command-line interface for ApolloAgent,
including version information and chat functionality.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import sys
import json
import argparse
import asyncio
from apollo.agent import ApolloAgent
from apollo.version import (
    __version__,
    __title__,
    __description__,
    __author__,
    __author_email__,
    __license__,
    __copyright__,
    __repository__,
    __keywords__,
    __status__,
    __requires__,
    __python_requires__,
)


def get_version_info():
    """
    Return version information as a dictionary.
    """
    return {
        "name": __title__,
        "version": __version__,
        "description": __description__,
        "author": __author__,
        "author_email": __author_email__,
        "license": __license__,
        "copyright": __copyright__,
        "repository": __repository__,
        "keywords": __keywords__,
        "status": __status__,
        "dependencies": __requires__,
        "python_requires": __python_requires__,
    }


def print_version_info(print_json=False):
    """
    Print version information to the console.

    Args:
        print_json: If True, print information in JSON format.
    """
    info = get_version_info()

    if print_json:
        print(json.dumps(info, indent=2))
    else:
        print(f"{info['name']} v{info['version']}")

        print(f"Description: {info['description']}")
        print(f"Author: {info['author']} <{info['author_email']}>")
        print(f"License: {info['license']}")
        print(f"Status: {info['status']}")
        print(f"Repository: {info['repository']}")
        print("\nDependencies:")
        for dep in info["dependencies"]:
            print(f"  - {dep}")
        print(f"\nRequires Python {info['python_requires']}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='ApolloAgent CLI')
    parser.add_argument('--workspace', type=str, help='Workspace path')
    parser.add_argument('--mode', type=str, choices=['chat', 'execute'], default='chat',
                        help='Operation mode: chat or execute')
    parser.add_argument('--version', action='store_true', help='Show version information')
    parser.add_argument('--json', action='store_true', help='Output version info as JSON')
    return parser.parse_args()

async def run_apollo(args):
    """Run ApolloAgent with the specified arguments."""
    agent = ApolloAgent(workspace_path=args.workspace)
    
    if args.mode == 'chat':
        await agent.chat_terminal()
    elif args.mode == 'execute':
        await agent.execute_tool({})

def main():
    """Main entry point for the CLI."""
    args = parse_args()
    
    try:
        if args.version:
            print_version_info(print_json=args.json)
            return
            
        asyncio.run(run_apollo(args))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)

if __name__ == "__main__":
    main()
