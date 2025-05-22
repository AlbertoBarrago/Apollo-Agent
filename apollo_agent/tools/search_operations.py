"""
Search operations for the ApolloAgent.

This module contains functions for search operations like codebase search,
grep search, and file search.

Author: Alberto Barrago
License: BSD 3-Clause License - 2024
"""

import os
import re
import fnmatch
from typing import List, Dict, Any


async def codebase_search(
    agent, query: str, target_directories: List[str] = None
) -> Dict[str, Any]:
    """
    Find snippets of code from the codebase most relevant to the search query.
    This is a semantic search tool.

    Args:
        agent: The root path of the workspace.
        query: The search query.
        target_directories: List of directories to search in, relative to workspace_path.

    Returns:
        Dictionary with search results.
    """
    results = []
    search_dirs = target_directories if target_directories else [agent.workspace_path]

    for directory in search_dirs:
        absolute_dir = os.path.abspath(directory)
        if not absolute_dir.startswith(os.path.abspath(agent.workspace_path)):
            print(f"[WARNING] Skipping directory outside workspace: {directory}")
            continue

        if not os.path.isdir(absolute_dir):
            print(f"[WARNING] Path is not a directory, skipping: {directory}")
            continue

        for root, _, files in os.walk(absolute_dir):
            for file in files:
                if file.endswith(
                    (
                        ".py",
                        ".js",
                        ".ts",
                        ".html",
                        ".css",
                        ".java",
                        ".c",
                        ".cpp",
                        ".txt",
                    )
                ):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            if query.lower() in content.lower():
                                results.append(
                                    {
                                        "file_path": os.path.relpath(
                                            file_path, agent.workspace_path
                                        ),
                                        "content_snippet": (
                                            content[:500] + "..."
                                            if len(content) > 500
                                            else content
                                        ),
                                        "relevance_score": 0.8,
                                    }
                                )
                    except OSError as e:
                        print(f"[ERROR] Error reading file {file_path}: {e}")

    return {"query": query, "results": results}


def _match_pattern_sync(filename: str, pattern: str) -> bool:
    """
    Synchronous check if a filename matches a glob pattern.

    Args:
        filename: The filename to check.
        pattern: The glob pattern to match against.

    Returns:
        True if the filename matches the pattern, False otherwise.
    """
    return fnmatch.fnmatch(filename, pattern)


async def grep_search(
    agent,
    query: str,
    case_sensitive: bool = False,
    include_pattern: str = None,
    exclude_pattern: str = None,
) -> Dict[str, Any]:
    """
    Fast text-based regex search that finds exact pattern matches within files or directories.
    Best for finding specific strings or patterns.

    Args:
        agent: Apollo agent instance.
        query: The regex pattern to search for.
        case_sensitive: Whether the search should be case-sensitive.
        include_pattern: Glob pattern for files to include (e.g. '*.ts').
        exclude_pattern: Glob pattern for files to exclude.

    Returns:
        Dictionary with search results.
    """
    results = []
    flags = 0 if case_sensitive else re.IGNORECASE

    # Note: A real implementation would ideally use `ripgrep` via a subprocess
    # for better performance and features.

    for root, _, files in os.walk(agent.workspace_path):
        for file in files:
            file_path = os.path.join(root, file)
            relative_file_path = os.path.relpath(file_path, agent.workspace_path)

            if include_pattern and not _match_pattern_sync(file, include_pattern):
                continue
            if exclude_pattern and _match_pattern_sync(file, exclude_pattern):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        if re.search(query, line, flags=flags):
                            results.append(
                                {
                                    "file": relative_file_path,
                                    "line_number": i,
                                    "content": line.strip(),
                                }
                            )
                            if len(results) >= 50:
                                break

            except OSError as e:
                print(f"[ERROR] Error reading file {file_path}: {e}")

            if len(results) >= 50:
                break

    return {
        "query": query,
        "case_sensitive": case_sensitive,
        "include_pattern": include_pattern,
        "exclude_pattern": exclude_pattern,
        "results": results,
        "total_matches": len(results),
        "capped": len(results) >= 50,
    }


async def file_search(agent, query: str) -> Dict[str, Any]:
    """
    Fast file search based on fuzzy matching against a file path.

    Args:
        agent: Apollo agent instance.
        query: Fuzzy filename to search for.

    Returns:
        Dictionary with search results.
    """
    results = []

    for root, _, files in os.walk(agent.workspace_path):
        for file in files:
            if query.lower() in file.lower():
                file_path = os.path.join(root, file)
                results.append(
                    {
                        "file_path": os.path.relpath(file_path, agent.workspace_path),
                        "filename": file,
                    }
                )

                if len(results) >= 10:
                    break

        if len(results) >= 10:
            break

    return {
        "query": query,
        "results": results,
        "total_matches": len(results),
        "capped": len(results) >= 10,
    }
