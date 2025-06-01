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

Ensure you have Python 3.8+ installed.

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

## License

ApolloAgent is licensed under the BSD 3-Clause License. See the `LICENSE` file for more details.

## Contributing

We welcome contributions to ApolloAgent! If you'd like to help:
- Report bugs or suggest new features via [GitHub Issues](https://github.com/AlbertoBarrago/Apollo-Agent/issues).
- Submit pull requests for enhancements or changes.

## Collaboration Opportunities

ApolloAgent is a proof-of-concept project with many opportunities for improvement and expansion. Here are specific areas where your contributions would be valuable:

### Session Management
- **Chat History Persistence**: Implement more robust storage solutions for chat history (e.g., SQLite, Redis).
- **User Profiles**: Add support for multiple user profiles with personalized settings.
- **Context Retention**: Improve how the agent maintains context across multiple interactions.

### Error Handling
- **Graceful Recovery**: Enhance error recovery mechanisms to prevent session termination on failures.
- **User-Friendly Messages**: Create more informative error messages for end users.
- **Logging System**: Implement a comprehensive logging system for debugging and monitoring.

### New Tools and Capabilities
- **Code Generation**: Add tools for generating boilerplate code or common patterns.
- **Refactoring Assistance**: Implement tools to help with code refactoring tasks.
- **Integration with Development Tools**: Add support for Git operations, linters, or test runners.
- **Language Support**: Extend functionality to support additional programming languages.

### Performance Optimization
- **Caching Mechanisms**: Implement caching for frequently accessed files or search results.
- **Parallel Processing**: Use async/await patterns more extensively for I/O-bound operations.
- **Resource Management**: Improve memory usage for large codebases or long sessions.

### Testing and Documentation
- **Test Coverage**: Increase unit test coverage for core functionality.
- **Integration Tests**: Add integration tests for end-to-end workflows.
- **Documentation**: Improve inline documentation and add more examples to the README.
- **Tutorials**: Create tutorials or examples demonstrating common use cases.

### Getting Started with Contributions

1. **Pick an Area**: Choose one of the areas above that interests you.
2. **Create an Issue**: Describe what you plan to implement or improve.
3. **Fork and Clone**: Fork the repository and clone it locally.
4. **Implement Changes**: Make your changes following the project's coding style.
5. **Add Tests**: Write tests for your new functionality.
6. **Submit a PR**: Create a pull request with a clear description of your changes.

We're particularly interested in contributions that make ApolloAgent more robust, user-friendly, and versatile as a coding assistant.
