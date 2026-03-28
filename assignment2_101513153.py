"""
Author: Mjd Arow
Assignment: #2
Description: Port Scanner — A tool that scans a target machine for open network ports
"""

import socket
import threading
import sqlite3
import os
import platform
import datetime

# Print Python version and OS info
print("Python Version:", platform.python_version())
print("Operating System:", os.name)

# Dictionary mapping common port numbers to their service names
common_ports = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    8080: "HTTP-Alt"
}


class NetworkTool:
    def __init__(self, target):
        self.__target = target

    # Q3: What is the benefit of using @property and @target.setter?
    # Using @property and @target.setter encapsulates access to the private
    # attribute self.__target, preventing direct modification from outside the class.
    # The setter lets us add validation logic (like rejecting empty strings) in one place.
    # This approach follows the principle of data hiding and makes the class safer and
    # easier to maintain than exposing the attribute directly.
    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, value):
        if value == "":
            print("Error: Target cannot be empty")
        else:
            self.__target = value

    def __del__(self):
        print("NetworkTool instance destroyed")


# Q1: How does PortScanner reuse code from NetworkTool?
# PortScanner inherits from NetworkTool using class PortScanner(NetworkTool),
# which means it automatically gets the target property, getter, setter, and
# destructor without rewriting them. For example, self.target in PortScanner
# directly uses the @property getter defined in NetworkTool, including its
# validation logic, because of this inheritance relationship.
class PortScanner(NetworkTool):
    def __init__(self, target):
        super().__init__(target)
        self.scan_results = []
        self.lock = threading.Lock()

    def __del__(self):
        print("PortScanner instance destroyed")
        super().__del__()

    def scan_port(self, port):
        # Q4: What would happen without try-except here?
        # Without try-except, if the target machine is unreachable or refuses
        # the connection, Python would raise an unhandled socket.error exception
        # and the entire program would crash immediately. This would stop all
        # remaining threads from completing and no scan results would be saved.
        # The try-except block ensures the scanner continues gracefully even
        # when individual ports are unreachable.
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.target, port))
            if result == 0:
                status = "Open"
            else:
                status = "Closed"
            service_name = common_ports.get(port, "Unknown")
            self.lock.acquire()
            self.scan_results.append((port, status, service_name))
            self.lock.release()
        except socket.error as e:
            print(f"Error scanning port {port}: {e}")
        finally:
            sock.close()

    def get_open_ports(self):
        return [result for result in self.scan_results if result[1] == "Open"]

    # Q2: Why do we use threading instead of scanning one port at a time?
    # Threading allows multiple ports to be scanned simultaneously rather than
    # waiting for each connection attempt to time out before starting the next.
    # Without threads, scanning 1024 ports with a 1-second timeout would take
    # over 17 minutes in the worst case. With threading, all ports are scanned
    # concurrently, reducing total scan time to roughly the length of one timeout.
    def scan_range(self, start_port, end_port):
        threads = []
        for port in range(start_port, end_port + 1):
            thread = threading.Thread(target=self.scan_port, args=(port,))
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()


def save_results(target, results):
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT,
            port INTEGER,
            status TEXT,
            service TEXT,
            scan_date TEXT
        )""")
        for result in results:
            port, status, service = result
            cursor.execute(
                "INSERT INTO scans (target, port, status, service, scan_date) VALUES (?, ?, ?, ?, ?)",
                (target, port, status, service, str(datetime.datetime.now()))
            )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")


def load_past_scans():
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scans")
        rows = cursor.fetchall()
        if not rows:
            print("No past scans found.")
        else:
            for row in rows:
                _, target, port, status, service, scan_date = row
                print(f"[{scan_date}] {target} : Port {port} ({service}) - {status}")
        conn.close()
    except sqlite3.Error:
        print("No past scans found.")


# ── Main Program ──────────────────────────────────────────────────────────────
if __name__ == "__main__":

    target = input("Enter target IP address (press Enter for 127.0.0.1): ").strip()
    if target == "":
        target = "127.0.0.1"

    start_port = None
    end_port = None

    while start_port is None:
        try:
            start_port = int(input("Enter start port (1-1024): "))
            if not (1 <= start_port <= 1024):
                print("Port must be between 1 and 1024.")
                start_port = None
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

    while end_port is None:
        try:
            end_port = int(input("Enter end port (1-1024): "))
            if not (1 <= end_port <= 1024):
                print("Port must be between 1 and 1024.")
                end_port = None
            elif end_port < start_port:
                print("End port must be greater than or equal to start port.")
                end_port = None
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

    scanner = PortScanner(target)
    print(f"\nScanning {target} from port {start_port} to {end_port}...")
    scanner.scan_range(start_port, end_port)

    open_ports = scanner.get_open_ports()
    print(f"\n--- Scan Results for {target} ---")
    for port, status, service in open_ports:
        print(f"Port {port}: Open ({service})")
    print("------")
    print(f"Total open ports found: {len(open_ports)}")

    save_results(target, scanner.scan_results)

    view_history = input("\nWould you like to see past scan history? (yes/no): ").strip().lower()
    if view_history == "yes":
        load_past_scans()

# Q5: New Feature Proposal
# I would add a Port Risk Classifier that categorizes each open port as HIGH,
# MEDIUM, or LOW risk using a nested if-statement. HIGH risk ports (21, 22, 23,
# 3389) are frequently targeted by attackers, MEDIUM risk ports (25, 110, 143,
# 3306) expose sensitive services, and everything else is LOW risk. This gives
# users an immediate security assessment alongside the scan results, using a list
# comprehension like: risk_report = [("HIGH" if p in [21,22,23,3389] else
# "MEDIUM" if p in [25,110,143,3306] else "LOW", p, s) for p, s, _ in open_ports]
# Diagram: See diagram_101513153.png in the repository root