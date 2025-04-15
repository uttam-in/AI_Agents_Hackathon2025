# HYDRA Tools Implementation
import subprocess

def run_hydra_scan(
    target,
    service,
    userlist=None,
    passlist=None,
    username=None,
    password=None,
    port=None,
    tasks=None,
    verbose=False,
    very_verbose=False,
    output_file=None,
    stop_on_success=False,
    delay=None,
    additional_options=None
):
    """
    Executes a HYDRA scan with common options.
    :param target: Target IP or hostname
    :param service: Service to scan (e.g., ssh, ftp)
    :param userlist: Path to username list (optional)
    :param passlist: Path to password list (optional)
    :param username: Single username (optional)
    :param password: Single password (optional)
    :param port: Custom port (optional)
    :param tasks: Number of parallel tasks (optional)
    :param verbose: Verbose output (optional)
    :param very_verbose: Very verbose output (optional)
    :param output_file: Output to file (optional)
    :param stop_on_success: Stop after first found login (optional)
    :param delay: Delay between attempts in seconds (optional)
    :param additional_options: Additional HYDRA options (optional, string)
    :return: Output from HYDRA command
    """
    cmd = ['hydra']
    if userlist:
        cmd += ['-L', userlist]
    if passlist:
        cmd += ['-P', passlist]
    if username:
        cmd += ['-l', username]
    if password:
        cmd += ['-p', password]
    if port:
        cmd += ['-s', str(port)]
    if tasks:
        cmd += ['-t', str(tasks)]
    if verbose:
        cmd.append('-v')
    if very_verbose:
        cmd.append('-V')
    if output_file:
        cmd += ['-o', output_file]
    if stop_on_success:
        cmd.append('-f')
    if delay:
        cmd += ['-W', str(delay)]
    if additional_options:
        cmd.extend(additional_options.split())
    cmd += [target, service]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"HYDRA scan failed: {e.stderr}"
