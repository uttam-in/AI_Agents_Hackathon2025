import subprocess
import tempfile
import os
import time
import json
from typing import Dict, Any, Optional, List

class PythonTools:
    """Tools for executing Python scripts"""
    
    def run_script(self, script_content: str, script_args: str = "") -> Dict[str, Any]:
        """
        Run Python code from a string
        
        Args:
            script_content: The Python code to execute
            script_args: Optional arguments to pass to the script
            
        Returns:
            Dictionary with execution results
        """
        # Create a temporary file to hold the script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(script_content)
            temp_file_path = temp_file.name
        
        try:
            # Run the script with the specified arguments
            start_time = time.time()
            result = self._execute_python_file(temp_file_path, script_args)
            execution_time = time.time() - start_time
            result['execution_time'] = execution_time
            
            # Try to parse the output as JSON if possible
            if result['success'] and result['stdout']:
                try:
                    parsed_data = json.loads(result['stdout'])
                    result['parsed_data'] = parsed_data
                except json.JSONDecodeError:
                    result['parsed_data'] = None
            else:
                result['parsed_data'] = None
                
            return result
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def run_script_file(self, file_path: str, script_args: str = "") -> Dict[str, Any]:
        """
        Run Python code from a file
        
        Args:
            file_path: Path to the Python script file
            script_args: Optional arguments to pass to the script
            
        Returns:
            Dictionary with execution results
        """
        if not os.path.exists(file_path):
            return {
                "success": False,
                "stdout": "",
                "stderr": f"File not found: {file_path}",
                "parsed_data": None
            }
        
        # Run the script with the specified arguments
        start_time = time.time()
        result = self._execute_python_file(file_path, script_args)
        execution_time = time.time() - start_time
        result['execution_time'] = execution_time
        
        # Try to parse the output as JSON if possible
        if result['success'] and result['stdout']:
            try:
                parsed_data = json.loads(result['stdout'])
                result['parsed_data'] = parsed_data
            except json.JSONDecodeError:
                result['parsed_data'] = None
        else:
            result['parsed_data'] = None
            
        return result
    
    def _execute_python_file(self, file_path: str, args: str = "") -> Dict[str, Any]:
        """
        Execute a Python file with the given arguments
        
        Args:
            file_path: Path to the Python file
            args: Command-line arguments for the script
            
        Returns:
            Dictionary with stdout, stderr, and success flag
        """
        cmd = ["python3", file_path]
        
        # Add arguments if provided
        if args:
            cmd.extend(args.split())
        
        try:
            # Run the command and capture output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            # Check if execution was successful
            success = process.returncode == 0
            
            return {
                "success": success,
                "stdout": stdout.strip(),
                "stderr": stderr.strip()
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Error executing Python script: {str(e)}"
            }
            
    def list_available_packages(self) -> Dict[str, Any]:
        """
        List all installed Python packages
        
        Returns:
            Dictionary with the list of installed packages
        """
        try:
            process = subprocess.Popen(
                ["pip", "list", "--format=json"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            # Check if execution was successful
            success = process.returncode == 0
            
            if success:
                try:
                    packages = json.loads(stdout)
                    return {
                        "success": True,
                        "stdout": stdout,
                        "stderr": stderr,
                        "parsed_data": {"packages": packages}
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "stdout": stdout,
                        "stderr": stderr,
                        "parsed_data": None
                    }
            else:
                return {
                    "success": False,
                    "stdout": stdout,
                    "stderr": stderr,
                    "parsed_data": None
                }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Error listing packages: {str(e)}",
                "parsed_data": None
            }