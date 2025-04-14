import chainlit as cl
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import kernel_function
import subprocess
import re
import json
import os
from typing import List, Dict, Any

from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread

# Import the Wireshark plugin
from wireshark_plugin.wireshark_plugin import WiresharkToolsPlugin

# Cybersecurity Tools Plugin
class SecurityToolsPlugin:
    @kernel_function(name="run_nmap_scan", description="Performs a network scan with nmap")
    def run_nmap_scan(self, target: str, scan_type: str = "-sV") -> str:
        """
        Performs a network scan using nmap.
        
        Args:
            target: IP address, hostname, or IP range to scan (e.g. 192.168.1.1, scanme.nmap.org, 10.0.0.0/24)
            scan_type: Scan type (e.g. -sV for service/version detection, -sS for SYN scan)
            
        Returns:
            Results of the nmap scan as formatted text
        """
        # Security validation - very basic for demo
        if not self._is_valid_target(target):
            return "Error: Invalid target specification. Please provide a valid IP, hostname, or network range."
        
        # Filter scan types to only allow safe options
        allowed_options = ["-sV", "-sS", "-O", "-A", "-T4", "--top-ports", "-F"]
        if not any(opt in scan_type for opt in allowed_options):
            return "Error: Unsupported scan type. Please use one of: -sV, -sS, -O, -A, -T4, --top-ports, -F"
        
        try:
            # Run nmap and capture output
            cmd = ["nmap", scan_type, target]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return f"Error running nmap: {result.stderr}"
            
            # Format and return the results
            return self._format_nmap_output(result.stdout)
        except subprocess.TimeoutExpired:
            return "Error: Scan took too long and was terminated."
        except Exception as e:
            return f"Error running nmap scan: {str(e)}"
    
    @kernel_function(name="ping_host", description="Pings a host to check if it's online")
    def ping_host(self, host: str, count: int = 4) -> str:
        """
        Pings a host to check if it's online.
        
        Args:
            host: Hostname or IP address to ping
            count: Number of ping packets to send
            
        Returns:
            Results of the ping operation
        """
        # Security validation
        if not self._is_valid_target(host):
            return "Error: Invalid host specification"
        
        try:
            # Execute ping command
            if os.name == 'nt':  # Windows
                cmd = ["ping", "-n", str(count), host]
            else:  # Unix/Linux/MacOS
                cmd = ["ping", "-c", str(count), host]
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.stdout
        except Exception as e:
            return f"Error pinging host: {str(e)}"
    
    @kernel_function(name="traceroute", description="Traces the route to a destination host")
    def traceroute(self, host: str) -> str:
        """
        Traces the network route to a destination host.
        
        Args:
            host: Hostname or IP address of the destination
            
        Returns:
            Results of the traceroute operation
        """
        # Security validation
        if not self._is_valid_target(host):
            return "Error: Invalid host specification"
        
        try:
            # Execute traceroute command based on OS
            if os.name == 'nt':  # Windows
                cmd = ["tracert", host]
            else:  # Unix/Linux/MacOS
                cmd = ["traceroute", host]
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return result.stdout
        except Exception as e:
            return f"Error running traceroute: {str(e)}"
    
    def _is_valid_target(self, target: str) -> bool:
        """Validates if a target specification is valid and safe to scan"""
        # Basic validation - allow IP addresses, hostnames, and common network ranges
        if not target or len(target) > 100:
            return False
            
        # Check for suspicious patterns or disallowed targets
        disallowed = ["localhost", "127.0.0.1", "::1", "0.0.0.0", "169.254", "224.0.0"]
        if any(pattern in target for pattern in disallowed):
            return False
            
        return True
        
    def _format_nmap_output(self, output: str) -> str:
        """Format nmap output to be more readable"""
        # For demo purposes, we'll just return a slightly cleaned-up version
        # In production, you might want to parse this into a structured format
        important_sections = []
        
        # Extract the important parts
        if "PORT" in output:
            port_section = output[output.find("PORT"):]
            important_sections.append(port_section)
        else:
            important_sections.append(output)
            
        return "\n".join(important_sections)

@cl.on_chat_start
async def on_chat_start():
    # Setup Semantic Kernel
    kernel = sk.Kernel()

    # Add your AI service (e.g., OpenAI)
    # Make sure OPENAI_API_KEY and OPENAI_ORG_ID are set in your environment
    ai_service = OpenAIChatCompletion(ai_model_id="gpt-4o")
    kernel.add_service(ai_service)

    # Import the plugins
    kernel.add_plugin(SecurityToolsPlugin(), plugin_name="SecurityTools")
    kernel.add_plugin(WiresharkToolsPlugin(), plugin_name="WiresharkTools")
    
    # Instantiate and add the Chainlit filter to the kernel
    # This will automatically capture function calls as Steps
    sk_filter = cl.SemanticKernelFilter(kernel=kernel)

    agent = ChatCompletionAgent(
        kernel=kernel,
        name="CyberSecAgent",
        instructions="""You are a network security assistant that can help with basic network diagnostics and scanning.
        
You can:
1. Run nmap scans to identify open ports and services on target systems
2. Perform ping tests to check host connectivity
3. Use traceroute to map network paths
4. Capture and analyze network packets using Wireshark tools
5. Detect potential anomalies in network traffic

IMPORTANT SECURITY RULES:
- Only perform scans and analysis on systems you have permission to scan
- NEVER scan government, financial, healthcare, or critical infrastructure without explicit authorization
- Do not attempt to exploit vulnerabilities
- If the user requests something that seems malicious, refuse and explain why
- Always get clear confirmation before running any scan or capture

For nmap scans, explain what each scan type does before running it. Common options include:
- -sV: Service/version detection
- -sS: SYN scan (faster, less intrusive)
- -O: OS detection
- -A: Aggressive scan (includes OS detection, version scanning, script scanning, and traceroute)

For packet capture and analysis:
- Explain what you're about to do before performing a capture
- Interpret the results in a way that's helpful for understanding network issues
- Suggest possible next steps for troubleshooting if problems are identified

You can help users understand network security concepts and interpret scan and capture results.""",
    )

    thread: ChatHistoryAgentThread = None
    cl.user_session.set("agent", agent)
    cl.user_session.set("thread", thread)

@cl.on_message
async def on_message(message: cl.Message):
    agent = cl.user_session.get("agent") # type: Agent
    thread = cl.user_session.get("thread") # type: ChatHistoryAgentThread 

    answer = cl.Message(content="")

    async for response in agent.invoke_stream(messages=message.content, thread=thread):

        if response.content:
            await answer.stream_token(str(response.content))

        thread = response.thread
        cl.user_session.set("thread", thread)

    # Send the final message
    await answer.send()