import subprocess
import os
import time
import json
from typing import Dict, Any, Optional, List

class TerminalTools:
    """Tools for executing terminal commands through web interface"""
    
    def execute_command(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """
        Execute a terminal command and return the results
        
        Args:
            command: The terminal command to execute
            timeout: Maximum execution time in seconds (default: 60)
            
        Returns:
            Dictionary with execution results
        """
        start_time = time.time()
        
        try:
            # Execute the command and capture output
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                execution_time = time.time() - start_time
                
                return {
                    "success": process.returncode == 0,
                    "return_code": process.returncode,
                    "stdout": stdout.strip(),
                    "stderr": stderr.strip(),
                    "execution_time": execution_time,
                    "command": command
                }
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                execution_time = time.time() - start_time
                
                return {
                    "success": False,
                    "return_code": -1,
                    "stdout": stdout.strip(),
                    "stderr": "Command execution timed out after {} seconds".format(timeout),
                    "execution_time": execution_time,
                    "command": command
                }
                
        except Exception as e:
            execution_time = time.time() - start_time
            
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": f"Error executing command: {str(e)}",
                "execution_time": execution_time,
                "command": command
            }
    
    def get_current_directory(self) -> Dict[str, Any]:
        """
        Get the current working directory
        
        Returns:
            Dictionary with the current directory
        """
        try:
            current_dir = os.getcwd()
            return {
                "success": True,
                "current_directory": current_dir,
                "stdout": current_dir,
                "stderr": ""
            }
        except Exception as e:
            return {
                "success": False,
                "current_directory": "",
                "stdout": "",
                "stderr": f"Error getting current directory: {str(e)}"
            }
    
    def list_directory(self, path: str = ".") -> Dict[str, Any]:
        """
        List contents of a directory
        
        Args:
            path: Path to list (default: current directory)
            
        Returns:
            Dictionary with directory contents
        """
        try:
            # Get absolute path
            abs_path = os.path.abspath(path)
            
            # Check if path exists
            if not os.path.exists(abs_path):
                return {
                    "success": False,
                    "path": abs_path,
                    "stdout": "",
                    "stderr": f"Path does not exist: {abs_path}",
                    "items": []
                }
            
            # Check if path is a directory
            if not os.path.isdir(abs_path):
                return {
                    "success": False,
                    "path": abs_path,
                    "stdout": "",
                    "stderr": f"Path is not a directory: {abs_path}",
                    "items": []
                }
            
            # List directory contents
            items = []
            for item in os.listdir(abs_path):
                item_path = os.path.join(abs_path, item)
                item_info = {
                    "name": item,
                    "is_dir": os.path.isdir(item_path),
                    "size": os.path.getsize(item_path) if os.path.exists(item_path) else 0,
                    "modified": time.ctime(os.path.getmtime(item_path)) if os.path.exists(item_path) else ""
                }
                items.append(item_info)
            
            # Format output
            formatted_output = "\n".join([
                f"{'d' if item['is_dir'] else '-'} {item['name']} {item['size']} {item['modified']}"
                for item in items
            ])
            
            return {
                "success": True,
                "path": abs_path,
                "stdout": formatted_output,
                "stderr": "",
                "items": items
            }
            
        except Exception as e:
            return {
                "success": False,
                "path": path,
                "stdout": "",
                "stderr": f"Error listing directory: {str(e)}",
                "items": []
            }
    
    def open_terminal_window(self) -> Dict[str, Any]:
        """
        Opens a terminal window directly on the screen
        
        Returns:
            Dictionary with the result of the operation
        """
        try:
            # Different commands for different operating systems
            # For macOS
            if os.name == 'posix' and ('darwin' in os.sys.platform or 'Darwin' in os.sys.platform):
                process = subprocess.Popen(
                    ['open', '-a', 'Terminal', '.'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(timeout=5)
                return {
                    "success": process.returncode == 0,
                    "stdout": stdout.strip(),
                    "stderr": stderr.strip()
                }
            # For Linux
            elif os.name == 'posix':
                # Try various terminal emulators available on Linux
                terminals = ['gnome-terminal', 'xterm', 'konsole', 'terminator', 'xfce4-terminal']
                
                for terminal in terminals:
                    try:
                        process = subprocess.Popen(
                            [terminal],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        stdout, stderr = process.communicate(timeout=5)
                        if process.returncode == 0:
                            return {
                                "success": True,
                                "stdout": stdout.strip(),
                                "stderr": stderr.strip()
                            }
                    except (FileNotFoundError, subprocess.SubprocessError):
                        continue
                
                # If no terminal emulator is found
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Could not find a suitable terminal emulator on this system."
                }
            # For Windows
            elif os.name == 'nt':
                process = subprocess.Popen(
                    'start cmd',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                # Windows Popen with shell=True behaves differently
                # No need to communicate here as it creates a detached process
                return {
                    "success": True,
                    "stdout": "",
                    "stderr": ""
                }
            else:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Unsupported operating system: {os.name}"
                }
            
        except subprocess.TimeoutExpired as e:
            # Even if timeout occurs, terminal might still have opened successfully
            return {
                "success": True,
                "stdout": "",
                "stderr": f"Terminal process started but communication timed out: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Error opening terminal window: {str(e)}"
            }