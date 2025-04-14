import os
import sys
from typing import List, Dict, Any

# Add the parent directory to path so we can import the wireshark_tools module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wireshark_plugin.src.wireshark_tools import WiresharkTools

from semantic_kernel.functions import kernel_function, KernelFunction

class WiresharkToolsPlugin:
    """Semantic Kernel plugin for Wireshark network analysis tools"""
    
    def __init__(self):
        self.tools = WiresharkTools()
    
    @kernel_function(name="capture_packets", description="Captures network packets using tcpdump/tshark")
    def capture_packets(self, interface: str = "", duration: int = 10, filter_exp: str = "", count: int = 100) -> str:
        """
        Captures network packets using tcpdump or tshark.
        
        Args:
            interface: Network interface to capture packets from (leave empty for default)
            duration: Duration of capture in seconds (default: 10)
            filter_exp: Packet filter expression (e.g., "tcp port 80", "host 192.168.1.1")
            count: Maximum number of packets to capture (default: 100)
            
        Returns:
            Summary of captured packets
        """
        try:
            duration = int(duration)
            count = int(count)
            return self.tools.capture_packets(interface, duration, filter_exp, count)
        except ValueError:
            return "Error: Duration and count must be integers."
    
    @kernel_function(name="analyze_traffic", description="Analyzes network traffic patterns from a pcap file")
    def analyze_traffic(self, pcap_file: str = "", protocol: str = "", host: str = "") -> str:
        """
        Analyzes captured network traffic patterns.
        
        Args:
            pcap_file: Path to pcap file (leave empty to use most recent capture)
            protocol: Filter by protocol (e.g., "http", "dns", "tcp")
            host: Filter by host IP address
            
        Returns:
            Analysis of network traffic
        """
        return self.tools.analyze_traffic(pcap_file, protocol, host)
    
    @kernel_function(name="detect_anomalies", description="Detects anomalies in network traffic")
    def detect_anomalies(self, pcap_file: str = "", sensitivity: str = "medium") -> str:
        """
        Detects anomalies in network traffic like unusual ports, traffic spikes, etc.
        
        Args:
            pcap_file: Path to pcap file (leave empty to use most recent capture)
            sensitivity: Detection sensitivity (low, medium, high)
            
        Returns:
            List of detected anomalies if any
        """
        return self.tools.detect_anomalies(pcap_file, sensitivity)
    
    @kernel_function(name="list_interfaces", description="Lists available network interfaces for packet capture")
    def list_interfaces(self) -> str:
        """
        Lists available network interfaces for packet capture
        
        Returns:
            List of available network interfaces
        """
        return self.tools.list_interfaces()