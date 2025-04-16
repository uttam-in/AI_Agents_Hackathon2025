"""Netdiscover tools module for network discovery."""

import subprocess
import time
import re
import os

class NetdiscoverTools:
    """Tools for network discovery using netdiscover."""
    
    def __init__(self):
        """Initialize the NetdiscoverTools object."""
        pass
        
    def scan_network(self, ip_range: str = "192.168.1.0/24") -> str:
        """
        Scan the local network to discover active hosts using netdiscover.
        
        Args:
            ip_range: The IP range to scan in CIDR notation (e.g., 192.168.1.0/24)
            
        Returns:
            A string containing the scan results
        """
        try:
            # Run netdiscover with a timeout to ensure it doesn't run indefinitely
            cmd = ["netdiscover", "-r", ip_range, "-P", "-N"]
            
            # Execute the command with a timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60-second timeout
            )
            
            if result.returncode != 0:
                return f"Error running netdiscover: {result.stderr}"
                
            # Process and format the output
            output = result.stdout
            if not output.strip():
                return "No hosts found or netdiscover returned no results."
                
            # Parse and format the output for better readability
            return self._format_scan_results(output)
            
        except subprocess.TimeoutExpired:
            return "Netdiscover scan timed out after 60 seconds."
        except FileNotFoundError:
            return "Netdiscover tool not found. Please ensure it is installed."
        except Exception as e:
            return f"An error occurred while running netdiscover: {str(e)}"
            
    def passive_scan(self, interface: str = "eth0", duration: int = 30) -> str:
        """
        Perform a passive scan of the network to discover hosts without sending packets.
        
        Args:
            interface: The network interface to use for sniffing
            duration: How long to run the passive scan in seconds
            
        Returns:
            A string containing the passive scan results
        """
        try:
            # Run netdiscover in passive mode
            cmd = ["netdiscover", "-p", "-i", interface, "-N"]
            
            print(f"Starting passive network scan on interface {interface} for {duration} seconds...")
            
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Let it run for the specified duration
            time.sleep(duration)
            
            # Terminate the process
            process.terminate()
            try:
                process.wait(timeout=5)  # Wait up to 5 seconds for graceful termination
            except subprocess.TimeoutExpired:
                process.kill()  # Force kill if it doesn't terminate
                
            # Get output
            stdout, stderr = process.communicate()
            
            if stderr:
                return f"Error during passive scan: {stderr}"
                
            if not stdout.strip():
                return "No hosts discovered during passive scan."
                
            # Process and format the output
            return self._format_scan_results(stdout)
            
        except FileNotFoundError:
            return "Netdiscover tool not found. Please ensure it is installed."
        except Exception as e:
            return f"An error occurred during passive network scan: {str(e)}"
            
    def _format_scan_results(self, output: str) -> str:
        """
        Format the netdiscover output for better readability.
        
        Args:
            output: The raw output from netdiscover
            
        Returns:
            Formatted string with discovered hosts
        """
        # Extract the relevant information from the output
        lines = output.strip().split('\n')
        formatted_results = []
        
        # Find the header line and data lines
        data_started = False
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
                
            # Check if this is the header line
            if "IP" in line and "MAC" in line and "COUNT" in line:
                data_started = True
                formatted_results.append("DISCOVERED HOSTS:")
                formatted_results.append("-" * 80)
                formatted_results.append(f"{'IP Address':<18} {'MAC Address':<20} {'Vendor'}")
                formatted_results.append("-" * 80)
                continue
                
            # If we've found the header, start processing data lines
            if data_started:
                # Try to parse the line with IP and MAC addresses
                ip_mac_match = re.search(r'\s*(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F:]{17})\s+(\d+)\s*(.*)', line)
                if ip_mac_match:
                    ip = ip_mac_match.group(1)
                    mac = ip_mac_match.group(2)
                    vendor = ip_mac_match.group(4).strip()
                    formatted_results.append(f"{ip:<18} {mac:<20} {vendor}")
        
        # If no formatted results were added, return the original output
        if len(formatted_results) <= 4:  # Just the headers
            return "No hosts discovered or unable to parse netdiscover output."
            
        return "\n".join(formatted_results)