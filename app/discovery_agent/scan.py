"""
Discovery Agent - Host Discovery   basically port scannner
"""

import sys
import json
import nmap

#this means taking subnet as a string and returnns a list of dicts
def discover_hosts(subnet: str) -> list[dict]:
    # this will not scan ports, it will mainly find hosts
    # which are live on the network nad give their MAC address and manufacturer

    scanner = nmap.PortScanner()

    scanner.scan(hosts=subnet, arguments="-sn")
    results = []  # list of discovered hosts
    for host in scanner.all_hosts():
        host_info = scanner[host]
        mac = None
        vendor = None

        if "mac" in host_info["addresses"]:
            mac = host_info["addresses"]["mac"]
        vendor = host_info.get("vendor", {}).get(mac, "Unknown") 

        results.append({
            "ip":host,
            "mac":mac,
            "vendor":vendor,
            "status":host_info.state(),
        })

    return results




def scan_ports(ip: str) -> dict:
    scanner = nmap.PortScanner()
    scanner.scan(hosts=ip, arguments="-sV")

    open_ports = []

    if ip in scanner.all_hosts():
        host_info = scanner[ip]

        for _ in host_info.all_protocols():
            ports = host_info[_].keys()
            for port in ports:
                port_info = host_info[proto][port]
                if port_info["state"] == "open":
                    open_ports.append({
                        "port": port,
                        "protocol": _,
                        "service": port_info.get("name", "unknown"),
                        "product": port_info.get("product", ""),
                        "version": port_info.get("version", ""),
                    })

    return {
        "ip": ip,
        "open_ports": open_ports,
    }      


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scan.py <subnet> [--ports]")
        print("  e.g. python scan.py 192.168.1.0/24")
        print("       python scan.py 192.168.1.0/24 --ports")
        sys.exit(1)
 
    subnet = sys.argv[1]
    do_port_scan = "--ports" in sys.argv
 
    print(f"Discovering hosts on {subnet} ...\n")
    hosts = discover_hosts(subnet)
    print(json.dumps(hosts, indent=2))
    print(f"\nFound {len(hosts)} live host(s).")
 
    if do_port_scan:
        print("\nScanning open ports on each host (this may take a bit longer)...\n")
        for h in hosts:
            port_results = scan_ports(h["ip"])
            print(json.dumps(port_results, indent=2))


    
        


    