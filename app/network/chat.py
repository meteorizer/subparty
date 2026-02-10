"""Chat message handling over the control TCP connection."""
from __future__ import annotations

import time

from app.core.models import ChatMessage
from app.network.protocol import make_chat


def create_chat_message(hostname: str, ip: str, text: str) -> tuple[dict, ChatMessage]:
    ts = time.time()
    msg = make_chat(hostname, ip, text, ts)
    chat = ChatMessage(sender_hostname=hostname, sender_ip=ip, text=text, timestamp=ts)
    return msg, chat


def parse_chat_message(data: dict) -> ChatMessage:
    return ChatMessage(
        sender_hostname=data["hostname"],
        sender_ip=data["ip"],
        text=data["text"],
        timestamp=data["timestamp"],
    )
