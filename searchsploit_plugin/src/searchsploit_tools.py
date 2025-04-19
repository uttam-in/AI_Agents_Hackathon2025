import subprocess
import os
import re
from typing import List, Dict, Any, Optional

class SearchSploitTools:
    """Core functionality for SearchSploit tools interaction"""
    
    def __init__(self, searchsploit_path: str = "/usr/bin/searchsploit"):
        """
        Initialize SearchSploit tools.
        
        Args:
            searchsploit_path: Path to the searchsploit executable
        """
        self.searchsploit_path = self._validate_searchsploit_path(searchsploit_path)
        self.last_command_output = ""
        
    def _validate_searchsploit_path(self, searchsploit_path: str) -> str:
        """
        Validates and corrects the SearchSploit path if needed.
        
        Args:
            searchsploit_path: The provided path to SearchSploit
            
        Returns:
            Valid path to SearchSploit
        """
        # First, try to use the provided path
        if searchsploit_path and os.path.exists(searchsploit_path):
            return searchsploit_path
            
        # Try to detect the SearchSploit path
        try:
            # Try to get the location of searchsploit
            result = subprocess.run(["which", "searchsploit"], 
                                   capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except:
            # If any error occurs during detection, fall back to the default path
            pass
            
        # Fall back to default path if detection fails
        return "/usr/bin/searchsploit"
    
    def _run_searchsploit_command(self, args: List[str], timeout: int = 30) -> str:
        """
        Executes searchsploit command with provided arguments.
        
        Args:
            args: Arguments to pass to searchsploit
            timeout: Command execution timeout in seconds
            
        Returns:
            Command output
        """
        try:
            cmd = [self.searchsploit_path] + args
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                self.last_command_output = result.stdout.strip()
                return result.stdout.strip()
            else:
                return f"Error executing SearchSploit command: {result.stderr}"
            
        except Exception as e:
            return f"Error executing SearchSploit command: {str(e)}"
    
    def search_exploits(self, query: str, platform: str = "", type: str = "") -> str:
        """
        Searches for exploits matching the given criteria.
        
        Args:
            query: Search term (e.g., 'apache', 'windows', 'CVE-2021')
            platform: Filter results by platform (e.g., 'windows', 'linux', 'php')
            type: Filter results by exploit type (e.g., 'local', 'remote', 'dos')
            
        Returns:
            List of matching exploits
        """
        if not query or len(query) < 2:
            return "Error: Search query must be at least 2 characters long."
        
        try:
            # Escape query to prevent command injection
            safe_query = query.replace("'", "").replace('"', "").replace(";", "")
            
            # Build the command arguments
            args = [safe_query]
            
            # Apply filters if provided
            if platform:
                args.extend(["-p", platform])
            if type:
                args.extend(["-t", type])
                
            # Add formatting option for clean output
            args.append("--colour")
            
            # Execute the search
            output = self._run_searchsploit_command(args)
            
            if "Exploit Title" not in output:
                return f"No exploits found matching '{query}'."
            
            return f"SearchSploit results for '{query}':\n{output}"
        
        except Exception as e:
            return f"Error searching exploits: {str(e)}"
    
    def get_exploit_details(self, exploit_id: str) -> str:
        """
        Gets detailed information about a specific exploit.
        
        Args:
            exploit_id: The exploit ID or path
            
        Returns:
            Detailed exploit information
        """
        try:
            # Validate input to be a number or a path
            if not exploit_id.isdigit() and not "/" in exploit_id:
                return "Error: Exploit ID must be a number or a valid path."
            
            # Build the command
            args = ["-x", exploit_id]
            
            # Execute the command to get the exploit details
            output = self._run_searchsploit_command(args)
            
            if "No results from search" in output or "is not a valid" in output:
                return f"No details found for exploit ID '{exploit_id}'."
            
            return f"Exploit details for '{exploit_id}':\n{output}"
        
        except Exception as e:
            return f"Error getting exploit details: {str(e)}"
    
    def update_database(self) -> str:
        """
        Updates the SearchSploit database.
        
        Returns:
            Update result message
        """
        try:
            # Execute the command to update the database
            output = self._run_searchsploit_command(["-u"], timeout=120)
            
            if "Already up-to-date" in output:
                return "SearchSploit database is already up-to-date."
            elif "Database updated" in output:
                return "SearchSploit database has been successfully updated."
            else:
                return f"SearchSploit database update result: {output}"
        
        except Exception as e:
            return f"Error updating SearchSploit database: {str(e)}"
    
    def list_platforms(self) -> str:
        """
        Lists available platforms in the SearchSploit database.
        
        Returns:
            List of available platforms
        """
        try:
            # Use the --help command to extract platform information
            output = self._run_searchsploit_command(["--help"])
            
            # Extract platform information from help text
            platform_section = ""
            platforms = []
            in_platform_section = False
            
            for line in output.splitlines():
                if "--platform" in line:
                    in_platform_section = True
                    platform_section = line
                elif in_platform_section and line.strip() and not line.startswith("-"):
                    if "Example" in line or "Usage" in line:
                        in_platform_section = False
                        break
                    platforms.append(line.strip())
            
            if not platforms:
                # If extraction failed, return a default list of common platforms
                platforms = ["windows", "linux", "macos", "android", "ios", "hardware", 
                           "webapps", "jsp", "asp", "php", "jsp", "coldfusion"]
                return "Available platforms in SearchSploit:\n" + "\n".join(platforms)
            
            return "Available platforms in SearchSploit:\n" + "\n".join(platforms)
        
        except Exception as e:
            return f"Error listing platforms: {str(e)}"
    
    def download_exploit(self, exploit_id: str, output_path: str = "./") -> str:
        """
        Downloads an exploit to the specified path.
        
        Args:
            exploit_id: The exploit ID or path
            output_path: Directory to save the exploit
            
        Returns:
            Download result message
        """
        try:
            # Validate input to be a number or a path
            if not exploit_id.isdigit() and not "/" in exploit_id:
                return "Error: Exploit ID must be a number or a valid path."
            
            # Validate output path
            if not os.path.isdir(output_path):
                return f"Error: Output path '{output_path}' is not a valid directory."
            
            # Build the command
            args = ["-m", exploit_id]
            
            # Change to the output directory and execute the command
            current_dir = os.getcwd()
            os.chdir(output_path)
            
            output = self._run_searchsploit_command(args)
            
            # Change back to the original directory
            os.chdir(current_dir)
            
            if "Copied to:" in output:
                return f"Exploit successfully downloaded to {output_path}"
            else:
                return f"Download result: {output}"
        
        except Exception as e:
            # Make sure to change back to the original directory in case of error
            try:
                os.chdir(current_dir)
            except:
                pass
                
            return f"Error downloading exploit: {str(e)}"