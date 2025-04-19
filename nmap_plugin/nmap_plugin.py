import subprocess
import os
from semantic_kernel.functions import kernel_function

class NmapNetworkingToolsPlugin:
    @kernel_function(name="run_nmap_scan", description="Performs a network scan with nmap")
    def run_nmap_scan(self, target: str, scan_type: str = "-sV") -> str:
        if not self._is_valid_target(target):
            return "Error: Invalid target specification. Please provide a valid IP, hostname, or network range."
        allowed_options = ["-sV", "-sS", "-O", "-A", "-T4", "--top-ports", "-F"]
        if not any(opt in scan_type for opt in allowed_options):
            return "Error: Unsupported scan type. Please use one of: -sV, -sS, -O, -A, -T4, --top-ports, -F"
        try:
            cmd = ["nmap", scan_type, target]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                return f"Error running nmap: {result.stderr}"
            return self._format_nmap_output(result.stdout)
        except subprocess.TimeoutExpired:
            return "Error: Scan took too long and was terminated."
        except Exception as e:
            return f"Error running nmap scan: {str(e)}"

    @kernel_function(name="run_nmap_scan_live", description="Performs a live network scan with nmap and streams output line by line")
    def run_nmap_scan_live(self, target: str, scan_type: str = "-sV") -> str:
        import time
        if not self._is_valid_target(target):
            return "Error: Invalid target specification. Please provide a valid IP, hostname, or network range."
        allowed_options = ["-sV", "-sS", "-sU", "-O", "-A", "-T4", "--top-ports", "-F"]
        if not any(opt in scan_type for opt in allowed_options):
            return "Error: Unsupported scan type. Please use one of: -sV, -sS, -O, -A, -T4, --top-ports, -F, -sU"
        try:
            cmd = ["nmap", scan_type, target]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            output_lines = []
            for line in iter(process.stdout.readline, ''):
                if line:
                    output_lines.append(line.rstrip())
            process.stdout.close()
            process.wait()
            return "\n".join(output_lines)
        except Exception as e:
            return f"Error running live nmap scan: {str(e)}"

    @kernel_function(name="ping_host", description="Pings a host to check if it's online")
    def ping_host(self, host: str, count: int = 4) -> str:
        if not self._is_valid_target(host):
            return "Error: Invalid host specification"
        try:
            if os.name == 'nt':
                cmd = ["ping", "-n", str(count), host]
            else:
                cmd = ["ping", "-c", str(count), host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.stdout
        except Exception as e:
            return f"Error pinging host: {str(e)}"

    @kernel_function(name="traceroute", description="Traces the route to a destination host")
    def traceroute(self, host: str) -> str:
        if not self._is_valid_target(host):
            return "Error: Invalid host specification"
        try:
            if os.name == 'nt':
                cmd = ["tracert", host]
            else:
                cmd = ["traceroute", host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return result.stdout
        except Exception as e:
            return f"Error running traceroute: {str(e)}"

    def _is_valid_target(self, target: str) -> bool:
        if not target or len(target) > 100:
            return False
        disallowed = ["localhost", "127.0.0.1", "::1", "0.0.0.0", "169.254", "224.0.0"]
        if any(pattern in target for pattern in disallowed):
            return False
        return True

    def _format_nmap_output(self, output: str) -> str:
        important_sections = []
        if "PORT" in output:
            port_section = output[output.find("PORT"):]
            important_sections.append(port_section)
        else:
            important_sections.append(output)
        return "\n".join(important_sections)