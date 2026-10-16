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

## Run the system manually

Open three terminals in the project folder:

**Terminal 1 — primary**

```bash
python3 server.py
```

**Terminal 2 — backup monitor**

```bash
python3 udp_receiver.py
```

**Terminal 3 — client**

```bash
python3 client.py
```

Expected normal response: `Hello from PRIMARY!`

To simulate a primary failure, press **Ctrl+C** in Terminal 1. After the backup detects missed heartbeats and starts its TCP listener on port `5052`, run the client again. Expected response: `Hello from NEW PRIMARY!` The client also retries the backup if it has not promoted yet.

**Important:** Start the primary before the backup, or start them close together. This basic backup monitor can promote even if the primary has never been observed alive.

For standalone heartbeat testing, run `udp_receiver.py` and `udp_sender.py` instead of the primary. Stop the sender to simulate lost heartbeats. **Do not run `udp_sender.py` during a primary-failure test** because it can keep the backup from promoting.

## Automated testing

Run all tests from the project root:

```bash
python3 -m pytest -v
```

Run just the failure-injection tests:

```bash
python3 -m pytest tests/test_failover.py -v
```

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
