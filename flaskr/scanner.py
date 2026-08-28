import os
import sys
from datetime import datetime
from flask import current_app
from scapy.all import ARP, Ether, srp

# Explicitly import the database utility and your app factory
from flaskr.db import get_db 
from flaskr import create_app  # Assuming your factory function is named create_app

TARGET_SUBNET = "192.168.1.0/24"  # Change this to match your local subnet layout

def check_privileges():
    """Ensure the script is executed with root/administrator access."""
    if os.name != 'nt' and os.getuid() != 0:
        print("[-] Error: This script must be run with root privileges (sudo).")
        sys.exit(1)

def scan_local_network(subnet):
    """Performs an ARP scan on the local subnet to discover active hosts."""
    print(f"[*] Starting local network scan on subnet: {subnet}")

    ether_broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request = ARP(pdst=subnet)
    packet = ether_broadcast / arp_request

    answered_list, _ = srp(packet, timeout=2, verbose=False)

    discovered_hosts = []
    for sent, received in answered_list:
        discovered_hosts.append({
            "ip": received.psrc,
            "mac": received.hwsrc
        })

    print(f"[+] Scan finished. Found {len(discovered_hosts)} active hosts.")
    return discovered_hosts

def log_hosts_to_db(hosts):
    """Inserts discovered hosts using the active flaskr database connection context."""
    if not hosts:
        print("[*] No active hosts discovered to log.")
        return

    db = get_db()
 
    insert_query = """
    INSERT INTO network_logs (
        timestamp, source_ip, source_port, dest_ip, dest_port, protocol, bytes_sent, bytes_received, status, message
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entries = []
    
    for host in hosts:
        entry = (
            current_time,
            host["ip"],
            None,
            "255.255.255.255",
            None,
            "ARP",
            42,
            60,
            "RESPONDED",
            f"Host is UP. MAC Address: {host['mac']}"
        )
        log_entries.append(entry)
        
    db.executemany(insert_query, log_entries)
    db.commit()
    
    db_path = current_app.config.get('DATABASE', 'flaskr Context DB')
    print(f"[+] Successfully logged {len(log_entries)} rows to database '{db_path}'.")

def run_network_scan():
    """Wrapper function to be safely called inside an active flaskr application context."""
    check_privileges()
    active_hosts = scan_local_network(TARGET_SUBNET)
    log_hosts_to_db(active_hosts)

