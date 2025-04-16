import json
from typing import Dict, Any
from semantic_kernel.functions import kernel_function
from linux_plugin.src.linux_tools import LinuxTools

class LinuxToolsPlugin:
    """Plugin for executing Linux commands and parsing their output"""

    def __init__(self):
        self.linux_tools = LinuxTools()

    @kernel_function(name="execute_command", description="Executes a Linux command and returns the result")
    def execute_command(self, command: str) -> str:
        """
        Executes a Linux command and returns the result.
        
        Args:
            command: The Linux command to execute
            
        Returns:
            A string with the command output or error message
        """
        if not command or not isinstance(command, str):
            return "Error: Please provide a valid command string"
        
        # Security check - block potentially harmful commands
        if self._is_potentially_harmful(command):
            return "Error: This command is potentially harmful and has been blocked for security reasons"
        
        # Execute the command
        result = self.linux_tools.run_command(command)
        
        # Format the response for the agent
        response = self._format_response(command, result)
        return response

    @kernel_function(name="get_ip_address", description="Gets the IP address for a specified network interface")
    def get_ip_address(self, interface: str = "") -> str:
        """
        Gets the IP address for a specified network interface.
        
        Args:
            interface: The network interface name (e.g., eth0, wlan0). If empty, will return info for all interfaces.
            
        Returns:
            A string with the IP address information
        """
        # Execute the command
        command = "ip addr show" if not interface else f"ip addr show {interface}"
        result = self.linux_tools.run_command(command)
        
        # Check for errors
        if not result["success"]:
            return f"Error getting IP address: {result['stderr']}"
        
        # Format the response specific to IP address query
        response = self._format_ip_address_response(interface, result)
        return response

    @kernel_function(name="check_system_info", description="Retrieves system information from the host")
    def check_system_info(self, info_type: str = "all") -> str:
        """
        Retrieves system information from the host.
        
        Args:
            info_type: The type of information to retrieve (os, cpu, memory, disk, all)
            
        Returns:
            A string with the requested system information
        """
        responses = []
        
        # OS information
        if info_type.lower() in ["os", "all"]:
            uname_result = self.linux_tools.run_command("uname -a")
            if uname_result["success"]:
                responses.append(f"OS Information:\n{uname_result['stdout']}")
        
        # CPU information
        if info_type.lower() in ["cpu", "all"]:
            cpu_result = self.linux_tools.run_command("cat /proc/cpuinfo | grep 'model name' | uniq")
            if cpu_result["success"]:
                responses.append(f"CPU Information:\n{cpu_result['stdout']}")
        
        # Memory information
        if info_type.lower() in ["memory", "all"]:
            memory_result = self.linux_tools.run_command("free -h")
            if memory_result["success"]:
                responses.append(f"Memory Information:\n{memory_result['stdout']}")
        
        # Disk information
        if info_type.lower() in ["disk", "all"]:
            disk_result = self.linux_tools.run_command("df -h")
            if disk_result["success"]:
                responses.append(f"Disk Information:\n{disk_result['stdout']}")
        
        if not responses:
            return f"Unknown information type: {info_type}. Valid options are: os, cpu, memory, disk, all"
        
        return "\n\n".join(responses)

    def _is_potentially_harmful(self, command: str) -> bool:
        """
        Check if a command is potentially harmful or dangerous.
        
        This is a basic implementation and should be expanded for production use.
        """
        # List of dangerous commands or command parts
        dangerous_commands = [
            "rm -rf /", "mkfs", "dd if=/dev/zero", "> /dev/sda", 
            ":(){ :|:& };:", "chmod -R 777 /", "mv ~ /dev/null"
        ]
        
        # Check if any dangerous pattern is in the command
        for pattern in dangerous_commands:
            if pattern in command:
                return True
                
        return False
        
    def _format_response(self, command: str, result: Dict[str, Any]) -> str:
        """
        Format the command result into a readable string response.
        """
        if not result["success"]:
            return f"Error executing command '{command}':\n{result['stderr']}"
        
        # Start with the command that was executed
        response_parts = [f"Command executed: {command}\n"]
        
        # Add the parsed data if available
        if result["parsed_data"]:
            response_parts.append("Parsed results:")
            response_parts.append(json.dumps(result["parsed_data"], indent=2))
        
        # Add the raw output
        response_parts.append("\nRaw output:")
        response_parts.append(result["stdout"] if result["stdout"] else "(no output)")
        
        # Join all parts
        return "\n".join(response_parts)
    
    def _format_ip_address_response(self, interface: str, result: Dict[str, Any]) -> str:
        """
        Format IP address information into a readable string response.
        """
        if not result["success"]:
            return f"Error getting IP address information: {result['stderr']}"
        
        # If we have parsed data with interfaces
        if result["parsed_data"] and "interfaces" in result["parsed_data"]:
            interfaces = result["parsed_data"]["interfaces"]
            
            # If a specific interface was requested
            if interface and interface in interfaces:
                interface_data = interfaces[interface]
                ip_addresses = []
                
                # Get IPv4 addresses
                for addr in interface_data["addresses"]:
                    if addr["type"] == "ipv4":
                        ip_addresses.append(f"IPv4: {addr['address']}")
                    elif addr["type"] == "ipv6":
                        ip_addresses.append(f"IPv6: {addr['address']}")
                
                if ip_addresses:
                    mac = f"MAC: {interface_data['mac']}" if interface_data["mac"] else "MAC: Not available"
                    state = f"State: {interface_data['state']}"
                    return f"Interface {interface}\n{state}\n{mac}\n" + "\n".join(ip_addresses)
                else:
                    return f"No IP addresses found for interface {interface}"
            
            # For all interfaces
            elif not interface:
                response_parts = ["IP Address Information:"]
                
                for if_name, if_data in interfaces.items():
                    ip_addresses = []
                    for addr in if_data["addresses"]:
                        if addr["type"] == "ipv4":
                            ip_addresses.append(f"  IPv4: {addr['address']}")
                        elif addr["type"] == "ipv6":
                            ip_addresses.append(f"  IPv6: {addr['address']}")
                    
                    if ip_addresses:
                        mac = f"  MAC: {if_data['mac']}" if if_data["mac"] else "  MAC: Not available"
                        state = f"  State: {if_data['state']}"
                        response_parts.append(f"\nInterface {if_name}:\n{state}\n{mac}\n" + "\n".join(ip_addresses))
                
                return "\n".join(response_parts)
            
            # Interface not found
            else:
                return f"Interface {interface} not found. Available interfaces: {', '.join(interfaces.keys())}"
        
        # No parsed data, return raw output
        return f"IP Address Information:\n{result['stdout']}"