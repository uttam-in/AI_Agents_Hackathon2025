import os
import sys
from typing import List, Dict, Any

# Add the parent directory to path so we can import the searchsploit_tools module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from searchsploit_plugin.src.searchsploit_tools import SearchSploitTools

from semantic_kernel.functions import kernel_function

class SearchSploitPlugin:
    """Semantic Kernel plugin for SearchSploit security tools"""
    
    def __init__(self, searchsploit_path: str = "/usr/bin/searchsploit"):
        """
        Initialize the SearchSploit Plugin.
        
        Args:
            searchsploit_path: Path to the searchsploit executable
        """
        self.tools = SearchSploitTools(searchsploit_path)
    
    @kernel_function(name="search_exploits", description="Searches for exploits using SearchSploit")
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
        return self.tools.search_exploits(query, platform, type)
    
    @kernel_function(name="get_exploit_details", description="Gets detailed information about a specific exploit")
    def get_exploit_details(self, exploit_id: str) -> str:
        """
        Gets detailed information about a specific exploit.
        
        Args:
            exploit_id: The exploit ID or path
            
        Returns:
            Detailed exploit information
        """
        return self.tools.get_exploit_details(exploit_id)
    
    @kernel_function(name="update_database", description="Updates the SearchSploit database")
    def update_database(self) -> str:
        """
        Updates the SearchSploit database.
        
        Returns:
            Update result message
        """
        return self.tools.update_database()
    
    @kernel_function(name="list_platforms", description="Lists available platforms in the SearchSploit database")
    def list_platforms(self) -> str:
        """
        Lists available platforms in the SearchSploit database.
        
        Returns:
            List of available platforms
        """
        return self.tools.list_platforms()
    
    @kernel_function(name="download_exploit", description="Downloads an exploit to the specified path")
    def download_exploit(self, exploit_id: str, output_path: str = "./") -> str:
        """
        Downloads an exploit to the specified path.
        
        Args:
            exploit_id: The exploit ID or path
            output_path: Directory to save the exploit
            
        Returns:
            Download result message
        """
        return self.tools.download_exploit(exploit_id, output_path)