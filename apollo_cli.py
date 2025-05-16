import os
import sys
import argparse
import json
from agent import ApolloAgent

def print_result(result):
    """
    Print the result in a formatted JSON way.

    Args:
        result (dict): The result dictionary to be printed

    Returns:
        None
    """
    print(json.dumps(result, indent=2))

def main():
    """
    Command-line interface for ApolloAgent.

    This function parses command-line arguments and executes the corresponding
    ApolloAgent methods based on the provided commands and options. It supports
    various operations such as listing directories, searching code/files/text,
    editing files, and more.

    Returns:
        int: 0 for successful execution, 1 for errors or when help is displayed
    """
    parser = argparse.ArgumentParser(description="ApolloAgent CLI - A terminal interface for code assistance")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List directory command
    list_parser = subparsers.add_parser("list", help="List contents of a directory")
    list_parser.add_argument("path", nargs="?", default=".", help="Path to list contents of, relative to the workspace root")

    # Search commands
    search_parser = subparsers.add_parser("search", help="Search for code, files, or text")
    search_subparsers = search_parser.add_subparsers(dest="search_type", help="Type of search to perform")

    # Code search
    code_search_parser = search_subparsers.add_parser("code", help="Search for code snippets")
    code_search_parser.add_argument("query", help="The search query to find relevant code")
    code_search_parser.add_argument("--dirs", nargs="+", help="Directories to search in")

    # File search
    file_search_parser = search_subparsers.add_parser("file", help="Search for files by name")
    file_search_parser.add_argument("query", help="Fuzzy filename to search for")

    # Grep search
    grep_search_parser = search_subparsers.add_parser("grep", help="Search for text patterns in files")
    grep_search_parser.add_argument("query", help="The regex pattern to search for")
    grep_search_parser.add_argument("--case-sensitive", action="store_true", help="Make the search case sensitive")
    grep_search_parser.add_argument("--include", help="Glob pattern for files to include")
    grep_search_parser.add_argument("--exclude", help="Glob pattern for files to exclude")

    # File operations
    edit_parser = subparsers.add_parser("edit", help="Edit a file")
    edit_parser.add_argument("file", help="The path of the file to edit, relative to the workspace root")
    edit_parser.add_argument("--content", help="The new content for the file (if not provided, will open in default editor)")

    delete_parser = subparsers.add_parser("delete", help="Delete a file")
    delete_parser.add_argument("file", help="The path of the file to delete, relative to the workspace root")

    reapply_parser = subparsers.add_parser("reapply", help="Reapply the last edit to a file")
    reapply_parser.add_argument("file", help="The path of the file to reapply the last edit to")

    # Web search
    web_parser = subparsers.add_parser("web", help="Search the web")
    web_parser.add_argument("query", help="The search term to look up on the web")

    # Diff history
    diff_parser = subparsers.add_parser("diff", help="Show diff history")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Start a chat session with Apollo")
    chat_parser.add_argument("--message", help="Single message to send (non-interactive mode)")
    chat_parser.add_argument("--interactive", action="store_true", help="Start an interactive chat session")
    chat_parser.add_argument("--execute-python", action="store_true", help="Execute Python code in messages and responses")
    chat_parser.add_argument("--api-key", help="Google API key for Gemini (can also use GOOGLE_API_KEY env variable)")
    chat_parser.add_argument("--continuous", action="store_true", help="Run in continuous mode with Python execution")

    # Parse arguments
    args = parser.parse_args()

    # Initialize agent
    api_key = args.api_key if hasattr(args, 'api_key') and args.api_key else None
    agent = ApolloAgent(api_key=api_key)

    # Execute command
    if args.command == "list":
        result = agent.list_dir(args.path)
        print_result(result)

    elif args.command == "search":
        if args.search_type == "code":
            result = agent.codebase_search(args.query, args.dirs)
            print_result(result)
        elif args.search_type == "file":
            result = agent.file_search(args.query)
            print_result(result)
        elif args.search_type == "grep":
            result = agent.grep_search(args.query, args.case_sensitive, args.include, args.exclude)
            print_result(result)
        else:
            print("Error: Please specify a search type (code, file, or grep)")
            search_parser.print_help()
            return 1

    elif args.command == "edit":
        if args.content:
            result = agent.edit_file(args.file, args.content)
            print_result(result)
        else:
            # Open in default editor if no content provided
            import subprocess

            file_path = os.path.join(agent.workspace_path, args.file)

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Create file if it doesn't exist
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    f.write("")

            # Open in default editor
            if sys.platform == 'win32':
                os.startfile(file_path)
            else:
                editor = os.environ.get('EDITOR', 'nano')
                subprocess.call([editor, file_path])

            print(f"File opened in editor: {args.file}")

    elif args.command == "delete":
        result = agent.delete_file(args.file)
        print_result(result)

    elif args.command == "reapply":
        result = agent.reapply(args.file)
        print_result(result)

    elif args.command == "web":
        result = agent.web_search(args.query)
        print_result(result)

    elif args.command == "diff":
        result = agent.diff_history()
        print_result(result)

    elif args.command == "chat":
        execute_python = args.execute_python if hasattr(args, 'execute_python') else False

        if args.message:
            # Single message mode
            result = agent.chat(args.message, execute_python=execute_python)
            print_result(result)
        elif args.interactive or (hasattr(args, 'continuous') and args.continuous):
            # Interactive or continuous chat session
            print("Starting chat session with Apollo. Type 'exit' or 'quit' to end the session.")
            print("Apollo: Hello! I'm Apollo, your AI assistant. How can I help you today?")

            continuous_mode = hasattr(args, 'continuous') and args.continuous
            if continuous_mode:
                print("Running in continuous mode with Python execution enabled.")

            while True:
                try:
                    user_input = input("\nYou: ")
                    if user_input.lower() in ["exit", "quit", "bye"]:
                        print("\nApollo: Goodbye! Have a great day!")
                        break

                    if continuous_mode:
                        # In continuous mode, always execute Python code
                        result = agent.chat(user_input, interactive=True, execute_python=True)
                    else:
                        # In regular interactive mode, use the execute_python flag
                        result = agent.chat(user_input, interactive=True, execute_python=execute_python)

                except KeyboardInterrupt:
                    print("\n\nChat session ended by user.")
                    break
                except Exception as e:
                    print(f"\nError: {str(e)}")
                    print("Continuing session...")
        else:
            # No options provided, show help
            print("Error: Please specify one of: --message, --interactive, or --continuous")
            chat_parser.print_help()
            return 1

    else:
        parser.print_help()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
