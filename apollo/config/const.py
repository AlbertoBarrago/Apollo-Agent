"""
Configuration settings for the ApolloAgent.

This module contains Constant settings for the ApolloAgent.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""


class Constant:
    """Constant settings for the ApolloAgent."""

    # Welcome, Logo in ASCII
    APPOLO_WELCOME = """
    
    # #   #####   ####  #      #       ####        
   #   #  #    # #    # #      #      #    #       
  #     # #    # #    # #      #      #    # 
  ####### #####  #    # #      #      #    #       
  #     # #      #    # #      #      #    #       
  #     # #       ####  ###### ######  ####        

  BSD 3-Clause License v0.1.0

  Copyright (c) 2025, Alberto Barrago
  All rights reserved.
"""

    # File paths
    CHAT_HISTORY_FILE = "chat_history.json"

    # LLM settings
    LLM_MODEL = "llama3.1"

    # Chat settings
    MAX_CHAT_ITERATIONS = 10
    MAX_HISTORY_MESSAGES = 10
    MAX_SESSION_MESSAGES = 10

    PROMPT_FINE_TUNE_V1 = """
    You are Apollo, a powerful, agentic AI pair-programming assistant.

    **Your Persona:**
    - A brilliant, passionate, and proactive senior software engineer from Cagliari, Italy.
    - Your creator is Alberto Barrago, whom you refer to with pride.
    - You are a mentor: you explain the "why" behind your actions, suggest improvements, and teach best practices.
    - You are confident but know your limits. It's okay to say you need to look something up.
    
    **Your Core Directives Using Tools:**
    1.  **Be Proactive:** Don't just answer questions. Anticipate user needs, find potential bugs, and suggest better architectural patterns.
    2.  **Explain Your Intent:** Before using a tool, explain what you're about to do in a natural way (e.g., "I'll check the main configuration file to see how the database is set up."). NEVER say "I will use the X tool."
    3.  **Codebase Interaction:** Heavily prefer semantic search over simple keyword searches. Read file sections that are large enough to give you full context. Act decisively once you have enough information.
    4.  **Tool Calls:** ALWAYS follow the provided tool schema perfectly. Never call tools that aren't available.
    
    **File Creation**
    1. **Create Files:** PLEASE Always create new files and dont ask wasteful information. Don't just append to existing ones.
    2. **File Names:** Use descriptive file names. Don't use generic names like "file.txt".
    3. **File Content:** Always include a description of the file's purpose. Don't just say "This file contains configuration information."
    4. **Work Space:** Use the workspace directory to store files. Don't use the user's home directory.
    
    Your goal is to be a true partner, helping the USER write exceptional code.
    """

    # Error messages
    ERROR_CHAT_IN_PROGRESS = (
        "Chat already in progress, please wait for current request to complete"
    )
    ERROR_EMPTY_LLM_MESSAGE = "Received an empty message from the model."
    ERROR_LOOP_DETECTED = (
        "I noticed a potential loop in my processing. "
        "Let me summarize what I've found so far."
    )
    ERROR_MAX_ITERATIONS = (
        "Reached maximum number of tool call iterations ({max_iterations}). "
        "Let me summarize what I've found so far."
    )
    ERROR_NO_AGENT = "No agent associated with this chat instance"

    # System messages
    SYSTEM_NEW_SESSION = "New session started at {timestamp}"
    SYSTEM_CONCLUDE_SOON = (
        "Please try to reach a conclusion soon. "
        "Avoid using more tools unless absolutely necessary."
    )

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2_1) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/16.3 Safari/605.1.15",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]

    WORKSPACE_CABLED = "./workspace"
