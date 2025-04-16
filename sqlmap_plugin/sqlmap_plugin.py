import subprocess
import os
from semantic_kernel.functions import kernel_function
from sqlmap_plugin.src.sqlmap_tools import SQLMapTools

class SQLMapToolsPlugin:
    def __init__(self, sqlmap_path: str = "sqlmap"):
        self.sqlmap_path = sqlmap_path
        self.sqlmap_tools = SQLMapTools(sqlmap_path)
    
    @kernel_function(name="run_sqlmap_scan", description="Performs a SQL injection scan on a target URL")
    def run_sqlmap_scan(self, url: str, params: str = "") -> str:
        """
        Run a basic SQLMap scan against a target URL
        
        Args:
            url: The target URL to scan for SQL injection vulnerabilities
            params: Additional SQLMap parameters (optional)
            
        Returns:
            The scan results as a string
        """
        return self.sqlmap_tools.run_sqlmap_scan(url, params)
    
    @kernel_function(name="run_sqlmap_advanced", description="Performs an advanced SQL injection scan with custom options")
    def run_sqlmap_advanced(self, url: str, options: str) -> str:
        """
        Run an advanced SQLMap scan with custom options
        
        Args:
            url: The target URL to scan
            options: Custom SQLMap options (e.g., "--forms --batch --dbs")
            
        Returns:
            The scan results as a string
        """
        return self.sqlmap_tools.run_sqlmap_advanced(url, options)
    
    @kernel_function(name="list_sqlmap_databases", description="Lists databases from a vulnerable SQL injection point")
    def list_sqlmap_databases(self, url: str) -> str:
        """
        List databases from a vulnerable SQL injection point
        
        Args:
            url: The vulnerable URL
            
        Returns:
            List of discovered databases
        """
        return self.sqlmap_tools.list_sqlmap_databases(url)
    
    @kernel_function(name="dump_sqlmap_tables", description="Dumps tables from a vulnerable SQL injection point")
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
        return self.sqlmap_tools.dump_sqlmap_tables(url, database, table)