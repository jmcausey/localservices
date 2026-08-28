import socket
import subprocess
import platform
import requests

TARGET_HOST = "api.openweathermap.org/data/2.5/weather"  # Replace with your target domain (e.g., example.com)
TARGET_URL = f"https://{TARGET_HOST}"

def check_ping(host):
    """Check if the server responds to a ping."""
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', host]
    return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

def check_dns(host):
    """Check if DNS can resolve the host IP address."""
    try:
        socket.gethostbyname(host)
        return True
    except socket.gaierror:
        return False

def check_http_status(url):
    """Check if a basic HTTP request goes through."""
    try:
        response = requests.get(url, timeout=5)
        return f"Success (Status: {response.status_code})"
    except requests.exceptions.RequestException as e:
        return f"Failed ({type(e).__name__})"

# Execute diagnostic tests
print("--- NETWORK DIAGNOSTICS ---")
print(f"1. Local DNS Resolution: {'PASSED' if check_dns(TARGET_HOST) else 'FAILED'}")
print(f"2. ICMP Ping to Server:  {'PASSED' if check_ping(TARGET_HOST) else 'FAILED (Blocked or Down)'}")
print(f"3. Isolated HTTP Test:   {check_http_status(TARGET_URL)}")
