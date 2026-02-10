from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPixmap, QPainter, QBrush
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem


def _dot_icon(color: str, size: int = 12) -> QIcon:
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QBrush(QColor(color)))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(1, 1, size - 2, size - 2)
    painter.end()
    return QIcon(pix)


ONLINE_ICON = None
OFFLINE_ICON = None


def _get_online_icon():
    global ONLINE_ICON
    if ONLINE_ICON is None:
        ONLINE_ICON = _dot_icon("#a6e3a1")
    return ONLINE_ICON


def _get_offline_icon():
    global OFFLINE_ICON
    if OFFLINE_ICON is None:
        OFFLINE_ICON = _dot_icon("#6c7086")
    return OFFLINE_ICON


class PeerListWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("Sub Party")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        label = QLabel("PEERS")
        label.setObjectName("sectionLabel")
        layout.addWidget(label)

        self._list = QListWidget()
        layout.addWidget(self._list)

        self._peers: dict[str, QListWidgetItem] = {}  # ip -> item

    def add_or_update_peer(self, hostname: str, ip: str):
        if ip in self._peers:
            item = self._peers[ip]
            item.setText(f"{hostname}  ({ip})")
            item.setIcon(_get_online_icon())
        else:
            item = QListWidgetItem(_get_online_icon(), f"{hostname}  ({ip})")
            self._list.addItem(item)
            self._peers[ip] = item

    def remove_peer(self, ip: str):
        if ip in self._peers:
            item = self._peers[ip]
            item.setIcon(_get_offline_icon())

    def delete_peer(self, ip: str):
        if ip in self._peers:
            row = self._list.row(self._peers[ip])
            self._list.takeItem(row)
            del self._peers[ip]

    @property
    def peer_count(self) -> int:
        return self._list.count()
