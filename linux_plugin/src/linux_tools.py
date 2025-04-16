import subprocess
import re
import os
from typing import Dict, Optional, List, Tuple, Any


class LinuxTools:
    def __init__(self):
        pass

    def run_command(self, command: str) -> Dict[str, Any]:
        """
        Executes a Linux command and returns the result.
        
        Args:
            command: The Linux command to execute
            
        Returns:
            Dictionary with success status, stdout, stderr and parsed results if applicable
        """
        try:
            # Split the command string into a list
            cmd_parts = command.split()
            
            # Run the command
            result = subprocess.run(
                cmd_parts, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            # Create response dictionary
            response = {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "parsed_data": self._parse_command_output(command, result.stdout)
            }
            
            return response
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timed out after 30 seconds",
                "parsed_data": None
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Error executing command: {str(e)}",
                "parsed_data": None
            }

    def _parse_command_output(self, command: str, output: str) -> Optional[Dict[str, Any]]:
        """
        Parses the output of common Linux commands into structured data.
        
        Args:
            command: The original command that was executed
            output: The command output to parse
            
        Returns:
            Structured data based on the command type or None if no parser is available
        """
        cmd_base = command.split()[0]
        
        # IP address related commands
        if cmd_base == "ip" and "addr" in command:
            return self._parse_ip_addr(output)
        elif cmd_base == "ifconfig":
            return self._parse_ifconfig(output)
        
        # System information commands
        elif cmd_base == "uname":
            return self._parse_uname(output)
        elif cmd_base == "free":
            return self._parse_free(output)
        elif cmd_base == "df":
            return self._parse_df(output)
        
        # Process related commands
        elif cmd_base == "ps":
            return self._parse_ps(output)
        
        # Network commands
        elif cmd_base == "netstat" or cmd_base == "ss":
            return self._parse_netstat(output)
        
        # Default - return the raw output in a simple structure
        return {"raw": output.strip()}

    def _parse_ip_addr(self, output: str) -> Dict[str, Any]:
        """Parse output from 'ip addr' command"""
        interfaces = {}
        current_interface = None
        
        for line in output.splitlines():
            # New interface section
            if line.startswith(tuple(str(i) + ":" for i in range(10))):
                parts = line.split(":", 2)
                if len(parts) >= 2:
                    interface_name = parts[1].strip()
                    current_interface = interface_name
                    interfaces[current_interface] = {
                        "addresses": [],
                        "state": "unknown",
                        "mac": None
                    }
                    
                    # Extract state if available
                    if "state" in line:
                        state_match = re.search(r"state (\w+)", line)
                        if state_match:
                            interfaces[current_interface]["state"] = state_match.group(1)
            
            # Interface is UP/DOWN
            elif current_interface and "UP" in line:
                interfaces[current_interface]["state"] = "UP"
            elif current_interface and "DOWN" in line:
                interfaces[current_interface]["state"] = "DOWN"
            
            # MAC address
            elif current_interface and "link/ether" in line:
                mac_match = re.search(r"link/ether ([0-9a-f:]+)", line.lower())
                if mac_match:
                    interfaces[current_interface]["mac"] = mac_match.group(1)
            
            # IPv4 address
            elif current_interface and "inet " in line:
                ipv4_match = re.search(r"inet (\d+\.\d+\.\d+\.\d+/\d+)", line)
                if ipv4_match:
                    interfaces[current_interface]["addresses"].append({
                        "type": "ipv4",
                        "address": ipv4_match.group(1)
                    })
            
            # IPv6 address
            elif current_interface and "inet6" in line:
                ipv6_match = re.search(r"inet6 ([0-9a-f:]+/\d+)", line)
                if ipv6_match:
                    interfaces[current_interface]["addresses"].append({
                        "type": "ipv6",
                        "address": ipv6_match.group(1)
                    })
        
        return {"interfaces": interfaces}

    def _parse_ifconfig(self, output: str) -> Dict[str, Any]:
        """Parse output from 'ifconfig' command"""
        interfaces = {}
        current_interface = None
        
        for line in output.splitlines():
            # New interface section
            if line and not line.startswith(" "):
                parts = line.split(":", 1)
                if len(parts) >= 1:
                    current_interface = parts[0].strip()
                    interfaces[current_interface] = {
                        "addresses": [],
                        "state": "unknown",
                        "mac": None
                    }
                    
                    # Check if the interface is UP
                    if "UP" in line:
                        interfaces[current_interface]["state"] = "UP"
                    elif "DOWN" in line:
                        interfaces[current_interface]["state"] = "DOWN"
            
            # MAC address
            elif current_interface and "ether" in line:
                mac_match = re.search(r"ether ([0-9a-f:]+)", line.lower())
                if mac_match:
                    interfaces[current_interface]["mac"] = mac_match.group(1)
            
            # IPv4 address
            elif current_interface and "inet " in line:
                ipv4_match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", line)
                if ipv4_match:
                    # Try to get netmask if available
                    netmask = ""
                    netmask_match = re.search(r"netmask (\d+\.\d+\.\d+\.\d+)", line)
                    if netmask_match:
                        netmask = netmask_match.group(1)
                    
                    interfaces[current_interface]["addresses"].append({
                        "type": "ipv4",
                        "address": ipv4_match.group(1),
                        "netmask": netmask
                    })
            
            # IPv6 address
            elif current_interface and "inet6" in line:
                ipv6_match = re.search(r"inet6 ([0-9a-f:]+)", line)
                if ipv6_match:
                    interfaces[current_interface]["addresses"].append({
                        "type": "ipv6",
                        "address": ipv6_match.group(1)
                    })
        
        return {"interfaces": interfaces}

    def _parse_uname(self, output: str) -> Dict[str, str]:
        """Parse output from 'uname' command"""
        # For uname -a
        if output.count(" ") > 2:  # uname -a output has multiple fields
            parts = output.split(None, 5)
            if len(parts) >= 6:
                return {
                    "kernel_name": parts[0],
                    "hostname": parts[1],
                    "kernel_release": parts[2],
                    "kernel_version": parts[3],
                    "machine": parts[4],
                    "processor": parts[5] if len(parts) > 5 else ""
                }
        
        # Simple uname
        return {"system": output.strip()}

    def _parse_free(self, output: str) -> Dict[str, Any]:
        """Parse output from 'free' command"""
        memory_data = {}
        lines = output.strip().split('\n')
        
        # Check if we have enough lines
        if len(lines) < 2:
            return {"raw": output.strip()}
        
        # Get headers
        headers = lines[0].split()
        
        # Process memory line
        if len(lines) > 1 and lines[1].startswith('Mem:'):
            mem_values = lines[1].split()[1:]
            memory_data['memory'] = dict(zip(headers, mem_values))
        
        # Process swap line if it exists
        if len(lines) > 2 and lines[2].startswith('Swap:'):
            swap_values = lines[2].split()[1:]
            memory_data['swap'] = dict(zip(headers, swap_values))
        
        return memory_data

    def _parse_df(self, output: str) -> Dict[str, List[Dict[str, str]]]:
        """Parse output from 'df' command"""
        lines = output.strip().split('\n')
        if len(lines) < 2:
            return {"raw": output.strip()}
        
        # Get headers and normalize them
        headers = [h.lower() for h in lines[0].split()]
        
        # Process filesystem entries
        filesystems = []
        for line in lines[1:]:
            if line.strip():
                values = line.split(None, len(headers) - 1)
                if len(values) == len(headers):
                    filesystems.append(dict(zip(headers, values)))
        
        return {"filesystems": filesystems}

    def _parse_ps(self, output: str) -> Dict[str, List[Dict[str, str]]]:
        """Parse output from 'ps' command"""
        lines = output.strip().split('\n')
        if len(lines) < 2:
            return {"raw": output.strip()}
        
        # Get headers - handle both space delimited and non-space delimited formats
        header_line = lines[0]
        if "PID" in header_line:
            headers = []
            positions = []
            
            # Find the starting positions of each column
            for match in re.finditer(r'\b\w+\b', header_line):
                headers.append(match.group().lower())
                positions.append(match.start())
            
            # Process processes
            processes = []
            for line in lines[1:]:
                if line.strip():
                    process_data = {}
                    for i in range(len(headers) - 1):
                        process_data[headers[i]] = line[positions[i]:positions[i+1]].strip()
                    # Handle the last column
                    process_data[headers[-1]] = line[positions[-1]:].strip()
                    processes.append(process_data)
            
            return {"processes": processes}
        else:
            # Simple space-delimited format
            headers = [h.lower() for h in lines[0].split()]
            processes = []
            for line in lines[1:]:
                if line.strip():
                    values = line.split(None, len(headers) - 1)
                    if len(values) == len(headers):
                        processes.append(dict(zip(headers, values)))
            
            return {"processes": processes}

    def _parse_netstat(self, output: str) -> Dict[str, List[Dict[str, str]]]:
        """Parse output from 'netstat' or 'ss' command"""
        lines = output.strip().split('\n')
        if len(lines) < 2:
            return {"raw": output.strip()}
        
        # Find the header line (might not be the first line due to potential introductory text)
        header_line_idx = -1
        for i, line in enumerate(lines):
            if "Proto" in line or "Netid" in line or "State" in line:
                header_line_idx = i
                break
        
        if header_line_idx == -1:
            return {"raw": output.strip()}
        
        # Get headers
        header_line = lines[header_line_idx]
        headers = []
        positions = []
        
        # Find the starting positions of each column
        for match in re.finditer(r'\b\w+\b', header_line):
            headers.append(match.group().lower())
            positions.append(match.start())
        
        # Process connections
        connections = []
        for line in lines[header_line_idx+1:]:
            if line.strip() and not line.startswith("Active") and not line.startswith("Proto"):
                connection_data = {}
                for i in range(len(headers) - 1):
                    if i < len(positions) - 1:
                        connection_data[headers[i]] = line[positions[i]:positions[i+1]].strip()
                # Handle the last column
                if len(headers) > 0 and len(positions) > 0:
                    connection_data[headers[-1]] = line[positions[-1]:].strip()
                if connection_data:
                    connections.append(connection_data)
        
        return {"connections": connections}