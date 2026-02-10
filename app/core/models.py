from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field


@dataclass
class SharedFile:
    file_id: str
    filename: str
    size: int
    owner_ip: str
    owner_hostname: str
    file_path: str = ""  # local path, not shared over network

    @staticmethod
    def create(filename: str, size: int, owner_ip: str, owner_hostname: str, file_path: str = "") -> SharedFile:
        return SharedFile(
            file_id=uuid.uuid4().hex[:12],
            filename=filename,
            size=size,
            owner_ip=owner_ip,
            owner_hostname=owner_hostname,
            file_path=file_path,
        )

    def to_dict(self) -> dict:
        return {
            "file_id": self.file_id,
            "filename": self.filename,
            "size": self.size,
            "owner_ip": self.owner_ip,
            "owner_hostname": self.owner_hostname,
        }

    @staticmethod
    def from_dict(d: dict) -> SharedFile:
        return SharedFile(
            file_id=d["file_id"],
            filename=d["filename"],
            size=d["size"],
            owner_ip=d["owner_ip"],
            owner_hostname=d["owner_hostname"],
        )

    @property
    def size_display(self) -> str:
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 ** 2:
            return f"{self.size / 1024:.1f} KB"
        elif self.size < 1024 ** 3:
            return f"{self.size / 1024 ** 2:.1f} MB"
        else:
            return f"{self.size / 1024 ** 3:.2f} GB"


@dataclass
class Peer:
    hostname: str
    ip: str
    control_port: int
    last_seen: float = field(default_factory=time.time)
    shared_files: list[SharedFile] = field(default_factory=list)

    @property
    def is_alive(self) -> bool:
        return (time.time() - self.last_seen) < 10.0

    @property
    def display_name(self) -> str:
        return self.hostname

    def update_seen(self):
        self.last_seen = time.time()


@dataclass
class ChatMessage:
    sender_hostname: str
    sender_ip: str
    text: str
    timestamp: float = field(default_factory=time.time)
