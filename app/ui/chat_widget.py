from __future__ import annotations

import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton

from app.core.models import ChatMessage


class ChatWidget(QWidget):
    message_sent = Signal(str)  # text

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        label = QLabel("CHAT")
        label.setObjectName("sectionLabel")
        layout.addWidget(label)

        self._display = QTextEdit()
        self._display.setReadOnly(True)
        layout.addWidget(self._display, 1)

        input_layout = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("Type a message...")
        self._input.returnPressed.connect(self._send)
        input_layout.addWidget(self._input, 1)

        self._send_btn = QPushButton("Send")
        self._send_btn.clicked.connect(self._send)
        input_layout.addWidget(self._send_btn)

        layout.addLayout(input_layout)

    def _send(self):
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self.message_sent.emit(text)

    def add_message(self, msg: ChatMessage):
        ts = time.strftime("%H:%M", time.localtime(msg.timestamp))
        self._display.append(
            f'<span style="color:#89b4fa;">[{ts}]</span> '
            f'<span style="color:#a6e3a1;font-weight:bold;">{msg.sender_hostname}</span>: '
            f'{msg.text}'
        )

    def add_system_message(self, text: str):
        ts = time.strftime("%H:%M")
        self._display.append(
            f'<span style="color:#6c7086;">[{ts}] {text}</span>'
        )
