# HYDRA Plugin Main File
# Provides an interface to run HYDRA application scans

from hydra_plugin.src.hydra_tools import run_hydra_scan

class HydraPlugin:
    def __init__(self):
        pass

    def scan(self, target, service, userlist, passlist, options=None):
        """
        Run a HYDRA scan with the given parameters.
        :param target: Target IP or hostname
        :param service: Service to scan (e.g., ssh, ftp)
        :param userlist: Path to username list
        :param passlist: Path to password list
        :param options: Additional HYDRA options (optional)
        :return: Scan output
        """
        return run_hydra_scan(target, service, userlist, passlist, options)
