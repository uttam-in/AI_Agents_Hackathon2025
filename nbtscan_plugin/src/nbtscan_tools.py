import subprocess
import re
import os
from typing import List, Dict, Optional

class NBTScanTools:
    """Implementation of NetBIOS scanning utilities using nbtscan"""
    
    def __init__(self):
        self._validate_nbtscan_installed()
        self.last_scan_results = ""
    
    def _validate_nbtscan_installed(self) -> None:
        """Check if nbtscan is installed on the system"""
        try:
            subprocess.run(["which", "nbtscan"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("Warning: nbtscan does not appear to be installed. Please install it using your package manager.")
    
    def scan_network(self, target: str, verbose: bool = False, resolve_names: bool = True) -> str:
        """
        Scans a network range for NetBIOS names
        
        Args:
            target: Target IP or network range (e.g., 192.168.1.0/24)
            verbose: Include verbose output with additional details
            resolve_names: Try to resolve NetBIOS names to IP addresses
            
        Returns:
            Formatted scan results
        """
        if not target or self._is_invalid_target(target):
            return "Error: Invalid target. Please provide a valid IP address or network range."
        
        try:
            cmd = ["nbtscan"]
            
            if verbose:
                cmd.append("-v")
                
            if not resolve_names:
                cmd.append("-n")
                
            cmd.append(target)
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return f"Error executing nbtscan: {result.stderr}"
                
            self.last_scan_results = result.stdout
            return self._format_scan_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            return "Error: Scan took too long and was terminated."
        except Exception as e:
            return f"Error performing nbtscan: {str(e)}"
    
    def scan_host(self, target_ip: str) -> str:
        """
        Scans a single host for NetBIOS information
        
        Args:
            target_ip: Target IP address
            
        Returns:
            Formatted scan results for the host
        """
        if not target_ip or self._is_invalid_target(target_ip):
            return "Error: Invalid IP address. Please provide a valid IP address."
            
        try:
            cmd = ["nbtscan", "-v", target_ip]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return f"Error executing nbtscan: {result.stderr}"
                
            return self._format_scan_output(result.stdout)
            
        except Exception as e:
            return f"Error performing host scan: {str(e)}"
    
    def get_detailed_info(self, target_ip: str) -> str:
        """
        Gets detailed NetBIOS information for a host
        
        Args:
            target_ip: Target IP address
            
        Returns:
            Detailed NetBIOS information
        """
        try:
            # Using nbtscan with verbose flag for detailed information
            cmd = ["nbtscan", "-v", "-h", target_ip]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return f"Error executing nbtscan: {result.stderr}"
                
            return self._format_detailed_output(result.stdout)
            
        except Exception as e:
            return f"Error retrieving detailed information: {str(e)}"
    
    def _is_invalid_target(self, target: str) -> bool:
        """
        Checks if a target specification is invalid
        
        Args:
            target: Target IP or network range
            
        Returns:
            True if target is invalid, False otherwise
        """
        if not target or len(target) > 100:
            return True
            
        # Disallow localhost, private addresses for safety
        disallowed = ["localhost", "127.0.0.1", "::1", "0.0.0.0"]
        if any(pattern == target for pattern in disallowed):
            return True
            
        return False
    
    def _format_scan_output(self, output: str) -> str:
        """
        Formats the raw nbtscan output for better readability
        
        Args:
            output: Raw nbtscan output
            
        Returns:
            Formatted scan results
        """
        if not output.strip():
            return "No NetBIOS information found."
            
        # Clean up the output and parse it into a structured format
        lines = output.strip().split('\n')
        formatted_output = []
        
        for line in lines:
            if line.strip() and not line.startswith("Doing NBT"):
                formatted_output.append(line)
        
        if not formatted_output:
            return "No NetBIOS information found."
            
        return "\n".join(formatted_output)
    
    def _format_detailed_output(self, output: str) -> str:
        """
        Formats detailed nbtscan output
        
        Args:
            output: Raw nbtscan detailed output
            
        Returns:
            Formatted detailed results
        """
        if not output.strip():
            return "No detailed NetBIOS information found."
            
        # Process the detailed output to make it more readable
        lines = output.strip().split('\n')
        formatted_output = []
        
        for line in lines:
            if line.strip() and not line.startswith("Doing NBT"):
                formatted_output.append(line)
        
        if not formatted_output:
            return "No detailed NetBIOS information found."
            
        return "\n".join(formatted_output)