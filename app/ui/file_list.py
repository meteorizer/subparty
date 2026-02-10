from __future__ import annotations

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
        self.setStyleSheet("padding: 4px 0;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        info_layout = QVBoxLayout()
        name_label = QLabel(shared_file.filename)
        name_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(name_label)

        meta = shared_file.size_display
        if not is_mine:
            meta += f"  ·  {shared_file.owner_hostname}"
        meta_label = QLabel(meta)
        meta_label.setStyleSheet("font-size: 11px; color: #a6adc8;")
        info_layout.addWidget(meta_label)

        layout.addLayout(info_layout, 1)

        if is_mine:
            btn = QPushButton("✕")
            btn.setObjectName("removeBtn")
            btn.setToolTip("Remove from share list")
            btn.clicked.connect(lambda: self.remove_clicked.emit(shared_file.file_id))
            layout.addWidget(btn)
        else:
            btn = QPushButton("Download")
            btn.setObjectName("downloadBtn")
            btn.clicked.connect(
                lambda: self.download_clicked.emit(
                    shared_file.file_id, shared_file.filename, shared_file.owner_ip
                )
            )
            layout.addWidget(btn)


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
        self._my_layout.setSpacing(2)
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
        self._peer_layout.setSpacing(2)
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
