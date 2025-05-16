import os
import json
from agent import ApolloAgent

def main():
    """
    Test the ApolloAgent functionality with examples.

    This function initializes an ApolloAgent instance and systematically tests all
    its methods with example inputs. It demonstrates how to use each method and
    prints the results. The tests include:
    1. Listing directory contents
    2. Creating and editing a file
    3. Searching for files
    4. Searching the codebase
    5. Performing grep searches
    6. Reapplying edits
    7. Web search (placeholder)
    8. Diff history (placeholder)
    9. Deleting files

    Returns:
        None
    """
    print("Testing ApolloAgent functionality...")

    # Initialize the agent
    agent = ApolloAgent()
    print(f"Agent initialized with workspace path: {agent.workspace_path}")

    # Test list_dir
    print("\n1. Testing list_dir:")
    result = agent.list_dir(".")
    print("Directory contents:", json.dumps(result, indent=2))

    # Test edit_file
    print("\n2. Testing edit_file:")
    test_content = "This is a test file created by ApolloAgent.\nIt demonstrates the file editing capability."
    edit_result = agent.edit_file("test_file.txt", test_content)
    print("Edit result:", json.dumps(edit_result, indent=2))

    # Test file_search
    print("\n3. Testing file_search:")
    search_result = agent.file_search("test")
    print("File search results:", json.dumps(search_result, indent=2))

    # Test codebase_search
    print("\n4. Testing codebase_search:")
    code_results = agent.codebase_search("ApolloAgent")
    print("Code search results:", json.dumps(code_results, indent=2))

    # Test grep_search
    print("\n5. Testing grep_search:")
    grep_results = agent.grep_search("import", include_pattern="*.py")
    print("Grep search results:", json.dumps(grep_results, indent=2))

    # Test reapply
    print("\n6. Testing reapply:")
    reapply_result = agent.reapply("test_file.txt")
    print("Reapply result:", json.dumps(reapply_result, indent=2))

    # Test web_search (placeholder)
    print("\n7. Testing web_search (placeholder):")
    web_result = agent.web_search("Python programming")
    print("Web search result:", json.dumps(web_result, indent=2))

    # Test diff_history (placeholder)
    print("\n8. Testing diff_history (placeholder):")
    diff_result = agent.diff_history()
    print("Diff history result:", json.dumps(diff_result, indent=2))

    # Test chat functionality
    print("\n9. Testing chat functionality:")
    chat_result = agent.chat("Hello, Apollo!")
    print("Chat result:", json.dumps(chat_result, indent=2))

    chat_result = agent.chat("What can you do?")
    print("Chat result:", json.dumps(chat_result, indent=2))

    chat_result = agent.chat("Can you help me with some code?")
    print("Chat result:", json.dumps(chat_result, indent=2))

    # Clean up test file
    print("\n10. Testing delete_file:")
    if os.path.exists("test_file.txt"):
        delete_result = agent.delete_file("test_file.txt")
        print("Delete result:", json.dumps(delete_result, indent=2))
    else:
        print("Test file doesn't exist, skipping deletion.")

    print("\nAll tests completed!")

if __name__ == "__main__":
    main()
