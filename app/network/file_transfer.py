"""TCP file transfer with chunked streaming, progress, and checksum verification."""
from __future__ import annotations

import hashlib
import os
import socket
import struct

from PySide6.QtCore import QThread, Signal

from app.network.protocol import CHUNK_SIZE, TRANSFER_PORT


def _log(prefix: str, msg: str):
    print(f"{prefix} {msg}", flush=True)


class FileTransferServer(QThread):
    """Listens for incoming file transfer requests and serves file data."""

    transfer_started = Signal(str, str)  # file_id, requester_ip

    LOG = "[TransferServer]"

    def __init__(self, shared_files_getter, parent=None):
        super().__init__(parent)
        self._running = False
        self._get_shared_files = shared_files_getter
        self._server_sock: socket.socket | None = None

    def run(self):
        _log(self.LOG, "Thread started")
        self._running = True
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind(("", TRANSFER_PORT))
        self._server_sock.listen(5)
        self._server_sock.settimeout(1.0)
        _log(self.LOG, f"Listening on TCP port {TRANSFER_PORT}")

        while self._running:
            try:
                conn, addr = self._server_sock.accept()
            except socket.timeout:
                continue
            except OSError as e:
                _log(self.LOG, f"Accept error (likely closed): {e}")
                break
            _log(self.LOG, f"Connection from {addr[0]}")
            try:
                self._serve_file(conn, addr[0])
            except Exception as e:
                _log(self.LOG, f"Serve error: {e}")
            finally:
                conn.close()

        _log(self.LOG, "Loop exited")
        try:
            self._server_sock.close()
        except OSError:
            pass
        _log(self.LOG, "Thread exiting")

    def _serve_file(self, conn: socket.socket, requester_ip: str):
        # Protocol: client sends 12-byte file_id + 8-byte offset
        header = _recv_exact(conn, 20)
        if not header:
            _log(self.LOG, "Failed to receive request header")
            return
        file_id = header[:12].decode("ascii")
        offset = struct.unpack("!Q", header[12:20])[0]
        _log(self.LOG, f"File request: id={file_id}, offset={offset}")

        self.transfer_started.emit(file_id, requester_ip)

        # find the file
        shared = self._get_shared_files()
        target = None
        for f in shared:
            if f.file_id == file_id:
                target = f
                break
        if not target or not target.file_path or not os.path.isfile(target.file_path):
            _log(self.LOG, f"File not found: {file_id}")
            conn.sendall(struct.pack("!Q", 0))
            return

        file_size = os.path.getsize(target.file_path)
        _log(self.LOG, f"Serving {target.filename} ({file_size} bytes)")
        sha = hashlib.sha256()
        with open(target.file_path, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                sha.update(chunk)

        conn.sendall(struct.pack("!Q", file_size) + sha.digest())

        with open(target.file_path, "rb") as f:
            f.seek(offset)
            remaining = file_size - offset
            while remaining > 0 and self._running:
                to_read = min(CHUNK_SIZE, remaining)
                chunk = f.read(to_read)
                if not chunk:
                    break
                conn.sendall(chunk)
                remaining -= len(chunk)
        _log(self.LOG, f"Serve complete: {file_id}")

    def stop(self):
        _log(self.LOG, "stop() called")
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
                _log(self.LOG, "Server socket closed")
            except OSError as e:
                _log(self.LOG, f"Server socket close error: {e}")
        _log(self.LOG, "Waiting for thread...")
        if not self.wait(3000):
            _log(self.LOG, "Thread did not stop in 3s, terminating")
            self.terminate()
            self.wait(1000)
        _log(self.LOG, "stop() done")


class FileDownloadTask(QThread):
    """Downloads a file from a peer."""

    progress = Signal(str, int, int)  # file_id, bytes_downloaded, total_bytes
    completed = Signal(str, str)  # file_id, saved_path
    failed = Signal(str, str)  # file_id, error_message
    cancelled_signal = Signal(str)  # file_id

    LOG = "[Download]"

    def __init__(self, file_id: str, filename: str, peer_ip: str, save_dir: str, offset: int = 0, parent=None):
        super().__init__(parent)
        self.file_id = file_id
        self.filename = filename
        self.peer_ip = peer_ip
        self.save_dir = save_dir
        self.offset = offset
        self._cancelled = False

    def cancel(self):
        _log(self.LOG, f"cancel() called: {self.file_id}")
        self._cancelled = True

    def run(self):
        _log(self.LOG, f"Thread started: {self.file_id} from {self.peer_ip}")
        save_path = os.path.join(self.save_dir, self.filename)
        temp_path = save_path + ".part"

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            sock.connect((self.peer_ip, TRANSFER_PORT))
            _log(self.LOG, f"Connected to {self.peer_ip}:{TRANSFER_PORT}")

            sock.sendall(self.file_id.encode("ascii") + struct.pack("!Q", self.offset))

            header = _recv_exact(sock, 40)
            if not header:
                self.failed.emit(self.file_id, "Failed to receive file header")
                _log(self.LOG, "Failed to receive header")
                return

            file_size = struct.unpack("!Q", header[:8])[0]
            if file_size == 0:
                self.failed.emit(self.file_id, "File not found on peer")
                _log(self.LOG, "File not found on peer")
                return

            expected_sha = header[8:40]
            remaining = file_size - self.offset
            downloaded = self.offset
            _log(self.LOG, f"Downloading {file_size} bytes")

            mode = "ab" if self.offset > 0 else "wb"
            with open(temp_path, mode) as f:
                while remaining > 0:
                    if self._cancelled:
                        sock.close()
                        self.cancelled_signal.emit(self.file_id)
                        _log(self.LOG, "Cancelled")
                        return
                    to_recv = min(CHUNK_SIZE, remaining)
                    chunk = sock.recv(to_recv)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    remaining -= len(chunk)
                    self.progress.emit(self.file_id, downloaded, file_size)

            sock.close()

            sha = hashlib.sha256()
            with open(temp_path, "rb") as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    sha.update(chunk)

            if sha.digest() != expected_sha:
                self.failed.emit(self.file_id, "Checksum mismatch")
                _log(self.LOG, "Checksum mismatch")
                return

            if os.path.exists(save_path):
                base, ext = os.path.splitext(save_path)
                i = 1
                while os.path.exists(f"{base}_{i}{ext}"):
                    i += 1
                save_path = f"{base}_{i}{ext}"

            os.rename(temp_path, save_path)
            self.completed.emit(self.file_id, save_path)
            _log(self.LOG, f"Completed: {save_path}")

        except Exception as e:
            self.failed.emit(self.file_id, str(e))
            _log(self.LOG, f"Error: {e}")

        _log(self.LOG, "Thread exiting")


class ControlServer(QThread):
    """TCP server for control messages (file lists, chat)."""

    file_list_received = Signal(str, str, list)  # hostname, ip, files (list of dicts)
    chat_received = Signal(dict)  # raw chat message dict

    LOG = "[ControlServer]"

    def __init__(self, port: int, parent=None):
        super().__init__(parent)
        self._port = port
        self._running = False
        self._server_sock: socket.socket | None = None

    def run(self):
        _log(self.LOG, "Thread started")
        self._running = True
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind(("", self._port))
        self._server_sock.listen(10)
        self._server_sock.settimeout(1.0)
        _log(self.LOG, f"Listening on TCP port {self._port}")

        while self._running:
            try:
                conn, addr = self._server_sock.accept()
            except socket.timeout:
                continue
            except OSError as e:
                _log(self.LOG, f"Accept error (likely closed): {e}")
                break
            try:
                self._handle_connection(conn, addr[0])
            except Exception as e:
                _log(self.LOG, f"Handle error: {e}")
            finally:
                conn.close()

        _log(self.LOG, "Loop exited")
        try:
            self._server_sock.close()
        except OSError:
            pass
        _log(self.LOG, "Thread exiting")

    def _handle_connection(self, conn: socket.socket, ip: str):
        from app.network.protocol import recv_message
        msg = recv_message(conn)
        if not msg:
            _log(self.LOG, f"Empty message from {ip}")
            return
        msg_type = msg.get("type")
        _log(self.LOG, f"Received {msg_type} from {ip}")
        if msg_type == "FILE_LIST":
            files = msg.get("files", [])
            self.file_list_received.emit(msg["hostname"], ip, files)
        elif msg_type == "CHAT":
            self.chat_received.emit(msg)

    def stop(self):
        _log(self.LOG, "stop() called")
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
                _log(self.LOG, "Server socket closed")
            except OSError as e:
                _log(self.LOG, f"Server socket close error: {e}")
        _log(self.LOG, "Waiting for thread...")
        if not self.wait(3000):
            _log(self.LOG, "Thread did not stop in 3s, terminating")
            self.terminate()
            self.wait(1000)
        _log(self.LOG, "stop() done")


def send_to_peer(ip: str, port: int, msg: dict):
    """Send a control message to a peer (fire-and-forget)."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, port))
        from app.network.protocol import send_message
        send_message(sock, msg)
        sock.close()
    except OSError:
        pass


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
