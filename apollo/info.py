"""
Command-line tool to display version information for ApolloAgent.

This script allows users to check the current version and metadata
of their ApolloAgent installation.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import sys
import json
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


if __name__ == "__main__":
    as_json = "--json" in sys.argv
    print_version_info(print_json=as_json)
