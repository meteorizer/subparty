import os

from PySide6.QtCore import QSettings


class AppSettings:
    def __init__(self):
        self._settings = QSettings("SubParty", "SubParty")

    @property
    def download_folder(self) -> str:
        default = os.path.join(os.path.expanduser("~"), "Downloads", "SubParty")
        path = self._settings.value("download_folder", default)
        os.makedirs(path, exist_ok=True)
        return path

    @download_folder.setter
    def download_folder(self, path: str):
        self._settings.setValue("download_folder", path)

    @property
    def theme(self) -> str:
        return self._settings.value("theme", "dark")

    @theme.setter
    def theme(self, value: str):
        self._settings.setValue("theme", value)
