import subprocess
import os
import re
from typing import List, Optional


class SQLMapTools:
    def __init__(self, sqlmap_path: str = "sqlmap"):
        self.sqlmap_path = sqlmap_path
        
    def run_sqlmap_scan(self, url: str, params: str = "") -> str:
        """
        Run a basic SQLMap scan against a target URL
        
        Args:
            url: The target URL to scan for SQL injection vulnerabilities
            params: Additional SQLMap parameters (optional)
            
        Returns:
            The scan results as a string
        """
        if not self._is_valid_url(url):
            return "Error: Invalid URL format. Please provide a valid URL."
        
        try:
            cmd = [self.sqlmap_path, "-u", url, "--batch"]
            
            # Add any additional parameters
            if params:
                cmd.extend(params.split())
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                return f"Error running SQLMap: {result.stderr}"
                
            return self._format_sqlmap_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            return "Error: SQLMap scan took too long and was terminated."
        except Exception as e:
            return f"Error running SQLMap scan: {str(e)}"
    
    def run_sqlmap_advanced(self, url: str, options: str) -> str:
        """
        Run an advanced SQLMap scan with custom options
        
        Args:
            url: The target URL to scan
            options: Custom SQLMap options (e.g., "--forms --batch --dbs")
            
        Returns:
            The scan results as a string
        """
        if not self._is_valid_url(url):
            return "Error: Invalid URL format. Please provide a valid URL."
            
        try:
            cmd = [self.sqlmap_path, "-u", url]
            
            # Add custom options
            if options:
                cmd.extend(options.split())
                
            # Always add batch mode if not included
            if "--batch" not in options:
                cmd.append("--batch")
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                return f"Error running SQLMap: {result.stderr}"
                
            return self._format_sqlmap_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            return "Error: SQLMap scan took too long and was terminated."
        except Exception as e:
            return f"Error running advanced SQLMap scan: {str(e)}"
    
    def list_sqlmap_databases(self, url: str) -> str:
        """
        List databases from a vulnerable SQL injection point
        
        Args:
            url: The vulnerable URL
            
        Returns:
            List of discovered databases
        """
        if not self._is_valid_url(url):
            return "Error: Invalid URL format. Please provide a valid URL."
            
        try:
            cmd = [self.sqlmap_path, "-u", url, "--batch", "--dbs"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                return f"Error listing databases: {result.stderr}"
                
            return self._extract_databases(result.stdout)
            
        except subprocess.TimeoutExpired:
            return "Error: Database listing took too long and was terminated."
        except Exception as e:
            return f"Error listing databases: {str(e)}"
    
    def dump_sqlmap_tables(self, url: str, database: str = "", table: str = "") -> str:
        """
        Dump tables from a vulnerable SQL injection point
        
        Args:
            url: The vulnerable URL
            database: Specific database to target (optional)
            table: Specific table to dump (optional)
            
        Returns:
            Dumped table data
        """
        if not self._is_valid_url(url):
            return "Error: Invalid URL format. Please provide a valid URL."
            
        try:
            cmd = [self.sqlmap_path, "-u", url, "--batch"]
            
            if database:
                cmd.extend(["-D", database])
                
            if table and database:
                cmd.extend(["-T", table, "--dump"])
            elif database:
                cmd.extend(["--tables"])
            else:
                cmd.extend(["--dbs"])
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                return f"Error dumping tables: {result.stderr}"
                
            return self._format_sqlmap_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            return "Error: Table dump took too long and was terminated."
        except Exception as e:
            return f"Error dumping tables: {str(e)}"
    
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
    
    def _format_sqlmap_output(self, output: str) -> str:
        """Format SQLMap output to highlight important findings"""
        important_sections = []
        
        # Extract vulnerability findings
        if "sqlmap identified the following injection point" in output:
            vuln_section = output.split("sqlmap identified the following injection point")[1]
            vuln_section = "sqlmap identified the following injection point" + vuln_section.split("\n\n")[0]
            important_sections.append("VULNERABILITY FOUND:\n" + vuln_section)
            
        # Extract database information
        if "available databases" in output:
            db_section = output.split("available databases")[1]
            db_section = "available databases" + db_section.split("\n\n")[0]
            important_sections.append("DATABASE INFORMATION:\n" + db_section)
            
        # Extract table information
        if "Database:" in output and "tables" in output:
            table_section = re.search(r'Database: .*\n.*tables.*\n-+\n([\s\S]*?)(\n\n|\Z)', output)
            if table_section:
                important_sections.append("TABLE INFORMATION:\n" + table_section.group(0))
                
        # Extract dumped data
        if "dumping data from table" in output:
            dump_section = re.search(r'dumping data from table.*\n-+\n([\s\S]*?)(\n\n|\Z)', output)
            if dump_section:
                important_sections.append("DUMPED DATA:\n" + dump_section.group(0))
                
        # If no important sections were found, return a summary
        if not important_sections:
            if "No injection point found" in output:
                return "No SQL injection vulnerabilities found in the target."
            else:
                # Return the last few lines with summary info
                return "\n".join(output.strip().split("\n")[-20:])
                
        return "\n\n".join(important_sections)
    
    def _extract_databases(self, output: str) -> str:
        """Extract database names from SQLMap output"""
        if "available databases" in output:
            db_section = output.split("available databases")[1]
            db_section = "Available databases:\n" + db_section.split("\n\n")[0]
            return db_section
        elif "No injection point found" in output:
            return "No SQL injection vulnerabilities found in the target."
        else:
            return "No database information found in the output."