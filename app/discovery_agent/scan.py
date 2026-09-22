"""
Discovery Agent - Host Discovery   basically port scannner

crazy stuff to remember:
nmap cant get your device's mac address



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
        mac = host_info["addresses"].get("mac")
        vendor = None

        if mac is not  None:
            vendor = host_info.get("vendor",{}).get(mac,"Unknown")

        hostname = host_info.hostname()

        if hostname == "":
            hostname = None

        results.append({
            "ip":host,
            "mac":mac,
            "vendor":vendor,
            "hostname":hostname,
            "status": host_info.state(),
        })       

    return results




def scan_ports(ip: str) -> dict:
    scanner = nmap.PortScanner()
    scanner.scan(hosts=ip, arguments="-sV -O")

    open_ports = []
    os_guess = None

    if ip in scanner.all_hosts():
        host_info = scanner[ip]
        os_matches = host_info.get("osmatch",[])

        if len(os_matches) > 0:
            best_match = os_matches[0]
            os_guess = best_match["name"]

        for _ in host_info.all_protocols():
            ports = host_info[_].keys()
            for port in ports:
                port_info = host_info[_][port]
                if port_info["state"] == "open":
                    open_ports.append({
                        "port":port,
                        "protocol":_,
                        "service": port_info.get("name","unknown"),
                        "product":port_info.get("product","Product is not recognisable"),
                        "version":port_info.get("version","Version is not recognisable"),
                    })
    return{
        "ip":ip,
        "open_ports":open_ports,
        "os_guess":os_guess,
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
