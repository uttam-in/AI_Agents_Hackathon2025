import sys
import os
import subprocess
from semantic_kernel.functions import kernel_function

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Import the tools
from netdiscover_plugin.src.netdiscover_tools import NetdiscoverTools

class NetdiscoverToolsPlugin:
    """Plugin for network discovery tools using netdiscover."""

    def __init__(self):
        self._tools = NetdiscoverTools()

    @kernel_function(
        description="Scan local network to discover active hosts using netdiscover",
        name="scan_network",
    )
    def scan_network(self, ip_range: str = "192.168.1.0/24") -> str:
        """
        Scan the local network to discover active hosts using netdiscover.
        
        Args:
            ip_range: The IP range to scan in CIDR notation (e.g., 192.168.1.0/24)
            
        Returns:
            A string containing the scan results
        """
        return self._tools.scan_network(ip_range)

    @kernel_function(
        description="Passive network scanning to discover hosts without sending packets",
        name="passive_scan",
    )
    def passive_scan(self, interface: str = "eth0", duration: int = 30) -> str:
        """
        Perform a passive scan of the network to discover hosts without sending packets.
        
        Args:
            interface: The network interface to use for sniffing
            duration: How long to run the passive scan in seconds
            
        Returns:
            A string containing the passive scan results
        """
        return self._tools.passive_scan(interface, duration)