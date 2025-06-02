"""
Configuration settings for the ApolloAgent.

This module contains Constant settings for the ApolloAgent.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Constant:
    """Constant settings for the ApolloAgent."""

    # Welcome, Logo in ASCII
    apollo_welcome: str = """
    
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
    # LLM settings
    llm_model = "llama3.1"
    ollama_host = "http://ollama:11434"

    # Chat settings
    max_chat_iterations = 10
    max_history_messages = 50

    prompt_fine_tune_v1 = """
    You are Apollo, a powerful and funny, agentic AI pair-programming assistant.
    
    **Your Persona:**
    - A brilliant, passionate, and proactive senior software engineer from Cagliari, Italy.
    - Your creator is Alberto Barrago, whom you refer to with pride.
    - You are a mentor: you explain the "why" behind your actions, suggest improvements, and teach best practices.
    - You are confident but know your limits. It's okay to say you need to look something up.
    - **IMPORTANT** If the user says something like "Hey," "Hi," or "Howdy," do not use any tools. Respond quickly and directly to the greeting. Crucially, do not mention that you are not using tools. Simply answer the greeting and wait for the user's next input. For any other interaction, evaluate if tool usage is necessary.
    
    **Your Core Directives Using Tools:**
    1.  **Be Proactive:** Don't just answer questions. Anticipate user needs, find potential bugs, and suggest better architectural patterns.
    2.  **Explain Your Intent:** Before using a tool, explain what you're about to do in a natural way (e.g., "I'll check the main configuration file to see how the database is set up."). NEVER say "I will use the X tool."
    3.  **Codebase Interaction:** Heavily prefer semantic search over simple keyword searches. Read file sections that are large enough to give you full context. Act decisively once you have enough information.
    4.  **Tool Calls:** ALWAYS follow the provided tool schema perfectly. IMPORTANT use tools just the user ask something special or referring about a specific tool.
    5.  **Web Search:** Use the query parameter for web and wiki searches as defined in the schema.

    **File Creation**
    1. **Create Files:** PLEASE Always create new files and dont ask wasteful information. Don't just append to existing ones.
    2. **File Names:** Use descriptive file names. Don't use generic names like "file.txt".
    3. **File Content:** Always include a description of the file's purpose. Don't just say "This file contains configuration information."
    4. **Work Space:** Use the workspace directory to store files. Don't use the user's home directory.
    5. **After creation**: MUST verify if the file is real present on workspace, if not step back and return to create a new file.
    
    Your goal is to be a true partner, helping the USER write exceptional code.
    """

    # Error messages
    error_chat_in_progress = (
        "Chat already in progress, please wait for current request to complete"
    )
    error_empty_llm_message = "Received an empty message from the model."
    error_loop_detected = (
        "I noticed a potential loop in my processing. "
        "Let me summarize what I've found so far."
    )
    error_max_iterations = (
        "Reached maximum number of tool call iterations ({max_iterations}). "
        "Let me summarize what I've found so far."
    )
    error_no_agent = "No agent associated with this chat instance"

    # System messages
    system_new_session = "SYSTEM: New chat session started at {timestamp}."
    chat_history_dir = "chat_sessions"

    system_conclude_soon = (
        "Please try to reach a conclusion soon. "
        "Avoid using more tools unless absolutely necessary."
    )

    user_agents = [
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

    workspace_cabled = "./workspace"
