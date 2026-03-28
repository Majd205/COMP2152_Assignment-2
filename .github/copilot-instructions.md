# Port Scanner Project — AI Coding Instructions

## Project Overview
This is a **Python-based network port scanner** (COMP2152 Assignment 2). It scans a target machine for open network ports using concurrent socket connections, stores results in SQLite, and demonstrates OOP with inheritance, threading, and unit testing patterns.

**Critical constraint:** Only scan `127.0.0.1` (localhost). Scanning other machines without permission is illegal.

## Architecture & Key Components

### Core Classes
- **`NetworkTool` (Base Class)**: Encapsulates target IP with private attribute (`__target`), property getter/setter for validation, and destructor logging
- **`PortScanner` (Subclass)**: Inherits from `NetworkTool`, adds `scan_results` list, threading lock, and scanning methods

### Threading Pattern
Ports are scanned **concurrently** via threads (not sequentially) because:
- Single-port timeout = 1 second → 1024 ports would take ~17 minutes if scanned one-at-a-time
- Threading reduces total scan time to ~1 timeout duration
- Uses `threading.Lock()` to safely append results from multiple threads: `self.lock.acquire()` before modifying `self.scan_results`

### Data Persistence
- `save_results(target, results)`: Writes scan results to SQLite `scan_history.db` with columns: `id, target, port, status, service, scan_date`
- `load_past_scans()`: Retrieves and displays historical scans
- Table auto-created on first use with `CREATE TABLE IF NOT EXISTS`

### Common Ports Mapping
`common_ports` dict (lines 17–31) maps standard ports to service names (e.g., `80: "HTTP"`). Used to label results.

## Workflow & Testing

### Running the Scanner
```bash
python3 assignment2_101513153.py
```
- Prompts for target IP (defaults to `127.0.0.1`)
- Prompts for start/end port range (1–1024)
- Validates input (integer, range, end ≥ start)
- Displays open ports and service names

### Running Tests
```bash
python3 test_assignment2_101513153.py
```
Tests cover:
- Scanner initialization (`target`, empty `scan_results`)
- `get_open_ports()` filtering logic
- `common_ports` dictionary mappings
- Target validation (setter rejects empty string, keeps previous value)

## Code Patterns & Conventions

### Naming Convention
- Main file: `assignment2_{STUDENT_ID}.py` (e.g., `assignment2_101513153.py`)
- Test file: `test_assignment2_{STUDENT_ID}.py`

### Exception Handling
- Socket errors in `scan_port()` use try-except-finally:
  - **try**: Attempt connection
  - **except**: Log errors, continue gracefully
  - **finally**: Always close socket to prevent resource leaks
- SQLite errors caught in `save_results()` and `load_past_scans()`

### Output/Logging
- Print system info on startup (`platform.python_version()`, `os.name`)
- Print status messages during execution ("Scanning...", "--- Scan Results ---")
- Print destructor messages (`__del__`) to track object cleanup

## Integration Points

### Socket Module
- `socket.AF_INET, socket.SOCK_STREAM`: TCP IPv4 socket
- `sock.settimeout(1)`: 1-second timeout per port
- `sock.connect_ex()`: Non-blocking connect, returns 0 if port open

### Threading
- Create threads with `threading.Thread(target=scan_port, args=(port,))`
- Use `.start()` to begin execution and `.join()` to wait for completion
- Lock-protected access: `acquire()`/`release()` or context managers

## Critical Implementation Details

1. **Property Decorator**: `@property` and `@target.setter` allow validation on assignment without exposing private `__target`
2. **Inheritance Benefits**: Subclass reuses `target` property, validation logic, and destructor without duplication
3. **Thread Safety**: All writes to `self.scan_results` must acquire lock to avoid race conditions
4. **Port Status**: `socket.connect_ex()` returns 0 for open, non-zero for closed
5. **Service Lookup**: Use `common_ports.get(port, "Unknown")` to safely map port to service name

## File Structure
```
assignment2_101513153.py        # Main implementation
test_assignment2_101513153.py   # Unit tests (unittest framework)
scan_history.db                 # SQLite database (created at runtime)
README.md                        # Submission instructions
Assignment 2 - Port Scanner...  # Full spec & rubric (HTML)
```

## Common Modifications
- Adjust timeout in `sock.settimeout()` for slower/faster networks
- Extend `common_ports` dict with additional port mappings
- Modify port range validation (currently 1–1024)
- Add result filtering (e.g., display only open ports)
