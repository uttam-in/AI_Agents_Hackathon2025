import os
import sys
from typing import List, Dict, Any, Optional, Union, Tuple

# Add the parent directory to path so we can import the nbtscan_tools module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nbtscan_plugin.src.nbtscan_tools import NBTScanTools

from semantic_kernel.functions import kernel_function, KernelFunction

class NBTScanToolsPlugin:
    """Semantic Kernel plugin for NetBIOS scanning with nbtscan"""
    
    def __init__(self):
        self.tools = NBTScanTools()
    
    @kernel_function(name="scan_network", description="Scans a network range for NetBIOS names")
    def scan_network(self, target: str, verbose: str = "false", resolve_names: str = "true") -> str:
        """
        Scans a network range for NetBIOS names
        
        Args:
            target: Target IP or network range (e.g., 192.168.1.0/24)
            verbose: Include verbose output with additional details ("true" or "false")
            resolve_names: Try to resolve NetBIOS names to IP addresses ("true" or "false")
            
        Returns:
            Formatted scan results
        """
        verbose_bool = verbose.lower() == "true"
        resolve_bool = resolve_names.lower() == "true"
        return self.tools.scan_network(target, verbose_bool, resolve_bool)
    
    @kernel_function(name="scan_host", description="Scans a single host for NetBIOS information")
    def scan_host(self, target_ip: str) -> str:
        """
        Scans a single host for NetBIOS information
        
        Args:
            target_ip: Target IP address
            
        Returns:
            Formatted scan results for the host
        """
        return self.tools.scan_host(target_ip)
    
    @kernel_function(name="get_detailed_info", description="Gets detailed NetBIOS information for a host")
    def get_detailed_info(self, target_ip: str) -> str:
        """
        Gets detailed NetBIOS information for a host
        
        Args:
            target_ip: Target IP address
            
        Returns:
            Detailed NetBIOS information
        """
        return self.tools.get_detailed_info(target_ip)