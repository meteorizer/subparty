import sys
import threading

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def _log(msg: str):
    print(f"[Main] {msg}", flush=True)


def main():
    _log("Starting Sub Party")
    app = QApplication(sys.argv)
    app.setApplicationName("Sub Party")
    app.setOrganizationName("SubParty")

    window = MainWindow()
    window.show()

    # shutdown() runs inside the event loop, so threads can clean up properly
    app.aboutToQuit.connect(window.shutdown)

    _log("Entering event loop")
    exit_code = app.exec()

    _log(f"Event loop exited with code {exit_code}")
    _log(f"Remaining threads: {threading.active_count()}")
    for t in threading.enumerate():
        _log(f"  Thread: {t.name} (daemon={t.daemon}, alive={t.is_alive()})")

    _log("Calling sys.exit()")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
