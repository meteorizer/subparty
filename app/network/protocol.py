"""
Sub Party Network Protocol

All control messages are JSON, framed with 4-byte big-endian length prefix.

Message types:
  HELLO      - UDP broadcast for discovery
  BYE        - graceful disconnect
  FILE_LIST  - share file list with peers
  CHAT       - chat message
  FILE_REQ   - request file download
"""
from __future__ import annotations

import json
import socket
import struct
from typing import Any

DISCOVERY_PORT = 37710
CONTROL_PORT = 37711
TRANSFER_PORT = 37712

HEADER_SIZE = 4  # 4 bytes length prefix
CHUNK_SIZE = 65536  # 64KB chunks for file transfer


def encode_message(msg: dict[str, Any]) -> bytes:
    data = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    return struct.pack("!I", len(data)) + data


def decode_message(data: bytes) -> dict[str, Any]:
    return json.loads(data.decode("utf-8"))


def recv_message(sock: socket.socket) -> dict[str, Any] | None:
    header = _recv_exact(sock, HEADER_SIZE)
    if header is None:
        return None
    length = struct.unpack("!I", header)[0]
    if length > 10 * 1024 * 1024:  # 10MB sanity limit for control messages
        return None
    data = _recv_exact(sock, length)
    if data is None:
        return None
    return json.loads(data.decode("utf-8"))


def send_message(sock: socket.socket, msg: dict[str, Any]):
    sock.sendall(encode_message(msg))


def _recv_exact(sock: socket.socket, n: int) -> bytes | None:
    buf = bytearray()
    while len(buf) < n:
        try:
            chunk = sock.recv(n - len(buf))
        except (ConnectionError, OSError):
            return None
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)


def make_hello(hostname: str, control_port: int) -> dict:
    return {"type": "HELLO", "hostname": hostname, "control_port": control_port}


def make_bye(hostname: str) -> dict:
    return {"type": "BYE", "hostname": hostname}


def make_file_list(hostname: str, files: list[dict]) -> dict:
    return {"type": "FILE_LIST", "hostname": hostname, "files": files}


def make_chat(hostname: str, ip: str, text: str, timestamp: float) -> dict:
    return {"type": "CHAT", "hostname": hostname, "ip": ip, "text": text, "timestamp": timestamp}


def make_file_request(file_id: str, offset: int = 0) -> dict:
    return {"type": "FILE_REQ", "file_id": file_id, "offset": offset}
