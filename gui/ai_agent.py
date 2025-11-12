"""
AI Agent with tool calling capabilities for ChatGPT/OpenAI API.

This module provides an AI agent that can call tools to interact with the file system,
including listing files, reading files, and editing files.
"""

import os
import json
from typing import List, Dict, Optional, Callable, Any
from pathlib import Path

from .context_provider import ContextProvider


class AIAgent:
    """
    AI Agent with tool-calling capabilities adapted for ChatGPT/OpenAI API.

    This agent can use tools to interact with the file system and perform
    tasks autonomously through the OpenAI function calling API.
    """

    def __init__(
        self,
        api_key: Optional[str],
        model: str = "gpt-4o",
        working_dir: Optional[str] = None,
        max_iterations: int = 10
    ):
        """
        Initialize the AI agent.

        Args:
            api_key: OpenAI API key
            model: Model identifier to use (default: gpt-4o for tool calling)
            working_dir: Working directory for file operations (defaults to current directory)
            max_iterations: Maximum number of tool calling iterations (default: 10)
        """
        self.model = model
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.max_iterations = max_iterations
        self.history: List[Dict] = []
        self.client = self._initialize_client(api_key)
        self.tools = self._define_tools()
        self.tool_functions = self._register_tool_functions()
        self.context_provider = ContextProvider(working_dir=str(self.working_dir))
        self._system_message_cache = None

    def _initialize_client(self, api_key: Optional[str]):
        """
        Initialize the OpenAI client.

        Args:
            api_key: OpenAI API key

        Returns:
            OpenAI client instance or None if initialization fails
        """
        if not api_key:
            return None

        try:
            from openai import OpenAI
        except ImportError:
            print("Error: OpenAI library not available")
            return None

        try:
            return OpenAI(api_key=api_key)
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            return None

    def _define_tools(self) -> List[Dict]:
        """
        Define the tools available to the agent in OpenAI function format.

        Returns:
            List of tool definitions
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "List all files and directories in a given folder path. Returns a list of file and directory names.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "folder_path": {
                                "type": "string",
                                "description": "The path to the folder to list files from. Can be relative to the working directory or absolute."
                            }
                        },
                        "required": ["folder_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the contents of a file at the given path. Returns the file contents as a string.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "The path to the file to read. Can be relative to the working directory or absolute."
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Edit a file by replacing old content with new content. Performs a string replacement in the file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "The path to the file to edit. Can be relative to the working directory or absolute."
                            },
                            "old_content": {
                                "type": "string",
                                "description": "The exact content to be replaced in the file."
                            },
                            "new_content": {
                                "type": "string",
                                "description": "The new content to replace the old content with."
                            }
                        },
                        "required": ["file_path", "old_content", "new_content"]
                    }
                }
            }
        ]

    def _register_tool_functions(self) -> Dict[str, Callable]:
        """
        Register the actual Python functions that implement the tools.

        Returns:
            Dictionary mapping tool names to their implementation functions
        """
        return {
            "list_files": self._tool_list_files,
            "read_file": self._tool_read_file,
            "edit_file": self._tool_edit_file
        }

    def _resolve_path(self, path: str) -> Path:
        """
        Resolve a path relative to the working directory.

        Args:
            path: Path string (relative or absolute)

        Returns:
            Resolved Path object
        """
        path_obj = Path(path)
        if not path_obj.is_absolute():
            path_obj = self.working_dir / path_obj
        return path_obj.resolve()

    def _tool_list_files(self, folder_path: str) -> str:
        """
        Implementation of the list_files tool.

        Args:
            folder_path: Path to the folder to list

        Returns:
            JSON string containing the list of files and directories
        """
        try:
            resolved_path = self._resolve_path(folder_path)

            if not resolved_path.exists():
                return json.dumps({
                    "error": f"Folder does not exist: {resolved_path}"
                })

            if not resolved_path.is_dir():
                return json.dumps({
                    "error": f"Path is not a directory: {resolved_path}"
                })

            items = []
            for item in resolved_path.iterdir():
                item_info = {
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "path": str(item.relative_to(self.working_dir)) if item.is_relative_to(self.working_dir) else str(item)
                }
                items.append(item_info)

            # Sort: directories first, then files, alphabetically
            items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))

            return json.dumps({
                "folder": str(resolved_path),
                "items": items,
                "count": len(items)
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Error listing files: {str(e)}"})

    def _tool_read_file(self, file_path: str) -> str:
        """
        Implementation of the read_file tool.

        Args:
            file_path: Path to the file to read

        Returns:
            File contents or error message
        """
        try:
            resolved_path = self._resolve_path(file_path)

            if not resolved_path.exists():
                return json.dumps({
                    "error": f"File does not exist: {resolved_path}"
                })

            if not resolved_path.is_file():
                return json.dumps({
                    "error": f"Path is not a file: {resolved_path}"
                })

            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return json.dumps({
                "file": str(resolved_path),
                "content": content,
                "size_bytes": len(content.encode('utf-8'))
            }, indent=2)

        except UnicodeDecodeError:
            return json.dumps({
                "error": f"Cannot read file (not a text file or encoding issue): {file_path}"
            })
        except Exception as e:
            return json.dumps({"error": f"Error reading file: {str(e)}"})

    def _tool_edit_file(self, file_path: str, old_content: str, new_content: str) -> str:
        """
        Implementation of the edit_file tool.

        Args:
            file_path: Path to the file to edit
            old_content: Content to be replaced
            new_content: New content to insert

        Returns:
            Success message or error
        """
        try:
            resolved_path = self._resolve_path(file_path)

            if not resolved_path.exists():
                return json.dumps({
                    "error": f"File does not exist: {resolved_path}"
                })

            if not resolved_path.is_file():
                return json.dumps({
                    "error": f"Path is not a file: {resolved_path}"
                })

            # Read current content
            with open(resolved_path, 'r', encoding='utf-8') as f:
                current_content = f.read()

            # Check if old_content exists in the file
            if old_content not in current_content:
                return json.dumps({
                    "error": f"Content to replace not found in file",
                    "file": str(resolved_path)
                })

            # Replace content
            updated_content = current_content.replace(old_content, new_content)

            # Write back to file
            with open(resolved_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            return json.dumps({
                "success": True,
                "file": str(resolved_path),
                "message": "File edited successfully"
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Error editing file: {str(e)}"})

    def _execute_tool(self, tool_name: str, tool_arguments: Dict[str, Any]) -> str:
        """
        Execute a tool by name with given arguments.

        Args:
            tool_name: Name of the tool to execute
            tool_arguments: Arguments to pass to the tool

        Returns:
            Tool execution result as string
        """
        if tool_name not in self.tool_functions:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        tool_func = self.tool_functions[tool_name]
        try:
            return tool_func(**tool_arguments)
        except Exception as e:
            return json.dumps({"error": f"Tool execution error: {str(e)}"})

    def process_request(self, user_input: str) -> str:
        """
        Process the user's request through the AI agent (compatible with AIClient interface).

        This method is designed to be compatible with the existing ForShape GUI code
        that expects an AIClient-like interface.

        Args:
            user_input: The user's input string

        Returns:
            AI response string
        """
        if self.client is None:
            return "Error: OpenAI client not initialized. Please check your API key."

        try:
            # Get system message from context provider (only once, then cache it)
            if self._system_message_cache is None:
                system_message, forshape_context = self.context_provider.get_context(include_agent_tools=True)
                self._system_message_cache = system_message
            else:
                system_message = self._system_message_cache
                forshape_context = self.context_provider.load_forshape_context()

            # Augment user input with FORSHAPE.md context if available
            augmented_input = user_input
            if forshape_context:
                augmented_input = f"[User Context from FORSHAPE.md]\n{forshape_context}\n\n[User Request]\n{user_input}"

            # Use the run method with the context
            response = self.run(augmented_input, system_message)
            return response

        except Exception as e:
            error_msg = f"Error processing AI request: {str(e)}"
            return error_msg

    def run(self, user_message: str, system_message: Optional[str] = None) -> str:
        """
        Run the agent with a user message. The agent will autonomously call tools as needed.

        Args:
            user_message: The user's message/request
            system_message: Optional system message to set context

        Returns:
            Final response from the agent
        """
        if self.client is None:
            return "Error: OpenAI client not initialized. Please check your API key."

        # Initialize messages
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})

        # Add conversation history
        messages.extend(self.history)

        # Add user message
        messages.append({"role": "user", "content": user_message})

        # Agent loop: keep calling tools until the agent gives a final response
        for iteration in range(self.max_iterations):
            try:
                # Call OpenAI API with tools
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto"
                )

                response_message = response.choices[0].message

                # Check if the agent wants to call tools
                if response_message.tool_calls:
                    # Add the assistant's response to messages
                    messages.append(response_message)

                    # Process each tool call
                    for tool_call in response_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)

                        # Execute the tool
                        tool_result = self._execute_tool(tool_name, tool_args)

                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": tool_result
                        })

                    # Continue the loop to get the next response
                    continue

                # No tool calls, we have a final response
                final_response = response_message.content

                # Update history
                self.history.append({"role": "user", "content": user_message})
                self.history.append({"role": "assistant", "content": final_response})

                return final_response

            except Exception as e:
                return f"Error during agent execution: {str(e)}"

        # If we hit max iterations
        return "Agent reached maximum iterations without completing the task."

    def get_history(self) -> List[Dict]:
        """
        Get the conversation history.

        Returns:
            List of message dictionaries
        """
        return self.history

    def clear_history(self):
        """Clear the conversation history."""
        self.history = []

    def is_available(self) -> bool:
        """
        Check if the AI agent is available and ready.

        Returns:
            True if client is initialized, False otherwise
        """
        return self.client is not None

    def get_working_dir(self) -> str:
        """
        Get the current working directory for file operations.

        Returns:
            Working directory path as string
        """
        return str(self.working_dir)

    def get_model(self) -> str:
        """
        Get the model identifier being used.

        Returns:
            Model identifier string
        """
        return self.model
