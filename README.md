# ApolloAgent
[![codecov](https://codecov.io/gh/AlbertoBarrago/ApolloAgent/graph/badge.svg?token=SD0LGLSUY6)](https://codecov.io/gh/AlbertoBarrago/ApolloAgent)
[![Black Code Formatter](https://github.com/AlbertoBarrago/ApolloAgent/actions/workflows/black.yml/badge.svg)](https://github.com/AlbertoBarrago/ApolloAgent/actions/workflows/black.yml)

![img.png](screen.png)

ApolloAgent is a custom AI agent that implements various functions for code assistance.

> "_ApolloAgent is a versatile PoC showcasing how AI-driven tools can simplify coding tasks and enhance productivity._"

ApolloAgent provides the following functionality:

- **Web Search**: Get info from duck duck.
- **Wiki Search**: Get info from Wikipedia.
- **Grep Search**: Perform fast, text-based regex searches within files or directories.
- **File Search**: Locate files quickly using fuzzy matching on file paths.
- **File Operations**: Delete and edit files directly through the agent.
- **Session**: Each session is stored in a separate file inside the chat_sessions folder 

## Installation

Ensure you have Python 3.10+ installed.

```bash
# Clone the repository
git clone https://github.com/albertobarrago/ApolloAgent.git

# Navigate to the project directory
cd ApolloAgent

# Install dependencies
pip install -r requirements.txt
```

If no `requirements.txt` is included, install dependencies manually as needed.

## Usage

To start ApolloAgent, simply run:

```bash
python main.py
```

You can:
- Search for a file: `search {file_name}`
- Search on web: `Search on web {query}`
- Search on wiki: `Search on wiki {argument}`
- Create a New file: `Create a new file called {file_name} with this content: {content}`

### Docker (docker-compose)
**Pull the LLM model into Ollama**:
    Ensure the required LLM model (e.g., `llama3.1`) is available in your Ollama container before running ApolloAgent.
    * First, start just the Ollama service:
        ```bash
        docker compose up -d ollama
        ```
    * Then, execute the pull command inside the running Ollama container:
        ```bash
        docker exec -it ollama ollama pull llama3.1
        ```
    * Wait for the download to complete.

1. **Start all services**:
    From your project root (where `docker-compose.yml` is located), run:
    ```bash
    docker compose up -d
    ```
    This command builds your `apolloagent` image, creates the Docker network, and starts both Ollama and ApolloAgent in detached mode.

2. **Interact with ApolloAgent**:
    To access the interactive chat terminal of ApolloAgent:
    ```bash
    docker attach apollo-agent
    ```
    You can detach from the terminal by pressing `Ctrl+C`.

3. **Stop and Clean Up**:
    To stop and remove all services defined in your `docker-compose.yml` file:
    ```bash
    docker compose down
    ```
   
## Tool: `codebase_search`

The `codebase_search` tool is designed to help you find relevant code snippets within the project's codebase based on a natural language query. It's particularly useful when you're looking for code related to a specific concept or functionality but don't know the exact file names or precise syntax.

### How it Works

Internally, `codebase_search` takes your natural language query and processes it to extract significant keywords. It then searches through the files in the workspace (respecting specified `included_extensions` like `.py`, `.js`, `.md`, etc.) to find files that contain **all** of these extracted keywords. This approach aims to provide more relevant results than a simple substring match of the entire query.

### When to Use

Use `codebase_search` when:

*   You want to understand how a particular feature is implemented.
*   You're looking for code related to a general concept (e.g., "error handling," "user authentication").
*   You remember what a piece of code does but not where it is or its exact variable/function names.

### Parameters

When the ApolloAgent decides to use this tool, it will invoke it with the following parameter:

*   `query` (string): Your natural language search query. For example:
    *   `"how are database connections managed"`
    *   `"find the main configuration settings"`
    *   `"show me code related to payment processing"`

### Return Value

The `codebase_search` tool returns a JSON object. This object will always contain `query`, `results`, and `error` keys.

*   `query` (string): The original natural language query you provided.
*   `results` (array of objects): A list of found items.
    *   If matches are found, each object in the array represents a distinct match and includes the following fields:
        *   `file_path` (string): The path to the file where the keywords were found, relative to the workspace root.
        *   `content_snippet` (string): A preview of the file's content (up to the first 500 characters).
        *   `relevance_score` (number): A score indicating the relevance. (Note: This is currently a fixed value for keyword matches but is designed for future semantic enhancements).
    *   If no matches are found (but no error occurred), this will be an empty list (`[]`).
*   `error` (string | null):
    *   If the search operation encounters an issue (e.g., an invalid workspace path, permission errors), this field will contain a descriptive error message (string). In such cases, the `results` list will typically be empty.
    *   If the search completes successfully (even if no items are found), this field will be `null`.

**Example JSON Response (Success with results):**
## License

ApolloAgent is licensed under the BSD 3-Clause License. See the `LICENSE` file for more details.

## Contributing

We welcome contributions to ApolloAgent! If you'd like to help:
- Report bugs or suggest new features via [GitHub Issues](https://github.com/AlbertoBarrago/Apollo-Agent/issues).
- Submit pull requests for enhancements or changes.

### Getting Started with Contributions

1. **Pick an Area**: Choose one of the areas above that interests you.
2. **Create an Issue**: Describe what you plan to implement or improve.
3. **Fork and Clone**: Fork the repository and clone it locally.
4. **Implement Changes**: Make your changes following the project's coding style.
5. **Add Tests**: Write tests for your new functionality.
6. **Submit a PR**: Create a pull request with a clear description of your changes.

We're particularly interested in contributions that make ApolloAgent more robust, user-friendly, and versatile as a coding assistant.
