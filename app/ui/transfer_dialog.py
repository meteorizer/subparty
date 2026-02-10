from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QScrollArea, QFrame,
)


class TransferItemWidget(QFrame):
    cancel_clicked = Signal(str)  # file_id

    def __init__(self, file_id: str, filename: str, parent=None):
        super().__init__(parent)
        self.file_id = file_id
        self.setFrameShape(QFrame.NoFrame)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        top = QHBoxLayout()
        self._name_label = QLabel(filename)
        self._name_label.setStyleSheet("font-weight: bold;")
        top.addWidget(self._name_label, 1)

        self._status_label = QLabel("Waiting...")
        self._status_label.setStyleSheet("font-size: 11px; color: #a6adc8;")
        top.addWidget(self._status_label)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("padding: 2px 8px; font-size: 11px; background-color: #f38ba8;")
        cancel_btn.clicked.connect(lambda: self.cancel_clicked.emit(file_id))
        self._cancel_btn = cancel_btn
        top.addWidget(cancel_btn)

        layout.addLayout(top)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        layout.addWidget(self._progress)

    def update_progress(self, downloaded: int, total: int):
        pct = int(downloaded * 100 / total) if total > 0 else 0
        self._progress.setValue(pct)

        if total < 1024 ** 2:
            dl_str = f"{downloaded / 1024:.0f} KB"
            tot_str = f"{total / 1024:.0f} KB"
        elif total < 1024 ** 3:
            dl_str = f"{downloaded / 1024 ** 2:.1f} MB"
            tot_str = f"{total / 1024 ** 2:.1f} MB"
        else:
            dl_str = f"{downloaded / 1024 ** 3:.2f} GB"
            tot_str = f"{total / 1024 ** 3:.2f} GB"

        self._status_label.setText(f"{dl_str} / {tot_str}  ({pct}%)")

    def mark_completed(self):
        self._progress.setValue(100)
        self._status_label.setText("Completed")
        self._status_label.setStyleSheet("font-size: 11px; color: #a6e3a1;")
        self._cancel_btn.setVisible(False)

    def mark_failed(self, error: str):
        self._status_label.setText(f"Failed: {error}")
        self._status_label.setStyleSheet("font-size: 11px; color: #f38ba8;")
        self._cancel_btn.setVisible(False)

    def mark_cancelled(self):
        self._status_label.setText("Cancelled")
        self._status_label.setStyleSheet("font-size: 11px; color: #fab387;")
        self._cancel_btn.setVisible(False)


class TransferPanel(QWidget):
    cancel_transfer = Signal(str)  # file_id

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self._label = QLabel("TRANSFERS")
        self._label.setObjectName("sectionLabel")
        self._label.setVisible(False)
        layout.addWidget(self._label)

        self._area = QScrollArea()
        self._area.setWidgetResizable(True)
        self._area.setVisible(False)
        self._container = QWidget()
        self._items_layout = QVBoxLayout(self._container)
        self._items_layout.setContentsMargins(0, 0, 0, 0)
        self._items_layout.setSpacing(4)
        self._items_layout.addStretch()
        self._area.setWidget(self._container)
        layout.addWidget(self._area)

        self._items: dict[str, TransferItemWidget] = {}

    def add_transfer(self, file_id: str, filename: str):
        if file_id in self._items:
            return
        self._label.setVisible(True)
        self._area.setVisible(True)
        item = TransferItemWidget(file_id, filename)
        item.cancel_clicked.connect(lambda fid: self.cancel_transfer.emit(fid))
        self._items[file_id] = item
        self._items_layout.insertWidget(self._items_layout.count() - 1, item)

    def update_progress(self, file_id: str, downloaded: int, total: int):
        if file_id in self._items:
            self._items[file_id].update_progress(downloaded, total)

    def mark_completed(self, file_id: str):
        if file_id in self._items:
            self._items[file_id].mark_completed()

    def mark_failed(self, file_id: str, error: str):
        if file_id in self._items:
            self._items[file_id].mark_failed(error)

    def mark_cancelled(self, file_id: str):
        if file_id in self._items:
            self._items[file_id].mark_cancelled()
