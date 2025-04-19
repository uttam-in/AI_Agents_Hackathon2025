import json
from typing import Dict, Any, Optional
from semantic_kernel.functions import kernel_function
from python_plugin.src.python_tools import PythonTools

class PythonScriptPlugin:
    """Plugin for executing Python scripts and handling their output"""

    def __init__(self):
        self.python_tools = PythonTools()

    @kernel_function(name="run_script", description="Runs a Python script and returns the result")
    def run_script(self, script_content: str, script_args: str = "") -> str:
        """
        Executes a Python script and returns the result.
        
        Args:
            script_content: The Python code to execute
            script_args: Optional command-line arguments to pass to the script
            
        Returns:
            A string with the script output or error message
        """
        if not script_content or not isinstance(script_content, str):
            return "Error: Please provide valid Python code"
        
        # Security check - block potentially harmful operations
        if self._is_potentially_harmful(script_content):
            return "Error: This script contains potentially harmful operations and has been blocked for security reasons"
        
        # Execute the script
        result = self.python_tools.run_script(script_content, script_args)
        
        # Format the response for the agent
        response = self._format_response(result)
        return response
    
    @kernel_function(name="run_script_file", description="Runs a Python script from a file and returns the result")
    def run_script_file(self, file_path: str, script_args: str = "") -> str:
        """
        Executes a Python script from a file and returns the result.
        
        Args:
            file_path: Path to the Python script file
            script_args: Optional command-line arguments to pass to the script
            
        Returns:
            A string with the script output or error message
        """
        if not file_path or not isinstance(file_path, str):
            return "Error: Please provide a valid file path"
        
        # Execute the script file
        result = self.python_tools.run_script_file(file_path, script_args)
        
        # Format the response for the agent
        response = self._format_response(result)
        return response

    def _is_potentially_harmful(self, script_content: str) -> bool:
        """
        Check if a script is potentially harmful or dangerous.
        
        This is a basic implementation and should be expanded for production use.
        """
        # List of dangerous patterns or imports that might indicate harmful operations
        dangerous_patterns = [
            "os.system('rm -rf", 
            "shutil.rmtree('/'", 
            "subprocess.run(['rm', '-rf'",
            "__import__('os').system('rm -rf",
            "exec(\"import os; os.system('rm",
            "open('/etc/passwd', 'w')",
            "open('/etc/shadow', 'w')"
        ]
        
        # Check if any dangerous pattern is in the script
        for pattern in dangerous_patterns:
            if pattern in script_content:
                return True
                
        return False
        
    def _format_response(self, result: Dict[str, Any]) -> str:
        """
        Format the script execution result into a readable string response.
        """
        if not result["success"]:
            return f"Error executing script:\n{result['stderr']}"
        
        # Start with the execution status
        response_parts = ["Script execution completed"]
        
        # Add the parsed data if available
        if result.get("parsed_data"):
            response_parts.append("\nParsed results:")
            response_parts.append(json.dumps(result["parsed_data"], indent=2))
        
        # Add the standard output
        if result["stdout"]:
            response_parts.append("\nStandard output:")
            response_parts.append(result["stdout"])
        else:
            response_parts.append("\nStandard output: (no output)")
        
        # Add stderr if it exists but wasn't considered an error
        if result["stderr"] and result["success"]:
            response_parts.append("\nStandard error:")
            response_parts.append(result["stderr"])
        
        # Add execution time if available
        if "execution_time" in result:
            response_parts.append(f"\nExecution time: {result['execution_time']:.2f} seconds")
        
        # Join all parts
        return "\n".join(response_parts)