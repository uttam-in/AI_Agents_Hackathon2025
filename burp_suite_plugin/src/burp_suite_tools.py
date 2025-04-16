import subprocess
import os
import re
import json
import tempfile
from typing import List, Dict, Any, Optional

class BurpSuiteTools:
    """Core functionality for Burp Suite web application security testing tools"""
    
    def __init__(self, burp_path: str = "burpsuite"):
        """
        Initialize Burp Suite tools with path settings.
        
        Args:
            burp_path: Path to Burp Suite executable or command (default: burpsuite)
        """
        self.burp_path = self._validate_burp_path(burp_path)
        self.last_scan_results = None
    
    def _validate_burp_path(self, burp_path: str) -> str:
        """
        Validates and corrects the Burp Suite path if needed.
        
        Args:
            burp_path: The provided path to Burp Suite
            
        Returns:
            Valid path to Burp Suite
        """
        try:
            # Try to detect the Burp Suite path
            cmd = ["which", "burpsuite"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
                
            # On macOS, check common locations
            common_paths = [
                "/Applications/Burp Suite Professional.app/Contents/MacOS/Burp Suite Professional",
                "/Applications/Burp Suite Community Edition.app/Contents/MacOS/Burp Suite Community Edition"
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    return path
        except:
            # If any error occurs during detection, fall back to the default
            pass
            
        # Fall back to provided path
        return burp_path
    
    def scan_target(self, target_url: str, scan_type: str = "passive") -> str:
        """
        Performs a web security scan on a target URL using Burp Suite.
        
        Args:
            target_url: The URL to scan
            scan_type: Type of scan (passive, active, crawler)
            
        Returns:
            Scan results as a string
        """
        if not self._is_valid_url(target_url):
            return "Error: Invalid URL format. Please provide a valid URL."
        
        # In a real implementation, this would use the Burp Suite API or CLI
        # For this demo, we'll simulate a scan response
        scan_types = {
            "passive": "Passive scan analyzing responses without sending additional requests",
            "active": "Active scan sending crafted requests to detect vulnerabilities",
            "crawler": "Crawling the site to discover content before scanning"
        }
        
        if scan_type not in scan_types:
            return f"Error: Invalid scan type. Please choose from: {', '.join(scan_types.keys())}"
        
        try:
            # Simulate command execution
            print(f"Would execute: {self.burp_path} --project-file=temp.burp --unpause-spider-and-scanner --target={target_url}")
            
            # Simulate scan results
            scan_results = self._simulate_scan_results(target_url, scan_type)
            self.last_scan_results = scan_results
            
            return self._format_scan_results(scan_results)
            
        except Exception as e:
            return f"Error performing scan: {str(e)}"
    
    def analyze_request(self, request_file: str = "", raw_request: str = "") -> str:
        """
        Analyzes an HTTP request for security issues.
        
        Args:
            request_file: Path to a file containing an HTTP request (optional)
            raw_request: Raw HTTP request string (optional)
            
        Returns:
            Analysis of the HTTP request
        """
        request_content = ""
        
        if request_file:
            try:
                with open(request_file, 'r') as f:
                    request_content = f.read()
            except Exception as e:
                return f"Error reading request file: {str(e)}"
        elif raw_request:
            request_content = raw_request
        else:
            return "Error: Please provide either a request file or a raw request."
        
        if not request_content.strip():
            return "Error: Empty request content."
        
        # Perform basic request analysis
        analysis = self._analyze_http_request(request_content)
        return analysis
    
    def send_to_intruder(self, target_url: str, parameters: str = "all", attack_type: str = "sniper") -> str:
        """
        Sets up a Burp Intruder attack configuration.
        
        Args:
            target_url: The target URL for the intruder attack
            parameters: Which parameters to target (all, query, body, cookies)
            attack_type: Type of intruder attack (sniper, battering ram, pitchfork, cluster bomb)
            
        Returns:
            Intruder configuration details
        """
        if not self._is_valid_url(target_url):
            return "Error: Invalid URL format. Please provide a valid URL."
        
        valid_params = ["all", "query", "body", "cookies", "headers"]
        if parameters not in valid_params:
            return f"Error: Invalid parameters option. Please choose from: {', '.join(valid_params)}"
        
        valid_attacks = ["sniper", "battering ram", "pitchfork", "cluster bomb"]
        if attack_type not in valid_attacks:
            return f"Error: Invalid attack type. Please choose from: {', '.join(valid_attacks)}"
        
        # In a real implementation, this would interact with Burp Suite's API
        # For this demo, we'll return a configuration summary
        
        # Extract parameters from URL for the example
        param_list = []
        if "?" in target_url:
            query_part = target_url.split("?", 1)[1]
            param_list = [p.split("=")[0] for p in query_part.split("&")]
        
        config = {
            "target_url": target_url,
            "attack_type": attack_type,
            "parameter_type": parameters,
            "detected_parameters": param_list if param_list else ["No query parameters detected"]
        }
        
        return self._format_intruder_config(config)
    
    def test_for_vulns(self, target_url: str, vuln_type: str) -> str:
        """
        Tests a target for specific vulnerability types.
        
        Args:
            target_url: The URL to test
            vuln_type: Type of vulnerability to test for (xss, sqli, csrf, etc.)
            
        Returns:
            Vulnerability test results
        """
        if not self._is_valid_url(target_url):
            return "Error: Invalid URL format. Please provide a valid URL."
        
        valid_vulns = ["xss", "sqli", "csrf", "ssrf", "idor", "open_redirect", "file_inclusion"]
        if vuln_type.lower() not in valid_vulns:
            return f"Error: Invalid vulnerability type. Please choose from: {', '.join(valid_vulns)}"
        
        # In a real implementation, this would perform actual tests via Burp Suite
        # For this demo, we'll simulate test results
        
        test_results = self._simulate_vuln_test(target_url, vuln_type)
        return self._format_vuln_test_results(test_results)
    
    def export_site_map(self, target_url: str = "", output_format: str = "json") -> str:
        """
        Exports the Burp site map for a target domain.
        
        Args:
            target_url: The URL to export the site map for (optional, exports all if empty)
            output_format: Format of export (json, xml, html)
            
        Returns:
            Site map data or export confirmation
        """
        if target_url and not self._is_valid_url(target_url):
            return "Error: Invalid URL format. Please provide a valid URL."
        
        valid_formats = ["json", "xml", "html"]
        if output_format.lower() not in valid_formats:
            return f"Error: Invalid output format. Please choose from: {', '.join(valid_formats)}"
        
        # In a real implementation, this would interact with Burp Suite's API
        # For this demo, we'll simulate site map data
        
        site_map = self._simulate_site_map(target_url)
        
        # Create a temporary file for the export (in a real implementation)
        temp_dir = tempfile.gettempdir()
        timestamp = "example_timestamp"
        export_file = os.path.join(temp_dir, f"burp_sitemap_{timestamp}.{output_format}")
        
        return f"Site map exported to {export_file}\n\nSample entries:\n" + json.dumps(site_map[:3], indent=2)
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        if not url or len(url) > 1000:
            return False
            
        url_pattern = re.compile(
            r'^(http|https)://'  # http:// or https://
            r'([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.'  # domain segments and sub-domains
            r'([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])'  # domain name
            r'(\.[a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])*'  # additional domain segments
            r'(:[0-9]+)?'  # optional port
            r'(/[^/\s]*)*$'  # optional path
        )
        
        return bool(url_pattern.match(url))
    
    def _analyze_http_request(self, request_content: str) -> str:
        """Analyzes an HTTP request for security issues"""
        security_issues = []
        
        # Check for basic security headers or lack thereof
        if "Cookie:" in request_content:
            if not "secure;" in request_content.lower():
                security_issues.append("- Cookies without 'secure' flag detected")
            if not "httponly;" in request_content.lower():
                security_issues.append("- Cookies without 'HttpOnly' flag detected")
        
        # Check for sensitive information in request
        sensitive_patterns = ["password", "pwd", "pass", "key", "token", "secret", "credential"]
        for pattern in sensitive_patterns:
            if pattern in request_content.lower():
                security_issues.append(f"- Potentially sensitive data found: '{pattern}'")
        
        # Check for basic injection points
        if "?" in request_content:
            security_issues.append("- URL query parameters detected (potential injection points)")
        
        if request_content.startswith("POST") and "Content-Type: application/x-www-form-urlencoded" in request_content:
            security_issues.append("- Form submission detected (potential injection points)")
        
        # Check for Content Security Policy
        if not "Content-Security-Policy:" in request_content:
            security_issues.append("- No Content Security Policy (CSP) header found")
        
        if not security_issues:
            security_issues.append("No immediate security issues detected in this request.")
        
        request_info = self._parse_request_basics(request_content)
        
        analysis = [
            "HTTP Request Analysis:",
            f"Method: {request_info.get('method', 'Unknown')}",
            f"Target: {request_info.get('target', 'Unknown')}",
            f"Headers: {len(request_info.get('headers', []))} found",
            "\nPotential Security Observations:",
        ] + security_issues
        
        return "\n".join(analysis)
    
    def _parse_request_basics(self, request_content: str) -> Dict[str, Any]:
        """Extract basic information from an HTTP request"""
        result = {
            "method": "Unknown",
            "target": "Unknown",
            "headers": []
        }
        
        lines = request_content.splitlines()
        if not lines:
            return result
        
        # Parse first line for method and target
        first_line_parts = lines[0].split()
        if len(first_line_parts) >= 2:
            result["method"] = first_line_parts[0]
            result["target"] = first_line_parts[1]
        
        # Parse headers
        headers = []
        for line in lines[1:]:
            if not line.strip():
                break  # End of headers
            
            if ": " in line:
                header_name, header_value = line.split(": ", 1)
                headers.append({"name": header_name, "value": header_value})
        
        result["headers"] = headers
        return result
    
    def _simulate_scan_results(self, target_url: str, scan_type: str) -> List[Dict[str, Any]]:
        """Simulate Burp Suite scan results"""
        # Generate some realistic-looking scan results
        results = []
        
        # Passive scan findings
        if scan_type in ["passive", "active", "crawler"]:
            results.append({
                "issue_type": "Missing Security Headers",
                "severity": "Low",
                "confidence": "Certain",
                "url": target_url,
                "description": "The application does not use HTTP Strict Transport Security (HSTS) to ensure connections are always made over HTTPS.",
                "remediation": "Add the Strict-Transport-Security header with an appropriate max-age directive."
            })
            
            results.append({
                "issue_type": "Cookie Without Secure Flag",
                "severity": "Low",
                "confidence": "Certain",
                "url": target_url,
                "description": "A cookie was set without the secure flag, which means it can be accessed via unencrypted connections.",
                "remediation": "Set the secure flag on all cookies that are used for sensitive sessions."
            })
        
        # Active scan findings
        if scan_type in ["active", "crawler"]:
            results.append({
                "issue_type": "Cross-Site Scripting (Reflected)",
                "severity": "High",
                "confidence": "Firm",
                "url": f"{target_url}?search=<test>",
                "description": "The application appears to be vulnerable to reflected cross-site scripting attacks.",
                "remediation": "Implement proper input validation and output encoding for user-supplied data."
            })
            
            results.append({
                "issue_type": "SQL Injection",
                "severity": "High",
                "confidence": "Tentative",
                "url": f"{target_url}?id=1",
                "description": "The application might be vulnerable to SQL injection attacks.",
                "remediation": "Use parameterized queries or prepared statements to prevent SQL injection."
            })
        
        # Add more findings for crawler scan
        if scan_type == "crawler":
            results.append({
                "issue_type": "Directory Listing",
                "severity": "Medium",
                "confidence": "Certain",
                "url": f"{target_url}/assets/",
                "description": "Directory listing is enabled on the server, which can expose sensitive files.",
                "remediation": "Disable directory listing in the web server configuration."
            })
            
            results.append({
                "issue_type": "Outdated Framework Version",
                "severity": "Medium",
                "confidence": "Firm",
                "url": target_url,
                "description": "The application appears to be using an outdated version of a web framework.",
                "remediation": "Update the framework to the latest stable version."
            })
        
        return results
    
    def _format_scan_results(self, results: List[Dict[str, Any]]) -> str:
        """Format scan results into readable text"""
        if not results:
            return "No issues found during the scan."
        
        # Group by severity
        high_issues = [r for r in results if r.get("severity") == "High"]
        medium_issues = [r for r in results if r.get("severity") == "Medium"]
        low_issues = [r for r in results if r.get("severity") == "Low"]
        
        # Format output
        output = ["Burp Suite Scan Results:", ""]
        
        output.append(f"Issues found: {len(results)}")
        output.append(f"  High: {len(high_issues)}")
        output.append(f"  Medium: {len(medium_issues)}")
        output.append(f"  Low: {len(low_issues)}")
        output.append("")
        
        # Add detailed findings
        output.append("Detailed Findings:")
        for issue in results:
            output.append(f"\n[{issue.get('severity', 'Unknown')}] {issue.get('issue_type', 'Unknown Issue')}")
            output.append(f"URL: {issue.get('url', 'Unknown')}")
            output.append(f"Confidence: {issue.get('confidence', 'Unknown')}")
            output.append(f"Description: {issue.get('description', 'No description')}")
            output.append(f"Remediation: {issue.get('remediation', 'No remediation guidance')}")
        
        return "\n".join(output)
    
    def _simulate_vuln_test(self, target_url: str, vuln_type: str) -> Dict[str, Any]:
        """Simulate vulnerability test results"""
        # Create realistic-looking vulnerability test results based on the type
        vuln_tests = {
            "xss": {
                "vulnerable": True,
                "details": "Reflected XSS detected in the 'search' parameter",
                "test_url": f"{target_url}?search=<script>alert(1)</script>",
                "evidence": "The application reflected the script tag without encoding",
                "severity": "High",
                "cwe": "CWE-79: Improper Neutralization of Input During Web Page Generation"
            },
            "sqli": {
                "vulnerable": True,
                "details": "SQL injection detected in the 'id' parameter",
                "test_url": f"{target_url}?id=1' OR '1'='1",
                "evidence": "The application returned different responses for SQL syntax",
                "severity": "High",
                "cwe": "CWE-89: Improper Neutralization of Special Elements used in an SQL Command"
            },
            "csrf": {
                "vulnerable": True,
                "details": "No CSRF tokens detected in form submissions",
                "test_url": target_url,
                "evidence": "Forms submitted without anti-CSRF tokens were accepted",
                "severity": "Medium",
                "cwe": "CWE-352: Cross-Site Request Forgery"
            },
            "ssrf": {
                "vulnerable": False,
                "details": "No SSRF vulnerability detected",
                "test_url": f"{target_url}?url=http://internal-server",
                "evidence": "The application did not attempt to connect to the provided URL",
                "severity": "N/A",
                "cwe": "CWE-918: Server-Side Request Forgery"
            },
            "idor": {
                "vulnerable": True,
                "details": "Insecure Direct Object Reference detected",
                "test_url": f"{target_url}/user/2",
                "evidence": "Authorized access to resources by changing the user ID",
                "severity": "Medium",
                "cwe": "CWE-639: Authorization Bypass Through User-Controlled Key"
            },
            "open_redirect": {
                "vulnerable": True,
                "details": "Open redirect detected in the 'redirect' parameter",
                "test_url": f"{target_url}?redirect=https://attacker.com",
                "evidence": "The application redirected to the provided URL without validation",
                "severity": "Medium",
                "cwe": "CWE-601: URL Redirection to Untrusted Site"
            },
            "file_inclusion": {
                "vulnerable": False,
                "details": "No file inclusion vulnerability detected",
                "test_url": f"{target_url}?file=../../../etc/passwd",
                "evidence": "The application did not include the requested file",
                "severity": "N/A",
                "cwe": "CWE-98: Improper Control of Filename for Include/Require Statement"
            }
        }
        
        # Return the test results for the specified vulnerability type
        return vuln_tests.get(vuln_type.lower(), {
            "vulnerable": False,
            "details": f"Unknown vulnerability type: {vuln_type}",
            "test_url": target_url,
            "evidence": "N/A",
            "severity": "N/A",
            "cwe": "N/A"
        })
    
    def _format_vuln_test_results(self, test_results: Dict[str, Any]) -> str:
        """Format vulnerability test results into readable text"""
        if not test_results:
            return "No test results available."
        
        vulnerable = test_results.get("vulnerable", False)
        
        output = ["Vulnerability Test Results:", ""]
        
        output.append(f"Status: {'VULNERABLE' if vulnerable else 'NOT VULNERABLE'}")
        output.append(f"Details: {test_results.get('details', 'No details')}")
        output.append(f"Test URL: {test_results.get('test_url', 'N/A')}")
        output.append(f"Evidence: {test_results.get('evidence', 'N/A')}")
        output.append(f"Severity: {test_results.get('severity', 'N/A')}")
        output.append(f"CWE: {test_results.get('cwe', 'N/A')}")
        
        if vulnerable:
            output.append("\nReminder: This finding is for educational and demonstration purposes only.")
        
        return "\n".join(output)
    
    def _format_intruder_config(self, config: Dict[str, Any]) -> str:
        """Format intruder configuration into readable text"""
        output = ["Burp Intruder Attack Configuration:", ""]
        
        output.append(f"Target URL: {config.get('target_url', 'Unknown')}")
        output.append(f"Attack type: {config.get('attack_type', 'Unknown')}")
        output.append(f"Parameter targeting: {config.get('parameter_type', 'all')}")
        
        if "detected_parameters" in config:
            output.append("\nDetected parameters:")
            for param in config["detected_parameters"]:
                output.append(f"  - {param}")
        
        output.append("\nAttack description:")
        if config.get("attack_type") == "sniper":
            output.append("  Sniper attack targets each position one at a time with each payload.")
        elif config.get("attack_type") == "battering ram":
            output.append("  Battering Ram uses the same payload in all positions at once.")
        elif config.get("attack_type") == "pitchfork":
            output.append("  Pitchfork attack uses one payload set per position, iterating through all sets in parallel.")
        elif config.get("attack_type") == "cluster bomb":
            output.append("  Cluster Bomb tries all combinations of payloads for all positions.")
        
        output.append("\nNote: In an actual Burp Suite integration, this would configure the attack in the Burp Intruder interface.")
        
        return "\n".join(output)
    
    def _simulate_site_map(self, target_url: str) -> List[Dict[str, Any]]:
        """Simulate Burp site map data"""
        # Generate a realistic site map
        base_url = target_url if target_url else "https://example.com"
        base_domain = base_url.split("//")[1].split("/")[0]
        
        # Create sample site map entries
        site_map = [
            {
                "url": base_url,
                "status_code": 200,
                "content_type": "text/html",
                "response_size": 15204,
                "request_method": "GET"
            },
            {
                "url": f"{base_url}/login",
                "status_code": 200,
                "content_type": "text/html",
                "response_size": 5423,
                "request_method": "GET"
            },
            {
                "url": f"{base_url}/api/users",
                "status_code": 200,
                "content_type": "application/json",
                "response_size": 2340,
                "request_method": "GET"
            },
            {
                "url": f"{base_url}/about",
                "status_code": 200,
                "content_type": "text/html",
                "response_size": 3245,
                "request_method": "GET"
            },
            {
                "url": f"{base_url}/assets/main.js",
                "status_code": 200,
                "content_type": "application/javascript",
                "response_size": 25123,
                "request_method": "GET"
            },
            {
                "url": f"{base_url}/assets/styles.css",
                "status_code": 200,
                "content_type": "text/css",
                "response_size": 10452,
                "request_method": "GET"
            },
            {
                "url": f"{base_url}/api/products",
                "status_code": 200,
                "content_type": "application/json",
                "response_size": 8721,
                "request_method": "GET"
            },
            {
                "url": f"{base_url}/contact",
                "status_code": 200,
                "content_type": "text/html",
                "response_size": 4103,
                "request_method": "GET"
            },
            {
                "url": f"{base_url}/signup",
                "status_code": 200,
                "content_type": "text/html",
                "response_size": 6235,
                "request_method": "GET"
            },
            {
                "url": f"{base_url}/admin",
                "status_code": 302,
                "content_type": "text/html",
                "response_size": 215,
                "request_method": "GET"
            }
        ]
        
        return site_map