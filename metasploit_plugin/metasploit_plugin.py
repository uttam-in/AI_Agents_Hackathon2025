import os
import sys
from typing import List, Dict, Any

# Add the parent directory to path so we can import the metasploit_tools module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from metasploit_plugin.src.metasploit_tools import MetasploitTools

from semantic_kernel.functions import kernel_function, KernelFunction

class MetasploitToolsPlugin:
    """Semantic Kernel plugin for Metasploit Framework security tools"""
    
    def __init__(self, host: str = "localhost", msf_path: str = "/usr/share/metasploit-framework"):
        """
        Initialize the Metasploit Tools Plugin.
        
        Args:
            host: Hostname or IP of the Kali Linux server running Metasploit
            msf_path: Path to Metasploit Framework installation on the server
        """
        self.tools = MetasploitTools(host, msf_path)
    
    @kernel_function(name="list_modules", description="Lists available Metasploit modules of a specific type")
    def list_modules(self, module_type: str = "exploit") -> str:
        """
        Lists available Metasploit modules of a specific type.
        
        Args:
            module_type: Type of module (exploit, auxiliary, post, payload, encoder, nop)
            
        Returns:
            List of available modules
        """
        return self.tools.list_modules(module_type)
    
    @kernel_function(name="search_modules", description="Searches Metasploit modules based on a query")
    def search_modules(self, query: str) -> str:
        """
        Searches Metasploit modules based on a query.
        
        Args:
            query: Search term (e.g., 'apache', 'windows', 'CVE-2021')
            
        Returns:
            List of matching modules
        """
        return self.tools.search_modules(query)
    
    @kernel_function(name="scan_target", description="Performs a scan on a target using Metasploit")
    def scan_target(self, target: str, scan_type: str = "basic") -> str:
        """
        Performs a scan on a target using Metasploit.
        
        Args:
            target: Target IP address or hostname
            scan_type: Type of scan (basic, comprehensive, service)
            
        Returns:
            Scan results
        """
        return self.tools.scan_target(target, scan_type)
    
    @kernel_function(name="exploit_target", description="Attempts to exploit a target using a specified module")
    def exploit_target(self, target: str, exploit_module: str, payload: str = "", options: str = "") -> str:
        """
        Attempts to exploit a target using a specified module.
        
        Args:
            target: Target IP address or hostname
            exploit_module: Full path to exploit module (e.g., 'exploit/windows/smb/ms17_010_eternalblue')
            payload: Payload to use (leave empty for default)
            options: Additional options for the exploit in format "key1=value1,key2=value2"
            
        Returns:
            Result of exploitation attempt
        """
        # Parse options string into dictionary
        options_dict = {}
        if options:
            for option in options.split(','):
                if '=' in option:
                    key, value = option.split('=', 1)
                    options_dict[key.strip()] = value.strip()
        
        return self.tools.exploit_target(target, exploit_module, payload, options_dict)
    
    @kernel_function(name="generate_payload", description="Generates a payload using msfvenom")
    def generate_payload(self, payload_type: str, output_format: str = "raw", options: str = "") -> str:
        """
        Generates a payload using msfvenom.
        
        Args:
            payload_type: Type of payload (e.g., 'windows/meterpreter/reverse_tcp')
            output_format: Output format (raw, exe, python, ruby, etc.)
            options: Additional options for the payload in format "key1=value1,key2=value2"
            
        Returns:
            Information about the generated payload
        """
        # Parse options string into dictionary
        options_dict = {}
        if options:
            for option in options.split(','):
                if '=' in option:
                    key, value = option.split('=', 1)
                    options_dict[key.strip()] = value.strip()
        
        return self.tools.generate_payload(payload_type, output_format, options_dict)
    
    @kernel_function(name="list_sessions", description="Lists active Metasploit sessions")
    def list_sessions(self) -> str:
        """
        Lists active Metasploit sessions.
        
        Returns:
            List of active sessions
        """
        return self.tools.list_sessions()
    
    @kernel_function(name="handle_interactive_shell", description="Handles an interactive shell session from an exploit like vsftpd_234_backdoor")
    def handle_interactive_shell(self, session_id: str = "1", commands: str = "") -> str:
        """
        Handles an interactive shell session.
        
        Args:
            session_id: The session ID to interact with (default: 1)
            commands: Comma-separated list of commands to run in the session
            
        Returns:
            Result of the interaction
        """
        try:
            # Convert session_id to integer
            session_id_int = int(session_id)
            
            # Parse commands into a list if provided
            command_list = None
            if commands:
                command_list = [cmd.strip() for cmd in commands.split(',')]
            
            return self.tools.handle_interactive_shell(session_id_int, command_list)
        except ValueError:
            return "Error: Session ID must be a valid integer."
        except Exception as e:
            return f"Error handling interactive shell: {str(e)}"