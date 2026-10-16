# end-to-end tests for the local primary/backup demonstration

import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

# find the main project folder even when pytest runs from another directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOST = "127.0.0.1"
PRIMARY_PORT = 5050
BACKUP_PORT = 5052


def port_is_open(port):
    # try connecting to a TCP port and return True if a server is listening
    try:
        with socket.create_connection((HOST, port), timeout=0.3):
            return True
    except OSError:
        return False


def wait_for_port(port, timeout=12):
    # keep checking until a server starts listening or the deadline expires
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if port_is_open(port):
            return True
        time.sleep(0.1)
    return False


def request(port, message=b"Test message"):
    # open a real TCP connection, send a message, and receive the response
    with socket.create_connection((HOST, port), timeout=2) as connection:
        connection.settimeout(2)
        connection.sendall(message)
        return connection.recv(1024)


def start_program(filename, output_file):
    # launch a Python program as a separate process
    return subprocess.Popen(
        [sys.executable, "-u", str(PROJECT_ROOT / filename)],
        cwd=PROJECT_ROOT,
        stdout=output_file,
        stderr=subprocess.STDOUT,
    )


def stop_program(process):
    # stop the process and make sure it cannot remain running after a test
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)


@pytest.fixture
def running_system(tmp_path):
    # start the primary first so the backup does not promote prematurely
    # use log files to avoid filling a subprocess output pipe
    with (tmp_path / "primary.log").open("w+") as primary_log, \
         (tmp_path / "backup.log").open("w+") as backup_log:
        primary = start_program("server.py", primary_log)
        backup = None
        try:
            if not wait_for_port(PRIMARY_PORT, timeout=5):
                pytest.fail("Primary did not start on TCP port 5050")

            backup = start_program("udp_receiver.py", backup_log)
            yield primary, backup, backup_log
        finally:
            if backup is not None:
                stop_program(backup)
            stop_program(primary)


def test_primary_accepts_tcp_requests(running_system):
    # verify that the primary returns the expected response over TCP
    assert request(PRIMARY_PORT) == b"Hello from PRIMARY!"


def test_heartbeat_keeps_backup_in_standby(running_system):
    # allow time for several heartbeat messages to reach the backup
    _, backup, backup_log = running_system
    time.sleep(3)
    backup_log.flush()
    backup_log.seek(0)
    log_text = backup_log.read()

    assert "Heartbeat received" in log_text
    assert backup.poll() is None
    assert not port_is_open(BACKUP_PORT)


def test_backup_promotes_after_primary_failure(running_system):
    # stop the primary and check whether the backup opens its TCP port
    primary, _, _ = running_system
    time.sleep(1)
    stop_program(primary)

    assert wait_for_port(BACKUP_PORT, timeout=10), "Backup did not promote"
    assert request(BACKUP_PORT) == b"Hello from NEW PRIMARY!"


def test_client_uses_backup_after_failure(running_system):
    # stop primary, wait for promotion, then run the actual client program
    primary, _, _ = running_system
    time.sleep(1)
    stop_program(primary)
    assert wait_for_port(BACKUP_PORT, timeout=10), "Backup did not promote"

    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "client.py")],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Connected to BACKUP server!" in result.stdout
    assert "Hello from NEW PRIMARY!" in result.stdout
