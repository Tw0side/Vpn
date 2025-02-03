import subprocess as sub
import sys

class vpnmanager:
    def __init__(self):
        self.tor_service_name = "tor"
        self.tor_path = "/etc/tor/torrc.dynamic"
        self.tor_socksport =10000
        self.tor_transport = 9070
        self.tor_dns_port = 5353
        self.non_tor_networks = ["192.168.0.0/16", "127.0.0.1/8"]

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
        print("Starting VPN...")
        
        if self._start_tor_service():
            self._add_firewall_rules()
            print("Firewall rules added.")
            print("Firewall rules added.")
            print("VPN is active.")
        else:
            print("Failed to start Tor. VPN not active...")

    def stop_vpn(self):
        print("Stopping VPN...")
        
        if self._stop_tor_service():
            self._remove_firewall_rules()
            print("Firewall rules removed.")
            print("Tor service stopped successfully.")
            print("VPN is inactive.")
        else:
            print("Failed to stop Tor service. Manual cleanup required...")

    def status_vpn(self):
        print("Checking VPN status")
        if self._is_tor_service_running():
            print("VPN is active")
        else:
            print("VPN is inactive")

    def _start_tor_service(self):
        try:
            sub.run(["sudo", self.tor_service_name , "-f" ,self.tor_path], check=True)
            return True
        except sub.CalledProcessError as e:
            print(f"Error starting Tor service: {e}")
            return False

    def _stop_tor_service(self):
        try:
            sub.run(["sudo", "systemctl", "stop", self.tor_service_name], check=True)
            return True
        except sub.CalledProcessError as e:
            print(f"Error stopping Tor service: {e}")
            return False

    def _is_tor_service_running(self):
        try:
            result = sub.run(
                ["sudo", "systemctl", "is-active", "--quiet", self.tor_service_name],
                stdout=sub.PIPE,
                stderr=sub.PIPE,
            )
            return result.returncode == 0
        except FileNotFoundError:
            print("Error: systemctl command not found. Are you on a system without systemd?")
            return False
        except Exception as e:
            print(f"Error checking Tor service status: {e}")
            return False

    def _add_firewall_rules(self):
        print("Adding firewall rules...")
        try:
            sub.run(["sudo", "iptables", "-F"], check=True)
            sub.run(["sudo", "iptables", "-t", "nat", "-F"], check=True)

            # Redirect TCP traffic to Tor
            sub.run(["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "tcp",
                     "-m", "tcp", "--syn", "-j", "REDIRECT", "--to-ports", str(self.tor_transport)], check=True)

            # Redirect UDP traffic (DNS) to Tor
            sub.run(["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "udp", "--dport", "53",
                     "-j", "REDIRECT", "--to-ports", str(self.tor_dns_port)], check=True)

            # Exclude local networks from redirection
            for network in self.non_tor_networks:
                sub.run(["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-d", network, "-j", "ACCEPT"], check=True)

            # Allow loopback traffic
            sub.run(["sudo", "iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"], check=True)
            sub.run(["sudo", "iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"], check=True)

        except sub.CalledProcessError as e:
            print(f"Error adding firewall rules: {e}")

    def _remove_firewall_rules(self):
        print("Removing firewall rules...")
        try:
            sub.run(["sudo", "iptables", "-F"], check=True)
            sub.run(["sudo", "iptables", "-t", "nat", "-F"], check=True)
        except sub.CalledProcessError as e:
            print(f"Error removing firewall rules: {e}")

if __name__ == "__main__":
    vpn = vpnmanager()
    vpn.create_tor_config()
    vpn.stop_vpn()