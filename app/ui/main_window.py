from __future__ import annotations

import os
import socket
import threading

from PySide6.QtCore import Qt, QUrl, QMimeData
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QWidget, QVBoxLayout,
    QMenu, QFileDialog, QApplication, QMessageBox,
)

from app.core.models import SharedFile, Peer, ChatMessage
from app.core.settings import AppSettings
from app.network.protocol import CONTROL_PORT, make_file_list, make_chat
from app.network.discovery import DiscoveryService
from app.network.file_transfer import (
    ControlServer, FileTransferServer, FileDownloadTask, send_to_peer,
)
from app.network.chat import create_chat_message, parse_chat_message
from app.ui.peer_list import PeerListWidget
from app.ui.file_list import FileListWidget
from app.ui.chat_widget import ChatWidget
from app.ui.transfer_dialog import TransferPanel
from app.ui.styles import THEMES

LOG_PREFIX = "[MainWindow]"


def _log(msg: str):
    print(f"{LOG_PREFIX} {msg}", flush=True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sub Party")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)
        self.setAcceptDrops(True)

        self._settings = AppSettings()
        self._hostname = socket.gethostname()
        self._my_ip = self._get_local_ip()
        self._peers: dict[str, Peer] = {}  # ip -> Peer
        self._my_shared_files: list[SharedFile] = []
        self._downloads: dict[str, FileDownloadTask] = {}

        self._setup_ui()
        self._setup_menu()
        self._setup_network()
        self._apply_theme()
        _log(f"Initialized: {self._hostname} ({self._my_ip})")

    # ── UI Setup ──────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)

        # left: peer list
        self._peer_list = PeerListWidget()
        self._peer_list.setMinimumWidth(220)
        self._peer_list.setMaximumWidth(320)
        splitter.addWidget(self._peer_list)

        # right: file list + transfer panel + chat
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_splitter = QSplitter(Qt.Vertical)

        # top: file list
        self._file_list = FileListWidget()
        self._file_list.file_removed.connect(self._on_file_removed)
        self._file_list.download_requested.connect(self._on_download_requested)
        right_splitter.addWidget(self._file_list)

        # bottom container: transfers + chat
        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        self._transfer_panel = TransferPanel()
        self._transfer_panel.cancel_transfer.connect(self._on_cancel_transfer)
        bottom_layout.addWidget(self._transfer_panel)

        self._chat = ChatWidget()
        self._chat.message_sent.connect(self._on_chat_send)
        bottom_layout.addWidget(self._chat, 1)

        right_splitter.addWidget(bottom)
        right_splitter.setSizes([350, 350])

        right_layout.addWidget(right_splitter)
        splitter.addWidget(right)
        splitter.setSizes([250, 750])

        main_layout.addWidget(splitter)

    def _setup_menu(self):
        menu_bar = self.menuBar()

        # Settings menu
        settings_menu = menu_bar.addMenu("Settings")

        dl_folder_action = QAction("Download Folder...", self)
        dl_folder_action.triggered.connect(self._change_download_folder)
        settings_menu.addAction(dl_folder_action)

        theme_menu = settings_menu.addMenu("Theme")
        dark_action = QAction("Dark", self)
        dark_action.triggered.connect(lambda: self._set_theme("dark"))
        theme_menu.addAction(dark_action)

        light_action = QAction("Light", self)
        light_action.triggered.connect(lambda: self._set_theme("light"))
        theme_menu.addAction(light_action)

        settings_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        settings_menu.addAction(quit_action)

    # ── Network Setup ─────────────────────────────────────────

    def _setup_network(self):
        _log("Setting up network...")

        # Control server (file lists, chat)
        self._control_server = ControlServer(CONTROL_PORT, parent=self)
        self._control_server.file_list_received.connect(self._on_file_list_received)
        self._control_server.chat_received.connect(self._on_chat_received)
        self._control_server.start()

        # File transfer server
        self._transfer_server = FileTransferServer(
            shared_files_getter=lambda: self._my_shared_files,
            parent=self,
        )
        self._transfer_server.start()

        # Discovery
        self._discovery = DiscoveryService(self._hostname, CONTROL_PORT, parent=self)
        self._discovery.peer_discovered.connect(self._on_peer_discovered)
        self._discovery.peer_lost.connect(self._on_peer_lost)
        self._discovery.start()

        self._chat.add_system_message(f"Started as {self._hostname} ({self._my_ip})")
        _log("Network setup complete")

    # ── Drag & Drop ───────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                self._add_shared_file(path)

    def _add_shared_file(self, path: str):
        size = os.path.getsize(path)
        sf = SharedFile.create(
            filename=os.path.basename(path),
            size=size,
            owner_ip=self._my_ip,
            owner_hostname=self._hostname,
            file_path=path,
        )
        self._my_shared_files.append(sf)
        self._file_list.add_my_file(sf)
        self._broadcast_file_list()

    def _on_file_removed(self, file_id: str):
        self._my_shared_files = [f for f in self._my_shared_files if f.file_id != file_id]
        self._broadcast_file_list()

    # ── File List Broadcasting ────────────────────────────────

    def _broadcast_file_list(self):
        files_data = [f.to_dict() for f in self._my_shared_files]
        msg = make_file_list(self._hostname, files_data)
        for peer in self._peers.values():
            send_to_peer(peer.ip, peer.control_port, msg)

    def _on_file_list_received(self, hostname: str, ip: str, files: list):
        shared = [SharedFile.from_dict(f) for f in files]
        if ip in self._peers:
            self._peers[ip].shared_files = shared
        self._file_list.update_peer_files(ip, hostname, shared)

    # ── File Download ─────────────────────────────────────────

    def _on_download_requested(self, file_id: str, filename: str, owner_ip: str):
        if file_id in self._downloads:
            return
        save_dir = self._settings.download_folder
        task = FileDownloadTask(file_id, filename, owner_ip, save_dir, parent=self)
        task.progress.connect(self._transfer_panel.update_progress)
        task.completed.connect(self._on_download_completed)
        task.failed.connect(self._on_download_failed)
        task.cancelled_signal.connect(self._transfer_panel.mark_cancelled)
        self._downloads[file_id] = task
        self._transfer_panel.add_transfer(file_id, filename)
        task.start()

    def _on_download_completed(self, file_id: str, saved_path: str):
        self._transfer_panel.mark_completed(file_id)
        self._downloads.pop(file_id, None)

    def _on_download_failed(self, file_id: str, error: str):
        self._transfer_panel.mark_failed(file_id, error)
        self._downloads.pop(file_id, None)

    def _on_cancel_transfer(self, file_id: str):
        task = self._downloads.get(file_id)
        if task:
            task.cancel()

    # ── Chat ──────────────────────────────────────────────────

    def _on_chat_send(self, text: str):
        msg_dict, chat_msg = create_chat_message(self._hostname, self._my_ip, text)
        self._chat.add_message(chat_msg)
        for peer in self._peers.values():
            send_to_peer(peer.ip, peer.control_port, msg_dict)

    def _on_chat_received(self, data: dict):
        chat_msg = parse_chat_message(data)
        self._chat.add_message(chat_msg)

    # ── Peer Discovery ────────────────────────────────────────

    def _on_peer_discovered(self, hostname: str, ip: str, control_port: int):
        is_new = ip not in self._peers
        self._peers[ip] = Peer(hostname=hostname, ip=ip, control_port=control_port)
        self._peers[ip].update_seen()
        self._peer_list.add_or_update_peer(hostname, ip)
        if is_new:
            self._chat.add_system_message(f"{hostname} joined")
            # send our file list to new peer
            if self._my_shared_files:
                files_data = [f.to_dict() for f in self._my_shared_files]
                msg = make_file_list(self._hostname, files_data)
                send_to_peer(ip, control_port, msg)

    def _on_peer_lost(self, ip: str):
        peer = self._peers.pop(ip, None)
        if peer:
            self._peer_list.remove_peer(ip)
            self._file_list.remove_peer_files(ip)
            self._chat.add_system_message(f"{peer.hostname} left")

    # ── Theme ─────────────────────────────────────────────────

    def _apply_theme(self):
        theme = self._settings.theme
        qss = THEMES.get(theme, THEMES["dark"])
        QApplication.instance().setStyleSheet(qss)

    def _set_theme(self, theme: str):
        self._settings.theme = theme
        self._apply_theme()

    # ── Settings ──────────────────────────────────────────────

    def _change_download_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder", self._settings.download_folder)
        if folder:
            self._settings.download_folder = folder

    # ── Close ─────────────────────────────────────────────────

    def closeEvent(self, event):
        _log("closeEvent: showing confirm dialog")
        reply = QMessageBox.question(
            self,
            "Sub Party",
            "Are you sure you want to quit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            _log("closeEvent: user confirmed quit")
            event.accept()
            QApplication.quit()
        else:
            _log("closeEvent: user cancelled quit")
            event.ignore()

    def shutdown(self):
        """Stop all network threads. Called from app.aboutToQuit signal."""
        _log("shutdown() called")
        _log(f"Active threads before shutdown: {threading.active_count()}")
        for t in threading.enumerate():
            _log(f"  Thread: {t.name} (daemon={t.daemon})")

        _log("Stopping discovery...")
        self._discovery.stop()
        _log("Stopping control server...")
        self._control_server.stop()
        _log("Stopping transfer server...")
        self._transfer_server.stop()

        _log(f"Cancelling {len(self._downloads)} downloads...")
        for file_id, task in self._downloads.items():
            _log(f"  Cancelling download: {file_id}")
            task.cancel()
            task.wait(2000)

        _log(f"Active threads after shutdown: {threading.active_count()}")
        for t in threading.enumerate():
            _log(f"  Thread: {t.name} (daemon={t.daemon})")
        _log("shutdown() done")

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _get_local_ip() -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except OSError:
            return "127.0.0.1"
