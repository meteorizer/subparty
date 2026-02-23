from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QPushButton, QFrame,
)

from app.core.models import SharedFile


class FileItemWidget(QFrame):
    remove_clicked = Signal(str)  # file_id
    download_clicked = Signal(str, str, str)  # file_id, filename, owner_ip

    def __init__(self, shared_file: SharedFile, is_mine: bool, parent=None):
        super().__init__(parent)
        self._file = shared_file
        self.setFrameShape(QFrame.NoFrame)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        content = QWidget()
        layout = QHBoxLayout(content)
        layout.setContentsMargins(8, 8, 8, 8)

        info_layout = QVBoxLayout()
        name_label = QLabel(shared_file.filename)
        name_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(name_label)

        meta = shared_file.size_display
        if not is_mine:
            meta += f"  \u00b7  {shared_file.owner_hostname}"
        meta_label = QLabel(meta)
        meta_label.setStyleSheet("font-size: 11px; color: #a6adc8;")
        info_layout.addWidget(meta_label)

        layout.addLayout(info_layout, 1)

        if is_mine:
            btn = QPushButton("Dequeue")
            btn.setObjectName("removeBtn")
            btn.setToolTip("Remove from share list")
            btn.clicked.connect(lambda: self.remove_clicked.emit(shared_file.file_id))
            layout.addWidget(btn)
        else:
            self._download_btn = QPushButton("Download")
            self._download_btn.setObjectName("downloadBtn")
            self._download_btn.clicked.connect(
                lambda: self.download_clicked.emit(
                    shared_file.file_id, shared_file.filename, shared_file.owner_ip
                )
            )
            layout.addWidget(self._download_btn)

            self._open_folder_btn = QPushButton("Open folder")
            self._open_folder_btn.setObjectName("openFolderBtn")
            self._open_folder_btn.setVisible(False)
            layout.addWidget(self._open_folder_btn)

        outer.addWidget(content)

        # separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #313244;")
        separator.setFixedHeight(1)
        outer.addWidget(separator)

    def show_open_folder(self, folder_path: str):
        """Show the Open folder button after download completes."""
        if hasattr(self, "_open_folder_btn"):
            self._open_folder_btn.setVisible(True)
            self._open_folder_btn.clicked.connect(lambda: _open_folder(folder_path))


class FileListWidget(QWidget):
    file_removed = Signal(str)  # file_id
    download_requested = Signal(str, str, str)  # file_id, filename, owner_ip

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        label = QLabel("SHARED FILES")
        label.setObjectName("sectionLabel")
        layout.addWidget(label)

        # my files section
        self._my_label = QLabel("My Files")
        self._my_label.setStyleSheet("font-weight: bold; padding-top: 4px;")
        layout.addWidget(self._my_label)

        self._my_area = QScrollArea()
        self._my_area.setWidgetResizable(True)
        self._my_container = QWidget()
        self._my_layout = QVBoxLayout(self._my_container)
        self._my_layout.setContentsMargins(0, 0, 0, 0)
        self._my_layout.setSpacing(0)
        self._my_layout.addStretch()
        self._my_area.setWidget(self._my_container)
        layout.addWidget(self._my_area, 1)

        # peer files section
        self._peer_label = QLabel("Peer Files")
        self._peer_label.setStyleSheet("font-weight: bold; padding-top: 4px;")
        layout.addWidget(self._peer_label)

        self._peer_area = QScrollArea()
        self._peer_area.setWidgetResizable(True)
        self._peer_container = QWidget()
        self._peer_layout = QVBoxLayout(self._peer_container)
        self._peer_layout.setContentsMargins(0, 0, 0, 0)
        self._peer_layout.setSpacing(0)
        self._peer_layout.addStretch()
        self._peer_area.setWidget(self._peer_container)
        layout.addWidget(self._peer_area, 1)

        self._my_items: dict[str, FileItemWidget] = {}
        self._peer_items: dict[str, FileItemWidget] = {}

    def add_my_file(self, shared_file: SharedFile):
        if shared_file.file_id in self._my_items:
            return
        item = FileItemWidget(shared_file, is_mine=True)
        item.remove_clicked.connect(self._on_remove)
        self._my_items[shared_file.file_id] = item
        self._my_layout.insertWidget(self._my_layout.count() - 1, item)

    def remove_my_file(self, file_id: str):
        if file_id in self._my_items:
            widget = self._my_items.pop(file_id)
            self._my_layout.removeWidget(widget)
            widget.deleteLater()

    def _on_remove(self, file_id: str):
        self.remove_my_file(file_id)
        self.file_removed.emit(file_id)

    def update_peer_files(self, peer_ip: str, peer_hostname: str, files: list[SharedFile]):
        # remove old entries for this peer
        to_remove = [fid for fid, w in self._peer_items.items() if w._file.owner_ip == peer_ip]
        for fid in to_remove:
            widget = self._peer_items.pop(fid)
            self._peer_layout.removeWidget(widget)
            widget.deleteLater()

        # add new
        for f in files:
            item = FileItemWidget(f, is_mine=False)
            item.download_clicked.connect(
                lambda fid, fn, oip: self.download_requested.emit(fid, fn, oip)
            )
            self._peer_items[f.file_id] = item
            self._peer_layout.insertWidget(self._peer_layout.count() - 1, item)

    def remove_peer_files(self, peer_ip: str):
        to_remove = [fid for fid, w in self._peer_items.items() if w._file.owner_ip == peer_ip]
        for fid in to_remove:
            widget = self._peer_items.pop(fid)
            self._peer_layout.removeWidget(widget)
            widget.deleteLater()

    def mark_download_completed(self, file_id: str, saved_path: str):
        """Show Open folder button on the peer file item after download."""
        if file_id in self._peer_items:
            folder = os.path.dirname(saved_path)
            self._peer_items[file_id].show_open_folder(folder)


def _open_folder(folder_path: str):
    """Open a folder in the system file manager."""
    if sys.platform == "win32":
        os.startfile(folder_path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", folder_path])
    else:
        subprocess.Popen(["xdg-open", folder_path])
