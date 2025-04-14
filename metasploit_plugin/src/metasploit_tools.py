import subprocess
import os
import json
import re
import time
import socket
from typing import List, Dict, Any, Optional, Tuple

class MetasploitTools:
    """Core functionality for Metasploit Framework tools interaction"""
    
    def __init__(self, host: str = "localhost", msf_path: str = "/usr/share/metasploit-framework"):
        """
        Initialize Metasploit tools with connection settings.
        
        Args:
            host: Host where Metasploit is running (default: localhost)
            msf_path: Path to Metasploit Framework installation
        """
        self.host = host
        self.msf_path = msf_path
        self.last_command_output = ""
    
    def list_modules(self, module_type: str = "exploit") -> str:
        """
        Lists available Metasploit modules of a specific type.
        
        Args:
            module_type: Type of module (exploit, auxiliary, post, payload, encoder, nop)
            
        Returns:
            List of available modules
        """
        valid_types = ["exploit", "auxiliary", "post", "payload", "encoder", "nop"]
        if module_type not in valid_types:
            return f"Error: Invalid module type. Valid types are: {', '.join(valid_types)}"
        
        try:
            # Use msfconsole to list modules
            cmd = ["ssh", self.host, f"cd {self.msf_path} && ./msfconsole -q -x 'show {module_type}; exit'"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return f"Error listing modules: {result.stderr}"
            
            # Format the output
            output = result.stdout.strip()
            # Store the raw output for later use
            self.last_command_output = output
            
            # Extract module names and descriptions
            modules = []
            for line in output.splitlines():
                # Skip header lines and empty lines
                if not line.strip() or "Name" in line or "----" in line or "Metasploit" in line:
                    continue
                modules.append(line.strip())
            
            return f"Available {module_type} modules:\n" + "\n".join(modules)
        
        except Exception as e:
            return f"Error listing modules: {str(e)}"
    
    def search_modules(self, query: str) -> str:
        """
        Searches Metasploit modules based on a query.
        
        Args:
            query: Search term (e.g., 'apache', 'windows', 'CVE-2021')
            
        Returns:
            List of matching modules
        """
        if not query or len(query) < 3:
            return "Error: Search query must be at least 3 characters long."
        
        try:
            # Escape query to prevent command injection
            safe_query = query.replace("'", "").replace('"', "").replace(";", "")
            
            # Use msfconsole to search for modules
            cmd = ["ssh", self.host, f"cd {self.msf_path} && ./msfconsole -q -x 'search {safe_query}; exit'"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return f"Error searching modules: {result.stderr}"
            
            # Format the output
            output = result.stdout.strip()
            # Store the raw output for later use
            self.last_command_output = output
            
            if "No results from search" in output:
                return f"No modules found matching '{query}'."
            
            return f"Search results for '{query}':\n{output}"
        
        except Exception as e:
            return f"Error searching modules: {str(e)}"
    
    def scan_target(self, target: str, scan_type: str = "basic") -> str:
        """
        Performs a scan on a target using Metasploit.
        
        Args:
            target: Target IP address or hostname
            scan_type: Type of scan (basic, comprehensive, service)
            
        Returns:
            Scan results
        """
        try:
            # Validate input
            if not self._is_valid_target(target):
                return "Error: Invalid target IP or hostname."
            
            scan_commands = {
                "basic": f"use auxiliary/scanner/portscan/tcp; set RHOSTS {target}; set PORTS 1-1000; run; exit",
                "comprehensive": f"use auxiliary/scanner/portscan/tcp; set RHOSTS {target}; set PORTS 1-65535; run; exit",
                "service": f"use auxiliary/scanner/discovery/udp_sweep; set RHOSTS {target}; run; exit"
            }
            
            if scan_type not in scan_commands:
                return f"Error: Invalid scan type. Valid types are: {', '.join(scan_commands.keys())}"
            
            # Use msfconsole to run the scan
            cmd = ["ssh", self.host, f"cd {self.msf_path} && ./msfconsole -q -x '{scan_commands[scan_type]}'"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                return f"Error scanning target: {result.stderr}"
            
            # Format the output
            output = result.stdout.strip()
            # Store the raw output for later use
            self.last_command_output = output
            
            return f"Scan results for {target}:\n{output}"
        
        except Exception as e:
            return f"Error scanning target: {str(e)}"
    
    def exploit_target(self, target: str, exploit_module: str, payload: str = "", options: Dict[str, str] = None) -> str:
        """
        Attempts to exploit a target using a specified module.
        
        Args:
            target: Target IP address or hostname
            exploit_module: Full path to exploit module (e.g., 'exploit/windows/smb/ms17_010_eternalblue')
            payload: Payload to use (leave empty for default)
            options: Additional options for the exploit
            
        Returns:
            Result of exploitation attempt
        """
        try:
            # Validate input
            if not self._is_valid_target(target):
                return "Error: Invalid target IP or hostname."
            
            if not exploit_module or not exploit_module.startswith(('exploit/', 'auxiliary/')):
                return "Error: Invalid exploit module. Must start with 'exploit/' or 'auxiliary/'."
            
            # Build the command
            cmd_parts = [f"use {exploit_module}", f"set RHOSTS {target}"]
            
            if payload:
                cmd_parts.append(f"set PAYLOAD {payload}")
            
            if options:
                for key, value in options.items():
                    # Sanitize option keys and values
                    safe_key = re.sub(r'[^A-Za-z0-9_]', '', key)
                    safe_value = value.replace("'", "").replace('"', "").replace(";", "")
                    cmd_parts.append(f"set {safe_key} {safe_value}")
            
            cmd_parts.extend(["show options", "exploit", "exit"])
            
            # Join all commands with semicolons
            msf_commands = "; ".join(cmd_parts)
            
            # Use msfconsole to run the exploit
            cmd = ["ssh", self.host, f"cd {self.msf_path} && ./msfconsole -q -x '{msf_commands}'"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                return f"Error running exploit: {result.stderr}"
            
            # Format the output
            output = result.stdout.strip()
            # Store the raw output for later use
            self.last_command_output = output
            
            if "Exploit completed" in output:
                return f"Exploit execution completed. Results:\n{output}"
            else:
                return f"Exploit execution results:\n{output}"
        
        except Exception as e:
            return f"Error running exploit: {str(e)}"
    
    def generate_payload(self, payload_type: str, output_format: str = "raw", options: Dict[str, str] = None) -> str:
        """
        Generates a payload using msfvenom.
        
        Args:
            payload_type: Type of payload (e.g., 'windows/meterpreter/reverse_tcp')
            output_format: Output format (raw, exe, python, ruby, etc.)
            options: Additional options for the payload
            
        Returns:
            Information about the generated payload
        """
        try:
            if not payload_type or not '/' in payload_type:
                return "Error: Invalid payload type. Must be in format like 'windows/meterpreter/reverse_tcp'."
            
            # Build the command
            cmd_parts = ["msfvenom", "-p", payload_type]
            
            valid_formats = ["raw", "exe", "elf", "dll", "vbs", "js", "war", "py", "rb", "pl", "sh"]
            if output_format not in valid_formats:
                return f"Error: Invalid output format. Valid formats are: {', '.join(valid_formats)}"
            
            cmd_parts.extend(["-f", output_format])
            
            if options:
                for key, value in options.items():
                    # Sanitize option keys and values
                    safe_key = re.sub(r'[^A-Za-z0-9_]', '', key)
                    safe_value = value.replace("'", "").replace('"', "").replace(";", "")
                    cmd_parts.append(f"{safe_key}={safe_value}")
            
            cmd_parts.append("--list-options")
            
            # Join all parts with spaces
            msf_command = " ".join(cmd_parts)
            
            # Use SSH to run msfvenom
            cmd = ["ssh", self.host, msf_command]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return f"Error generating payload: {result.stderr}"
            
            # Format the output
            output = result.stdout.strip()
            
            return f"Payload generation information:\n{output}"
        
        except Exception as e:
            return f"Error generating payload: {str(e)}"
    
    def list_sessions(self) -> str:
        """
        Lists active Metasploit sessions.
        
        Returns:
            List of active sessions
        """
        try:
            # Use msfconsole to list sessions
            cmd = ["ssh", self.host, f"cd {self.msf_path} && ./msfconsole -q -x 'sessions -l; exit'"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return f"Error listing sessions: {result.stderr}"
            
            # Format the output
            output = result.stdout.strip()
            
            if "No active sessions" in output or not "Id  Name" in output:
                return "No active Metasploit sessions."
            
            # Extract session information
            sessions = []
            in_session_list = False
            for line in output.splitlines():
                if "Id  Name" in line:
                    in_session_list = True
                    sessions.append(line.strip())
                    continue
                
                if in_session_list and line.strip() and not "Metasploit" in line:
                    sessions.append(line.strip())
            
            return "Active Metasploit sessions:\n" + "\n".join(sessions)
        
        except Exception as e:
            return f"Error listing sessions: {str(e)}"
    
    def _is_valid_target(self, target: str) -> bool:
        """Validates if target is a valid IP address or hostname"""
        # Validate IP address
        try:
            socket.inet_aton(target)
            return True
        except socket.error:
            pass
        
        # Validate hostname
        if re.match(r'^[a-zA-Z0-9.-]+$', target):
            return True
            
        return False