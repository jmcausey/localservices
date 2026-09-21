Here is an itemized, object-oriented structural breakdown of flaskr/scanner.py.

### **Module: NetworkScannerModule**

A specialized network discovery and diagnostics module utilizing Scapy to perform ARP subnet scanning, process live host responses, and log activity metrics to SQLite.

#### **Constants & Global Configuration**

* **TARGET\_SUBNET**: Subnet target string ("192.168.1.0/24").

### **Service: PrivilegeValidator**

Execution guard verifying operating system permissions before hardware-level packet crafting.

#### **Functions**

* **check\_privileges()**  
  * Checks os.name \!= 'nt' and verifies POSIX root UID (os.getuid() \== 0).  
  * Terminal error output and process termination (sys.exit(1)) if root privileges are absent.

### **Component: ARPNetworkScanner**

Low-level network scanning engine utilizing Scapy frame generation and dispatch.

#### **Functions**

* **scan\_local\_network(subnet) \-\> List\[Dict\[str, str\]\]**  
  * **Frame Generation**: Crafts an Ethernet broadcast frame (Ether(dst="ff:ff:ff:ff:ff:ff")) stacked with an ARP request payload (ARP(pdst=subnet)).  
  * **Dispatch**: Calls Scapy's srp() method with a 2-second timeout to collect layer-2 responses.  
  * **Processing**: Iterates over answered packets to extract source IP (received.psrc) and hardware MAC addresses (received.hwsrc).  
  * **Returns**: Array of dictionaries containing target IP and MAC bindings.

### **Service: NetworkScanLogger**

Database integration component mapping network telemetry into standard SQLite database logs.

#### **Functions**

* **log\_hosts\_to\_db(hosts)**  
  * Retrieves active context database via get\_db().  
  * Generates timestamps formatted as YYYY-MM-DD HH:MM:SS.  
  * Maps discovered hosts into tuples with fields: timestamp, source\_ip (Host IP), source\_port (None), dest\_ip ("255.255.255.255"), dest\_port (None), protocol ("ARP"), bytes\_sent (42), bytes\_received (60), status ("RESPONDED"), and message ("Host is UP. MAC Address: \<mac\>").  
  * Executes bulk database insertion via db.executemany() and commits the transaction.

### **Service: ScannerTaskRunner**

Execution interface wrapper called by CLI commands or automated schedulers.

#### **Functions**

* **run\_network\_scan()**  
  * Orchestrates workflow: calls check\_privileges(), executes scan\_local\_network(TARGET\_SUBNET), and passes results to log\_hosts\_to\_db().  
  * Designed for execution within an active Flask application context (such as the flask scan-network CLI command).