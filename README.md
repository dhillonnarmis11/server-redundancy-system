# Server Redundancy Management System

A Python networking and system-testing portfolio project demonstrating a **primary/backup TCP service**, **UDP heartbeat monitoring**, **basic failure detection**, **automatic backup promotion**, **client retry/failover**, and **automated tests**.

> **Scope:** A local educational demonstration, not a production-ready high-availability or consensus system.

## Architecture

```text
                     TCP :5050 (normal operation)
TCP client ------------------------------------------> Primary server
    |                                                   |
    |                                           UDP ALIVE every 1 s
    |                                                   v
    |                                            Backup monitor
    |                                            UDP port :5051
    |                                                   |
    +---- TCP :5052 (after primary failure) ------------>|
                                                        v
                                            Promoted TCP server :5052
```

All programs currently run on `127.0.0.1` (localhost). The client prefers port `5050` and tries port `5052` if the primary is unavailable. The backup listens for `ALIVE` UDP datagrams and promotes itself after three consecutive 2-second receive timeouts (roughly six seconds without a heartbeat).

## Features

- IPv4 TCP request/response service on the primary (`server.py`)
- UDP heartbeats sent every second by a background thread
- Backup heartbeat monitoring and promotion (`udp_receiver.py`)
- Concurrent TCP client handling using Python threads
- Client connection timeout and bounded backup retries (`client.py`)
- Timestamped server logging
- Standalone UDP heartbeat simulator for isolated tests (`udp_sender.py`)
- Unit-level handler tests and process-level integration/failure-injection tests with `pytest`

## Requirements

- Python 3.10 or newer
- `pytest` for automated tests
- Local ports TCP `5050`, TCP `5052`, and UDP `5051` available

Install test dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## How to run the project

All commands below should be run **from the project root** (the folder containing `server.py`). You need Python 3.10+ and three terminal windows for manual testing.

### 1. Install the test dependency

```bash
python3 -m pip install -r requirements.txt
```

### 2. Run the complete system (three terminals)

**Terminal 1 — backup heartbeat receiver:**

```bash
python3 udp_receiver.py
```

The backup listens for UDP heartbeats on `127.0.0.1:5051`. **Start the primary promptly**: this simple monitor can promote itself if no heartbeats arrive for about six seconds, even if the primary was never started.

**Terminal 2 — primary TCP server and heartbeat sender:**

```bash
python3 server.py
```

The primary listens for TCP connections on port `5050` and sends UDP `ALIVE` heartbeats every second to port `5051`. Terminal 1 should show received heartbeats.

**Terminal 3 — TCP client:**

```bash
python3 client.py
```

Expected output includes:

```text
Connected to PRIMARY server!
PRIMARY says: Hello from PRIMARY!
```

The client sends one request and exits. Run it again to make another request.

### 3. Simulate primary failure and verify recovery

1. Keep `udp_receiver.py` running in Terminal 1.
2. Press **Ctrl+C** in Terminal 2 to stop `server.py`.
3. Immediately run `python3 client.py` in Terminal 3 again.
4. The backup should detect three consecutive two-second heartbeat timeouts and start a TCP listener on port `5052`. The client should retry and eventually receive `Hello from NEW PRIMARY!`.

The exact number of client retries depends on timing. The original primary must remain stopped for this test.

### 4. Run the standalone UDP sender (optional)

`udp_sender.py` is a **test utility**, not part of the normal three-terminal setup. To test heartbeat detection in isolation, stop all programs and run:

**Terminal 1:**

```bash
python3 udp_receiver.py
```

**Terminal 2:**

```bash
python3 udp_sender.py
```

Verify heartbeats are received, then press **Ctrl+C** in Terminal 2 to simulate heartbeat loss. **Do not run `udp_sender.py` during a primary-failure test**; it could keep the backup alive after the real primary stops.

### 5. Run automated tests

**Stop all manually started programs first**, so pytest can use ports `5050`, `5051`, and `5052` without conflicts.

From the project root, run **all tests**:

