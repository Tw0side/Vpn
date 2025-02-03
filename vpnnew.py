import subprocess as sub
import os
import sys

class VPNManager:
    def __init__(self):
        self.tor_service_name = "tor"
        self.tor_path = "/etc/tor/torrc.dynamic"
        self.tor_socksport = 10000
        self.tor_transport = 9070
        self.tor_dns_port = 5353
        self.non_tor_networks = ["192.168.0.0/16", "127.0.0.1/8"]
        self.tor_process = None

    def create_tor_config(self):
        """Dynamically create the Tor configuration file."""
        config = f"""
        VirtualAddrNetworkIPv4 10.192.0.0/10
        AutomapHostsOnResolve 1
        SocksPort {self.tor_socksport}
        TransPort {self.tor_transport}
        DNSPort {self.tor_dns_port}
        """
        try:
            with open(self.tor_path, "w") as file:
                file.write(config)
            print(f"Tor configuration file created at {self.tor_path}")
        except Exception as e:
            print(f"Failed to create Tor configuration: {e}")
            sys.exit(1)

    def start_vpn(self):
        """Start VPN service."""
        print("Starting VPN...")
        self._add_firewall_rules()
        print("Firewall rules added.")
        if self._start_tor_service():
            print("Tor service started successfully.")
            print("VPN is active.")
        else:
            print("Failed to start Tor. VPN not active.")

    def stop_vpn(self):
        """Stop VPN service."""
        print("Stopping VPN...")
        self._remove_firewall_rules()
        print("Firewall rules removed.")
        if self._stop_tor_service():
            print("Tor service stopped successfully.")
            print("VPN is inactive.")
        else:
            print("Failed to stop Tor service. Manual cleanup required.")

    def status_vpn(self):
        """Check VPN service status."""
        print("Checking VPN status...")
        if self._is_tor_process_running():
            print("VPN is active.")
        else:
            print("VPN is inactive.")

    def _start_tor_service(self):
        """Start the Tor service directly."""
        try:
            self.tor_process = sub.Popen(
                ["tor", "-f", self.tor_path],
                stdout=sub.PIPE,
                stderr=sub.PIPE,
            )
            # Check if Tor started successfully
            if self.tor_process.poll() is None:
                print("Tor process started.")
                return True
            else:
                print(f"Tor failed to start: {self.tor_process.stderr.read().decode()}")
                return False
        except FileNotFoundError:
            print("Error: Tor binary not found. Is it installed?")
            return False
        except Exception as e:
            print(f"Error starting Tor service: {e}")
            return False

    def _stop_tor_service(self):
        """Stop the Tor process."""
        try:
            if self.tor_process:
                self.tor_process.terminate()
                self.tor_process.wait()
                print("Tor process terminated.")
                return True
            else:
                print("No Tor process to stop.")
                return False
        except Exception as e:
            print(f"Error stopping Tor process: {e}")
            return False

    def _is_tor_process_running(self):
        """Check if the Tor process is running."""
        return self.tor_process and self.tor_process.poll() is None

    def _add_firewall_rules(self):
        """Add necessary iptables rules for VPN traffic."""
        print("Adding firewall rules...")
        try:
            sub.run(["sudo", "iptables", "-F"], check=True)
            sub.run(["sudo", "iptables", "-t", "nat", "-F"], check=True)

            # Exclude local networks before redirection
            for network in self.non_tor_networks:
                sub.run(["sudo", "iptables", "-t", "nat", "-I", "OUTPUT", "-d", network, "-j", "ACCEPT"], check=True)

            # Redirect TCP traffic to Tor
            sub.run(["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "tcp", "-m", "tcp", "--syn",
                     "-j", "REDIRECT", "--to-ports", str(self.tor_transport)], check=True)

            # Redirect UDP traffic (DNS) to Tor
            sub.run(["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "udp", "--dport", "53",
                     "-j", "REDIRECT", "--to-ports", str(self.tor_dns_port)], check=True)

            # Allow loopback traffic
            sub.run(["sudo", "iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"], check=True)
            sub.run(["sudo", "iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"], check=True)

        except sub.CalledProcessError as e:
            print(f"Error adding firewall rules: {e}")

    def _remove_firewall_rules(self):
        """Remove iptables rules."""
        print("Removing firewall rules...")
        try:
            sub.run(["sudo", "iptables", "-F"], check=True)
            sub.run(["sudo", "iptables", "-t", "nat", "-F"], check=True)
        except sub.CalledProcessError as e:
            print(f"Error removing firewall rules: {e}")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("This script must be run as root. Use 'sudo'.")
        sys.exit(1)

    vpn = VPNManager()
    vpn.create_tor_config()
    vpn.stop_vpn()
