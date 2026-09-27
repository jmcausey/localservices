import os
import sys
import sqlite3
import threading
from datetime import datetime, timedelta
from flask import current_app
from scapy.all import ARP, Ether, srp, IP, TCP, sniff
# Explicitly import the database utility from the flaskr package
from flaskr.db import get_db 

TARGET_SUBNET = "192.168.1.0/24"  # Change this to match your local subnet layout

# Global tracking structures for the live sniffer background thread
CONNECTION_COUNTS = {}
SNIFFER_STARTED = False
TRACKING_LOCK = threading.Lock()


# ==========================================
# 1. LIVE MONITORING & PACKET SNIFFING
# ==========================================

def log_packet_to_db(db_path, src_ip, src_port, dst_ip, dst_port, status, message):
    """Inserts real-time sniffed packet logs directly via a raw connection path."""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            # Explicitly provide standard defaults for missing columns to prevent schema errors
            cursor.execute("""
                INSERT INTO network_logs (
                    timestamp, source_ip, source_port, dest_ip, dest_port, 
                    protocol, bytes_sent, bytes_received, status, message
                ) VALUES (DATETIME('now'), ?, ?, ?, ?, ?, 0, 0, ?, ?)
            """, (src_ip, src_port, dst_ip, dst_port, "TCP", status, message))
            conn.commit()
    except sqlite3.Error as e:
        print(f"[-] Background Sniffer DB Error: {e}")

def process_packet(packet, db_path):
    """Callback function to analyze real-time TCP flags and flag scans with memory resetting."""
    if packet.haslayer(IP) and packet.haslayer(TCP):
        src_ip = packet[IP].src
        src_port = int(packet[TCP].sport) if packet[TCP].sport is not None else None
        dst_ip = packet[IP].dst
        dst_port = int(packet[IP].dport) if packet[IP].dport is not None else None
        flags = packet[TCP].sprintf('%TCP.flags%')

        if flags == 'S':  # Inbound connection request
            current_time = datetime.now()
            
            with TRACKING_LOCK:
                # Retrieve or initialize the IP tracking record
                if src_ip not in CONNECTION_COUNTS:
                    CONNECTION_COUNTS[src_ip] = {"count": 0, "first_seen": current_time}
                
                record = CONNECTION_COUNTS[src_ip]
                
                # Reset window if the connection attempt is older than 5 minutes
                if current_time - record["first_seen"] > timedelta(minutes=5):
                    record["count"] = 1
                    record["first_seen"] = current_time
                else:
                    record["count"] += 1
                
                current_count = record["count"]

            status = "CONNECTED"
            message = f"Inbound connection attempt #{current_count}"
            
            if current_count > 15:
                status = "ALERT"
                message = f"Potential port scan detected! Count: {current_count} within window."
                print(f"[{status}] {src_ip} -> {message}")
            
            log_packet_to_db(db_path, src_ip, src_port, dst_ip, dst_port, status, message)

def start_continuous_monitoring(db_path):
    """Runs inside a background worker thread to parse connections persistently."""
    print(f"[*] Starting background network connection sniffer logging to: {db_path}")
    sniff(filter='tcp[tcpflags] & tcp-syn != 0', 
          prn=lambda pkt: process_packet(pkt, db_path), 
          store=0)


# ==========================================
# 2. LOCAL SUBNET ARP SCANNING
# ==========================================

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
        
    # Standardized execution to support both standard tuples and customized sqlite3.Row connections
    db.executemany(insert_query, log_entries)
    db.commit()
    
    db_path = current_app.config.get('DATABASE', 'flaskr Context DB')
    print(f"[+] Successfully logged {len(log_entries)} rows to database '{db_path}'.")


# ==========================================
# 3. CONTEXT INITIALIZATION PIPELINE
# ==========================================

def run_network_scan():
    """Wrapper function to be safely called inside an active flaskr application context."""
    global SNIFFER_STARTED
    check_privileges()
    
    # 1. Safely grab the database path from Flask config context to hand off to background sniffer
    db_path = current_app.config.get('DATABASE')
    
    # 2. Spin up the continuous thread ONLY once when the scheduler loop invokes this function
    if not SNIFFER_STARTED and db_path:
        sniffer_thread = threading.Thread(
            target=start_continuous_monitoring, 
            args=(db_path,), 
            daemon=True
        )
        sniffer_thread.start()
        SNIFFER_STARTED = True

    # 3. Proceed with the routine snapshot ARP Subnet scan
    active_hosts = scan_local_network(TARGET_SUBNET)
    log_hosts_to_db(active_hosts)

