import os
import sys
from typing import List, Dict, Any

# Add the parent directory to path so we can import the burp_suite_tools module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from burp_suite_plugin.src.burp_suite_tools import BurpSuiteTools

from semantic_kernel.functions import kernel_function, KernelFunction

class BurpSuiteToolsPlugin:
    """Semantic Kernel plugin for Burp Suite web application security testing tools"""
    
    def __init__(self, burp_path: str = "burpsuite"):
        """
        Initialize the Burp Suite Tools Plugin.
        
        Args:
            burp_path: Path to Burp Suite executable or command
        """
        self.tools = BurpSuiteTools(burp_path)
    
    @kernel_function(name="scan_target", description="Performs a web security scan on a target URL using Burp Suite")
    def scan_target(self, target_url: str, scan_type: str = "passive") -> str:
        """
        Performs a web security scan on a target URL using Burp Suite.
        
        Args:
            target_url: The URL to scan
            scan_type: Type of scan (passive, active, crawler)
            
        Returns:
            Scan results as a string
        """
        return self.tools.scan_target(target_url, scan_type)
    
    @kernel_function(name="analyze_request", description="Analyzes an HTTP request for security issues")
    def analyze_request(self, request_file: str = "", raw_request: str = "") -> str:
        """
        Analyzes an HTTP request for security issues.
        
        Args:
            request_file: Path to a file containing an HTTP request (optional)
            raw_request: Raw HTTP request string (optional)
            
        Returns:
            Analysis of the HTTP request
        """
        return self.tools.analyze_request(request_file, raw_request)
    
    @kernel_function(name="send_to_intruder", description="Sets up a Burp Intruder attack configuration")
    def send_to_intruder(self, target_url: str, parameters: str = "all", attack_type: str = "sniper") -> str:
        """
        Sets up a Burp Intruder attack configuration.
        
        Args:
            target_url: The target URL for the intruder attack
            parameters: Which parameters to target (all, query, body, cookies, headers)
            attack_type: Type of intruder attack (sniper, battering ram, pitchfork, cluster bomb)
            
        Returns:
            Intruder configuration details
        """
        return self.tools.send_to_intruder(target_url, parameters, attack_type)
    
    @kernel_function(name="test_for_vulns", description="Tests a target for specific vulnerability types")
    def test_for_vulns(self, target_url: str, vuln_type: str) -> str:
        """
        Tests a target for specific vulnerability types.
        
        Args:
            target_url: The URL to test
            vuln_type: Type of vulnerability to test for (xss, sqli, csrf, ssrf, idor, open_redirect, file_inclusion)
            
        Returns:
            Vulnerability test results
        """
        return self.tools.test_for_vulns(target_url, vuln_type)
    
    @kernel_function(name="export_site_map", description="Exports the Burp site map for a target domain")
    def export_site_map(self, target_url: str = "", output_format: str = "json") -> str:
        """
        Exports the Burp site map for a target domain.
        
        Args:
            target_url: The URL to export the site map for (optional, exports all if empty)
            output_format: Format of export (json, xml, html)
            
        Returns:
            Site map data or export confirmation
        """
        return self.tools.export_site_map(target_url, output_format)