import json
import os
import time
import shlex
import subprocess
import pty
import select
import fcntl
import termios
import struct
from typing import Dict, Any, Optional, List, Tuple

class TerminalSession:
    """Maintains state for a terminal session"""
    
    def __init__(self, session_id: str, working_dir: str = None):
        self.session_id = session_id
        self.working_dir = working_dir or os.getcwd()
        self.env = os.environ.copy()
        self.history = []
        self.fd = None
        self.process = None
        self.interactive = False
    
    def is_alive(self) -> bool:
        """Check if the terminal process is still alive"""
        if self.process is None:
            return False
        return self.process.poll() is None
        
    def cleanup(self):
        """Clean up resources"""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
            except:
                pass


class TerminalTools:
    """Tools for executing terminal commands through web interface"""
    
    def __init__(self):
        self.sessions = {}  # Dictionary to store active terminal sessions
    
    def _get_or_create_session(self, session_id: str = None) -> TerminalSession:
        """Get an existing session or create a new one"""
        if not session_id:
            session_id = str(time.time())
            
        if session_id not in self.sessions:
            self.sessions[session_id] = TerminalSession(session_id)
        
        return self.sessions[session_id]
    
    def execute_command(self, command: str, timeout: int = 60, session_id: str = None) -> Dict[str, Any]:
        """
        Execute a terminal command and return the results
        
        Args:
            command: The terminal command to execute
            timeout: Maximum execution time in seconds (default: 60)
            session_id: Optional session ID to maintain state
            
        Returns:
            Dictionary with execution results
        """
        # Get or create a terminal session
        session = self._get_or_create_session(session_id)
        
        # Add command to history
        session.history.append(command)
        
        # Handle cd commands specially to track directory changes
        if command.strip().startswith('cd '):
            return self._handle_cd_command(command, session)
        
        # Handle environment variable assignment (VAR=value)
        if '=' in command and not command.startswith(('echo ', 'export ')):
            parts = command.split('=', 1)
            if len(parts) == 2 and ' ' not in parts[0]:
                var_name = parts[0].strip()
                var_value = parts[1].strip()
                # Remove quotes if present
                if (var_value.startswith('"') and var_value.endswith('"')) or \
                   (var_value.startswith("'") and var_value.endswith("'")):
                    var_value = var_value[1:-1]
                session.env[var_name] = var_value
                return {
                    "success": True,
                    "return_code": 0,
                    "stdout": f"Set {var_name}={var_value}",
                    "stderr": "",
                    "execution_time": 0,
                    "command": command,
                    "working_dir": session.working_dir
                }
        
        # Check for interactive commands that need PTY
        interactive_commands = ['vim', 'nano', 'less', 'more', 'top', 'htop', 'ssh', 'mysql', 'psql']
        is_interactive = any(command.strip().startswith(cmd) for cmd in interactive_commands)
        
        start_time = time.time()
        
        try:
            if is_interactive:
                # For interactive commands, use a simpler approach and warn the user
                return {
                    "success": True,
                    "return_code": 0,
                    "stdout": "Interactive command detected. Browser terminals cannot fully support interactive programs like editors and pagers. Try a simpler command or use a real terminal.",
                    "stderr": "",
                    "execution_time": 0,
                    "command": command,
                    "working_dir": session.working_dir
                }
            else:
                # Execute the command and capture output
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                    text=True,
                    cwd=session.working_dir,
                    env=session.env
                )
                
                try:
                    stdout, stderr = process.communicate(timeout=timeout)
                    execution_time = time.time() - start_time
                    
                    # Update environment variables if command contains exports
                    if 'export ' in command:
                        # Try to extract exported variables
                        self._update_env_from_export(command, session)
                    
                    # Check if the command might have changed the directory indirectly
                    if 'pwd' in command or '$(pwd)' in command or '`pwd`' in command:
                        # Refresh working directory
                        pwd_process = subprocess.run(
                            "pwd",
                            shell=True,
                            capture_output=True,
                            text=True,
                            cwd=session.working_dir
                        )
                        if pwd_process.returncode == 0:
                            session.working_dir = pwd_process.stdout.strip()
                    
                    return {
                        "success": process.returncode == 0,
                        "return_code": process.returncode,
                        "stdout": stdout.strip(),
                        "stderr": stderr.strip(),
                        "execution_time": execution_time,
                        "command": command,
                        "working_dir": session.working_dir
                    }
                except subprocess.TimeoutExpired:
                    process.kill()
                    stdout, stderr = process.communicate()
                    execution_time = time.time() - start_time
                    
                    return {
                        "success": False,
                        "return_code": -1,
                        "stdout": stdout.strip(),
                        "stderr": f"Command execution timed out after {timeout} seconds",
                        "execution_time": execution_time,
                        "command": command,
                        "working_dir": session.working_dir
                    }
                    
        except Exception as e:
            execution_time = time.time() - start_time
            
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": f"Error executing command: {str(e)}",
                "execution_time": execution_time,
                "command": command,
                "working_dir": session.working_dir
            }
    
    def _handle_cd_command(self, command: str, session: TerminalSession) -> Dict[str, Any]:
        """Handle cd command to track directory changes"""
        # Extract the target directory from the cd command
        parts = command.strip().split(' ', 1)
        if len(parts) == 1:
            # Just 'cd' without arguments - go to home directory
            target_dir = os.path.expanduser("~")
        else:
            target_dir = parts[1].strip()
            # Handle quoted paths
            if (target_dir.startswith('"') and target_dir.endswith('"')) or \
               (target_dir.startswith("'") and target_dir.endswith("'")):
                target_dir = target_dir[1:-1]
        
        # Handle special paths
        if target_dir == "-":
            # cd - (go to previous directory)
            # This is a simplification - real shells track OLDPWD
            return {
                "success": False,
                "return_code": 1,
                "stdout": "",
                "stderr": "OLDPWD not set",
                "execution_time": 0,
                "command": command,
                "working_dir": session.working_dir
            }
        
        # Resolve the absolute path
        if target_dir.startswith('/'):
            # Absolute path
            new_dir = target_dir
        else:
            # Relative path
            new_dir = os.path.join(session.working_dir, target_dir)
        
        # Normalize the path
        new_dir = os.path.normpath(new_dir)
        
        # Check if the directory exists
        if os.path.exists(new_dir) and os.path.isdir(new_dir):
            old_dir = session.working_dir
            session.working_dir = new_dir
            return {
                "success": True,
                "return_code": 0,
                "stdout": "",
                "stderr": "",
                "execution_time": 0,
                "command": command,
                "working_dir": new_dir
            }
        else:
            return {
                "success": False,
                "return_code": 1,
                "stdout": "",
                "stderr": f"cd: no such directory: {target_dir}",
                "execution_time": 0,
                "command": command,
                "working_dir": session.working_dir
            }
    
    def _update_env_from_export(self, command: str, session: TerminalSession) -> None:
        """Update environment variables from export command"""
        # Extract the export part of the command
        export_part = command[command.find('export')+6:].strip()
        
        # Handle multiple exports in one command (export VAR1=val1 VAR2=val2)
        export_parts = export_part.split()
        
        for part in export_parts:
            if '=' in part:
                var_name, var_value = part.split('=', 1)
                # Remove quotes if present
                if (var_value.startswith('"') and var_value.endswith('"')) or \
                   (var_value.startswith("'") and var_value.endswith("'")):
                    var_value = var_value[1:-1]
                session.env[var_name] = var_value
    
    def get_current_directory(self, session_id: str = None) -> Dict[str, Any]:
        """
        Get the current working directory for a session
        
        Args:
            session_id: Optional session ID
            
        Returns:
            Dictionary with the current directory
        """
        session = self._get_or_create_session(session_id)
        
        return {
            "success": True,
            "current_directory": session.working_dir,
            "stdout": session.working_dir,
            "stderr": ""
        }
    
    def list_directory(self, path: str = ".", session_id: str = None) -> Dict[str, Any]:
        """
        List contents of a directory
        
        Args:
            path: Path to list (default: current directory)
            session_id: Optional session ID
            
        Returns:
            Dictionary with directory contents
        """
        session = self._get_or_create_session(session_id)
        
        try:
            # Handle relative path based on session's working directory
            if path == ".":
                abs_path = session.working_dir
            elif path.startswith('/'):
                abs_path = path
            else:
                abs_path = os.path.join(session.working_dir, path)
                
            # Normalize path
            abs_path = os.path.normpath(abs_path)
            
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
            
            # Format output to look like ls -la
            formatted_output = []
            for item in items:
                file_type = 'd' if item['is_dir'] else '-'
                permissions = 'rwxr-xr-x' if item['is_dir'] else 'rw-r--r--'
                size_str = str(item['size']).rjust(8)
                name_str = item['name'] + ('/' if item['is_dir'] else '')
                formatted_output.append(f"{file_type}{permissions} {size_str} {item['modified']} {name_str}")
            
            return {
                "success": True,
                "path": abs_path,
                "stdout": "\n".join(formatted_output),
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
    
    def open_terminal_window(self, session_id: str = None) -> Dict[str, Any]:
        """
        Opens a terminal window directly on the screen
        
        Args:
            session_id: Optional session ID
            
        Returns:
            Dictionary with the result of the operation
        """
        session = self._get_or_create_session(session_id)
        
        try:
            # Different commands for different operating systems
            # For macOS
            if os.name == 'posix' and ('darwin' in os.sys.platform or 'Darwin' in os.sys.platform):
                process = subprocess.Popen(
                    ['open', '-a', 'Terminal', session.working_dir],
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
                            [terminal, '--working-directory', session.working_dir],
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
                # Use start command with the working directory
                cmd = f'start cmd /K "cd /d {session.working_dir}"'
                process = subprocess.Popen(
                    cmd,
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

    def get_command_history(self, session_id: str = None) -> Dict[str, Any]:
        """
        Get command history for a session
        
        Args:
            session_id: Optional session ID
            
        Returns:
            Dictionary with command history
        """
        session = self._get_or_create_session(session_id)
        
        return {
            "success": True,
            "history": session.history,
            "stdout": "\n".join(session.history),
            "stderr": ""
        }
            
    def get_environment_variables(self, session_id: str = None) -> Dict[str, Any]:
        """
        Get environment variables for a session
        
        Args:
            session_id: Optional session ID
            
        Returns:
            Dictionary with environment variables
        """
        session = self._get_or_create_session(session_id)
        
        # Format output like env command
        formatted_output = "\n".join([f"{key}={value}" for key, value in session.env.items()])
        
        return {
            "success": True,
            "environment": session.env,
            "stdout": formatted_output,
            "stderr": ""
        }