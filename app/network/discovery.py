"""UDP broadcast-based peer discovery for LAN."""
from __future__ import annotations

import json
import socket
import time

from PySide6.QtCore import QThread, Signal

from app.network.protocol import DISCOVERY_PORT, make_hello, make_bye

LOG_PREFIX = "[Discovery]"


def _log(msg: str):
    print(f"{LOG_PREFIX} {msg}", flush=True)


class DiscoveryService(QThread):
    """Broadcasts HELLO messages and listens for peers on UDP."""

    peer_discovered = Signal(str, str, int)  # hostname, ip, control_port
    peer_lost = Signal(str)  # ip

    def __init__(self, hostname: str, control_port: int, parent=None):
        super().__init__(parent)
        self._hostname = hostname
        self._control_port = control_port
        self._running = False
        self._peers: dict[str, float] = {}  # ip -> last_seen
        self._sock: socket.socket | None = None

    def run(self):
        _log("Thread started")
        self._running = True
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("", DISCOVERY_PORT))
        self._sock.settimeout(1.0)
        _log(f"Bound to UDP port {DISCOVERY_PORT}")

        last_broadcast = 0.0
        my_ips = self._get_local_ips()
        _log(f"Local IPs: {my_ips}")

        while self._running:
            now = time.time()

            # broadcast HELLO every 3 seconds
            if now - last_broadcast >= 3.0:
                hello = json.dumps(make_hello(self._hostname, self._control_port)).encode("utf-8")
                try:
                    self._sock.sendto(hello, ("<broadcast>", DISCOVERY_PORT))
                except OSError as e:
                    _log(f"Broadcast send error: {e}")
                last_broadcast = now

            # receive
            try:
                data, addr = self._sock.recvfrom(4096)
                ip = addr[0]
                if ip in my_ips:
                    continue
                msg = json.loads(data.decode("utf-8"))
                if msg.get("type") == "HELLO":
                    self._peers[ip] = now
                    self.peer_discovered.emit(msg["hostname"], ip, msg["control_port"])
                elif msg.get("type") == "BYE":
                    _log(f"Received BYE from {ip}")
                    if ip in self._peers:
                        del self._peers[ip]
                    self.peer_lost.emit(ip)
            except socket.timeout:
                pass
            except OSError as e:
                _log(f"Socket error (likely closed): {e}")
                break
            except json.JSONDecodeError:
                continue

            # check for dead peers
            dead = [ip for ip, ts in self._peers.items() if now - ts > 10.0]
            for ip in dead:
                _log(f"Peer timeout: {ip}")
                del self._peers[ip]
                self.peer_lost.emit(ip)

        _log("Loop exited, sending BYE")
        # send BYE before stopping
        try:
            bye_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            bye_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            bye_sock.sendto(
                json.dumps(make_bye(self._hostname)).encode("utf-8"),
                ("<broadcast>", DISCOVERY_PORT),
            )
            bye_sock.close()
            _log("BYE sent")
        except OSError as e:
            _log(f"BYE send error: {e}")

        _log("Thread exiting")

    def stop(self):
        _log("stop() called")
        self._running = False
        if self._sock:
            try:
                self._sock.close()
                _log("Socket closed")
            except OSError as e:
                _log(f"Socket close error: {e}")
        _log("Waiting for thread...")
        if not self.wait(3000):
            _log("Thread did not stop in 3s, terminating")
            self.terminate()
            self.wait(1000)
        _log("stop() done")

    @staticmethod
    def _get_local_ips() -> set[str]:
        ips = {"127.0.0.1"}
        try:
            hostname = socket.gethostname()
            for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
                ips.add(info[4][0])
        except OSError:
            pass
        return ips