```bash
python3 -m pytest -v
```

Or run each test file separately:

```bash
python3 -m pytest tests/test_server.py -v
python3 -m pytest tests/test_failover.py -v
```

`test_server.py` checks individual server response handlers. `test_failover.py` starts real subprocesses, injects primary failure, and checks backup promotion and client recovery. The complete suite currently defines **six tests**; results must be verified on your own machine.

### 6. Port reference and troubleshooting

| Port | Protocol | Program | Purpose |
| --- | --- | --- | --- |
| `5050` | TCP | `server.py` | Original primary service |
| `5051` | UDP | `udp_receiver.py` | Receives heartbeat messages |
| `5052` | TCP | `udp_receiver.py` after promotion | Backup TCP service |

- **Address already in use:** Stop older server/receiver instances before retrying.
- **Connection refused:** Confirm the correct server is running and the client is using the correct port.
- **Backup promoted before primary started:** Restart the backup, then start the primary promptly.
- **Integration test port conflict:** Stop manual server processes before running pytest.

### Test coverage

| Test | Purpose |
| --- | --- |
| `test_primary_response` | Verify primary handler response using a local socket pair |
| `test_backup_response` | Verify backup handler response using a local socket pair |
| `test_primary_accepts_tcp_requests` | Verify real TCP primary communication |
| `test_heartbeat_keeps_backup_in_standby` | Verify received heartbeats and no premature promotion |
| `test_backup_promotes_after_primary_failure` | Stop primary and verify backup promotion and response |
| `test_client_uses_backup_after_failure` | Verify the actual client connects to promoted backup |

**Before running integration tests:** Stop any manually running `server.py`, `udp_receiver.py`, or `udp_sender.py` processes. The tests use the same fixed ports and should not share them with other applications. Tests intentionally stop the primary process; they clean up their own subprocesses afterward.

### Failure scenarios to test manually

1. Primary healthy: client uses TCP `5050`.
2. Primary stopped: backup eventually serves requests on TCP `5052`.
3. Both services stopped: client reports connection failures after bounded retries.
4. Multiple sequential clients after promotion: backup serves each request.
5. Backup started without primary: observe the premature-promotion limitation.

## Project files

| File | Responsibility |
| --- | --- |
| `server.py` | Primary TCP service and UDP heartbeat thread |
| `udp_receiver.py` | Backup heartbeat monitor and promoted TCP service |
| `udp_sender.py` | Standalone heartbeat simulator for testing |
| `client.py` | Primary-first client with backup retries |
| `tests/test_server.py` | Handler-level tests |
| `tests/test_failover.py` | Process-level integration and failure-injection tests |

## Known limitations

- **No distributed consensus or fencing:** A network interruption can lead to both processes believing they are primary (split brain).
- **No reliable leader election:** Promotion is based on missed UDP heartbeats, which may be lost even if the primary is healthy.
- **No automatic failback:** The promoted backup does not revert when the original primary returns.
- **Different service ports:** The client must know both addresses; no virtual IP or load balancer is used.
- **No in-flight request recovery:** The client opens a new connection; it does not replay or guarantee exactly-once processing of interrupted requests.
- **Simplified health checks:** Receiving heartbeats does not prove that the primary TCP service can accept requests.
- **Basic concurrency:** One thread per client, without a connection limit or graceful coordinated shutdown.
- **Local-only deployment:** Uses loopback networking; no authentication, encryption, or deployment configuration.

## Skills demonstrated

Python, TCP/IP, UDP, socket programming, threading, exception handling, heartbeat monitoring, fault injection, integration testing, `pytest`, process lifecycle management, logging, Git, and technical documentation.

## Future improvements

- Add a startup grace period and require at least one valid heartbeat before treating a missing heartbeat as failure.
- Add TCP health probes alongside heartbeat monitoring.
- Add an explicit server-state machine, fencing/lease mechanism, and safe leader-election design.
- Implement coordinated shutdown, structured metrics, and configurable addresses/ports.
- Test network delays, packet loss, and recovery under load.
