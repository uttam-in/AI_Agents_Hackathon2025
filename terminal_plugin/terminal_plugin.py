import json
from typing import Dict, Any, Optional
from semantic_kernel.functions import kernel_function
from terminal_plugin.src.terminal_tools import TerminalTools

class TerminalPlugin:
    """Plugin for executing terminal commands through the web interface"""

    def __init__(self):
        self.terminal_tools = TerminalTools()

    @kernel_function(name="execute_command", description="Executes a terminal command and returns the result")
    def execute_command(self, command: str, timeout: str = "60") -> str:
        """
        Executes a terminal command and returns the result.
        
        Args:
            command: The terminal command to execute
            timeout: Maximum execution time in seconds (default: 60)
            
        Returns:
            A string with the command output or error message
        """
        if not command or not isinstance(command, str):
            return "Error: Please provide a valid command"
        
        # Convert timeout to integer
        try:
            timeout_int = int(timeout)
        except ValueError:
            timeout_int = 60  # Default timeout
        
        # Security check - block potentially harmful operations
        if self._is_potentially_harmful(command):
            return "Error: This command contains potentially harmful operations and has been blocked for security reasons"
        
        # Execute the command
        result = self.terminal_tools.execute_command(command, timeout_int)
        
        # Format the response for the agent
        response = self._format_response(result)
        return response
    
    @kernel_function(name="get_current_directory", description="Gets the current working directory")
    def get_current_directory(self) -> str:
        """
        Gets the current working directory.
        
        Returns:
            A string with the current directory path
        """
        # Get the current directory
        result = self.terminal_tools.get_current_directory()
        
        # Format the response for the agent
        if result["success"]:
            return f"Current directory: {result['current_directory']}"
        else:
            return f"Error: {result['stderr']}"
    
    @kernel_function(name="list_directory", description="Lists the contents of a directory")
    def list_directory(self, path: str = ".") -> str:
        """
        Lists the contents of a directory.
        
        Args:
            path: Path to the directory to list (default: current directory)
            
        Returns:
            A string with the directory contents
        """
        if not path or not isinstance(path, str):
            return "Error: Please provide a valid path"
        
        # List the directory
        result = self.terminal_tools.list_directory(path)
        
        # Format the response for the agent
        if result["success"]:
            return f"Directory listing for {result['path']}:\n{result['stdout']}"
        else:
            return f"Error: {result['stderr']}"

    def _is_potentially_harmful(self, command: str) -> bool:
        """
        Check if a command is potentially harmful or dangerous.
        
        This is a basic implementation and should be expanded for production use.
        """
        # List of dangerous patterns or commands that might indicate harmful operations
        dangerous_patterns = [
            "rm -rf /",
            "rm -rf /*",
            "> /dev/sda",
            "dd if=/dev/zero of=/dev/sda",
            ":(){ :|:& };:",
            "chmod -R 777 /",
            "mkfs",
            "> /etc/passwd",
            "> /etc/shadow"
        ]
        
        # Check if any dangerous pattern is in the command
        for pattern in dangerous_patterns:
            if pattern in command:
                return True
                
        return False
        
    def _format_response(self, result: Dict[str, Any]) -> str:
        """
        Format the command execution result into a readable string response.
        """
        # Start with the command that was executed
        response_parts = [f"Command: {result['command']}"]
        
        # Add execution status
        if result["success"]:
            response_parts.append("Status: Success")
        else:
            response_parts.append(f"Status: Failed (return code: {result['return_code']})")
        
        # Add the standard output
        if result["stdout"]:
            response_parts.append("\nOutput:")
            response_parts.append(result["stdout"])
        else:
            response_parts.append("\nOutput: (no output)")
        
        # Add stderr if it exists
        if result["stderr"]:
            response_parts.append("\nErrors:")
            response_parts.append(result["stderr"])
        
        # Add execution time if available
        if "execution_time" in result:
            response_parts.append(f"\nExecution time: {result['execution_time']:.2f} seconds")
        
        # Join all parts
        return "\n".join(response_parts)