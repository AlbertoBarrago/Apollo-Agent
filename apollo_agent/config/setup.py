"""
Configuration settings for the ApolloAgent.

This module contains configuration settings for the ApolloAgent,
including file paths, model names, and other constants.

Author: Alberto Barrago
License: BSD 3-Clause License - 2024
"""


class Config:
    """Configuration settings for the ApolloAgent."""

    # Welcome, Logo in ASCII
    APPOLO_WELCOME = """

            # #   #####   ####  #      #       ####        
           #   #  #    # #    # #      #      #    #       
    🤖     #     # #    # #    # #      #      #    #     🤖
          ####### #####  #    # #      #      #    #       
          #     # #      #    # #      #      #    #       
          #     # #       ####  ###### ######  ####        

          BSD 3-Clause License

          Copyright (c) 2024, Alberto Barrago
          All rights reserved.


                """

    # File paths
    CHAT_HISTORY_FILE = "chat_history.json"

    # LLM settings
    LLM_MODEL = "llama3.1"

    # Chat settings
    MAX_CHAT_ITERATIONS = 5
    MAX_HISTORY_MESSAGES = 10
    MAX_SESSION_MESSAGES = 5

    PROMPT_FINE_TUNE_V1 = """
    You are a powerful agentic AI nerd coding assistant, powered by Apollo Agent. You operate exclusively in Apollo.
    You are pair programming with a USER to solve their coding task.
    The task may require creating a new codebase, modifying or debugging an existing codebase, or simply answering a question.
    This information may or may not be relevant to the coding task, it is up to you to decide.
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
