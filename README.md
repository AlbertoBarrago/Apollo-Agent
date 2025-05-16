# ApolloAgent

ApolloAgent is a custom AI agent that implements various functions for code assistance. This agent is inspired by the Claude 3.7 Sonnet agent for Cursor IDE.

## Features

ApolloAgent provides the following functionality:

- **Codebase Search**: Find snippets of code from the codebase most relevant to a search query
- **Directory Listing**: List the contents of a directory
- **Grep Search**: Fast text-based regex search that finds exact pattern matches within files or directories
- **File Search**: Fast file search based on fuzzy matching against a file path
- **File Operations**: Delete and edit files
- **Reapply Edits**: Reapply the last edit to a specified file
- **Web Search**: Search the web for real-time information (placeholder implementation)
- **Diff History**: Retrieve the history of recent changes made to files (placeholder implementation)
- **Chat Interface**: Interact with Apollo conversationally, powered by Google's Gemini Flash AI
- **Python Execution**: Run Python code directly within chat conversations
- **Continuous Mode**: Chat and execute Python code in a seamless, continuous session

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ApolloAgent.git

# Navigate to the project directory
cd ApolloAgent

# Install dependencies (if any)
pip install -r requirements.txt  # Create this file if you have dependencies
```

## Architecture
```
+---------------------+     +-------------------------+     +--------------------------+     +-----------------------+
| Utente (Linguaggio  | --> | ApolloAgent (Orchestra. | --> | HuggingFaceTools         | --> | HuggingFace CodeAgent |
| Naturale)           |     | di Tool Personalizzati) |     | (Ponte per CodeAgent)    |     | (Cervello dell'Agente)|
+---------------------+     +-------------------------+     +--------------------------+     +-----------------------+
                                       ^                         |                                         ^
                                       |                         |                                         |
                                       |      +---------------------+                                      |
                                       +-----| get_available_tools()|                                      |
                                              +---------------------+                                      |
                                                                   |                                       |
                                                                   v                                       |
                                                                   |     +---------------------+           |
                                                                   +-----| Tool (Oggetti che   | <---------+
                                                                         | incapsulano le tue  |
                                                                         | funzioni)           |
                                                                         +---------------------+
```
