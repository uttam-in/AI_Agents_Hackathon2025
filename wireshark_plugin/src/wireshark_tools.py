import subprocess
import os
import tempfile
import datetime
import re
import ipaddress
from typing import List, Dict, Any, Optional

class WiresharkTools:
    """Core functionality for Wireshark network analysis tools"""
    
    def capture_packets(self, interface: str = "", duration: int = 10, 
                        filter_exp: str = "", count: int = 100) -> str:
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
        # Validate input
        if duration <= 0 or duration > 60:
            return "Error: Duration must be between 1 and 60 seconds."
        
        if count <= 0 or count > 1000:
            return "Error: Packet count must be between 1 and 1000."
            
        # Validate filter expression
        if filter_exp and not self._is_safe_filter(filter_exp):
            return "Error: Invalid or potentially unsafe filter expression."
        
        try:
            # Create a temporary file to store the capture
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            pcap_file = os.path.join(temp_dir, f"capture_{timestamp}.pcap")
            
            # Build command - try tshark first, fall back to tcpdump
            cmd = []
            try:
                # Check if tshark is available
                subprocess.run(["tshark", "-v"], capture_output=True, check=True)
                cmd = ["tshark"]
                if interface:
                    cmd.extend(["-i", interface])
                cmd.extend(["-a", f"duration:{duration}", "-c", str(count), "-w", pcap_file])
                if filter_exp:
                    cmd.extend(["-f", filter_exp])
            except (subprocess.SubprocessError, FileNotFoundError):
                # Fall back to tcpdump
                cmd = ["tcpdump"]
                if interface:
                    cmd.extend(["-i", interface])
                cmd.extend(["-G", str(duration), "-c", str(count), "-w", pcap_file])
                if filter_exp:
                    cmd.append(filter_exp)
            
            # Run the capture command
            capture_process = subprocess.run(cmd, capture_output=True, text=True, timeout=duration+5)
            
            if capture_process.returncode != 0:
                return f"Error capturing packets: {capture_process.stderr}"
            
            # Analyze the capture file
            return self._analyze_pcap(pcap_file)
        
        except Exception as e:
            return f"Error during packet capture: {str(e)}"
    
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
        try:
            # If no pcap file specified, find the most recent one
            if not pcap_file:
                temp_dir = tempfile.gettempdir()
                captures = [f for f in os.listdir(temp_dir) if f.startswith("capture_") and f.endswith(".pcap")]
                if not captures:
                    return "Error: No recent packet captures found."
                captures.sort(reverse=True)
                pcap_file = os.path.join(temp_dir, captures[0])
            
            # Validate file exists
            if not os.path.exists(pcap_file):
                return f"Error: Capture file {pcap_file} not found."
            
            # Build tshark command for analysis
            cmd = ["tshark", "-r", pcap_file, "-q", "-z", "io,stat,1"]
            
            # Add protocol filter if specified
            if protocol:
                valid_protocols = ["http", "dns", "tcp", "udp", "icmp", "arp", "ssh", "tls", "smtp"]
                if protocol.lower() not in valid_protocols:
                    return f"Error: Unsupported protocol. Supported protocols: {', '.join(valid_protocols)}"
                cmd.extend(["-Y", f"{protocol.lower()}"])
            
            # Add host filter if specified
            if host:
                try:
                    # Validate IP address
                    ipaddress.ip_address(host)
                    cmd.extend(["-Y", f"ip.addr=={host}"])
                except ValueError:
                    return "Error: Invalid IP address format."
            
            # Run the analysis
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return f"Error analyzing traffic: {result.stderr}"
            
            # Format the results
            return self._format_traffic_analysis(result.stdout)
        
        except Exception as e:
            return f"Error analyzing traffic: {str(e)}"
    
    def detect_anomalies(self, pcap_file: str = "", sensitivity: str = "medium") -> str:
        """
        Detects anomalies in network traffic like unusual ports, traffic spikes, etc.
        
        Args:
            pcap_file: Path to pcap file (leave empty to use most recent capture)
            sensitivity: Detection sensitivity (low, medium, high)
            
        Returns:
            List of detected anomalies if any
        """
        try:
            # If no pcap file specified, find the most recent one
            if not pcap_file:
                temp_dir = tempfile.gettempdir()
                captures = [f for f in os.listdir(temp_dir) if f.startswith("capture_") and f.endswith(".pcap")]
                if not captures:
                    return "Error: No recent packet captures found."
                captures.sort(reverse=True)
                pcap_file = os.path.join(temp_dir, captures[0])
            
            # Validate file exists
            if not os.path.exists(pcap_file):
                return f"Error: Capture file {pcap_file} not found."
            
            # Map sensitivity levels to threshold values
            sensitivity_map = {
                "low": 0.8,
                "medium": 0.6,
                "high": 0.4
            }
            
            threshold = sensitivity_map.get(sensitivity.lower(), 0.6)
            
            # Use tshark to get protocol hierarchy statistics
            cmd = ["tshark", "-r", pcap_file, "-q", "-z", "io,stat,1", "-z", "conv,tcp", "-z", "endpoints,ip"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return f"Error analyzing for anomalies: {result.stderr}"
            
            # Perform basic anomaly detection
            return self._detect_basic_anomalies(result.stdout, threshold)
        
        except Exception as e:
            return f"Error detecting anomalies: {str(e)}"
    
    def list_interfaces(self) -> str:
        """
        Lists available network interfaces for packet capture
        
        Returns:
            List of available network interfaces
        """
        try:
            # Try tshark first
            try:
                cmd = ["tshark", "-D"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return "Available capture interfaces:\n" + result.stdout
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
                
            # Fall back to other methods based on platform
            if os.name == 'nt':  # Windows
                cmd = ["ipconfig", "/all"]
            elif os.name == 'posix':  # Unix/Linux/MacOS
                cmd = ["ifconfig"]
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return f"Error listing interfaces: {result.stderr}"
                
            return "Available network interfaces:\n" + result.stdout
            
        except Exception as e:
            return f"Error listing interfaces: {str(e)}"
    
    def _is_safe_filter(self, filter_exp: str) -> bool:
        """Validates if a filter expression is safe to use"""
        # Basic validation to prevent command injection
        if len(filter_exp) > 100:
            return False
            
        # Check for suspicious patterns
        suspicious_patterns = [";", "&&", "||", "|", ">", "<", "$", "`", "\\"]
        if any(pattern in filter_exp for pattern in suspicious_patterns):
            return False
            
        return True
    
    def _analyze_pcap(self, pcap_file: str) -> str:
        """Analyzes a pcap file and returns a summary"""
        try:
            # Use tshark to analyze the capture file
            cmd = ["tshark", "-r", pcap_file, "-q", "-z", "io,stat,1", "-z", "conv,ip", "-z", "endpoints,ip"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return f"Error analyzing capture: {result.stderr}"
            
            # Extract key information
            packet_count = 0
            protocols = set()
            
            # Count packets
            packet_cmd = ["tshark", "-r", pcap_file, "-c", "1000"]
            packet_result = subprocess.run(packet_cmd, capture_output=True, text=True)
            packet_count = len(packet_result.stdout.splitlines())
            
            # Get protocols
            proto_cmd = ["tshark", "-r", pcap_file, "-T", "fields", "-e", "frame.protocols"]
            proto_result = subprocess.run(proto_cmd, capture_output=True, text=True)
            for line in proto_result.stdout.splitlines():
                if line:
                    for protocol in line.split(':'):
                        protocols.add(protocol)
            
            # Format summary
            summary = [
                f"Packet Capture Summary for {os.path.basename(pcap_file)}",
                f"- Total Packets: {packet_count}",
                f"- Protocols: {', '.join(sorted(protocols))}",
                "\nStatistics:",
                result.stdout
            ]
            
            return "\n".join(summary)
        
        except Exception as e:
            return f"Error analyzing capture file: {str(e)}"
    
    def _format_traffic_analysis(self, stdout: str) -> str:
        """Formats the traffic analysis output to be more readable"""
        lines = stdout.splitlines()
        formatted_output = []
        
        in_section = False
        current_section = ""
        
        for line in lines:
            # Detect section headers
            if line.startswith("=") and line.endswith("="):
                in_section = True
                current_section = line
                formatted_output.append(f"\n## {line.strip('=').strip()}")
                continue
                
            if in_section and line.strip():
                formatted_output.append(line)
        
        if not formatted_output:
            return "No significant traffic analysis results."
            
        return "\n".join(formatted_output)
    
    def _detect_basic_anomalies(self, stdout: str, threshold: float) -> str:
        """Performs basic anomaly detection on traffic data"""
        anomalies = []
        
        # Check for unusual ports
        unusual_ports = [22, 23, 3389, 8080, 4444, 31337]  # Just examples
        port_pattern = re.compile(r'(\d+)\s+(\w+)')
        
        # Extract TCP/UDP conversations
        in_conv_section = False
        for line in stdout.splitlines():
            if "TCP Conversations" in line or "UDP Conversations" in line:
                in_conv_section = True
                continue
                
            if in_conv_section and line.strip() and "Frames" in line:
                matches = port_pattern.findall(line)
                for match in matches:
                    port = int(match[0])
                    if port in unusual_ports:
                        anomalies.append(f"Unusual port detected: {port}")
        
        if not anomalies:
            return "No significant anomalies detected in the traffic."
            
        return "Potential anomalies detected:\n- " + "\n- ".join(anomalies)