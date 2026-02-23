DARK_THEME = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", "Malgun Gothic", sans-serif;
    font-size: 13px;
}
QSplitter::handle {
    background-color: #313244;
    width: 2px;
}
QListWidget {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 4px;
    outline: none;
}
QListWidget::item {
    padding: 8px 12px;
    border-radius: 4px;
    margin: 2px 0;
}
QListWidget::item:hover {
    background-color: #313244;
}
QListWidget::item:selected {
    background-color: #45475a;
}
QTextEdit, QPlainTextEdit {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 8px;
    color: #cdd6f4;
}
QLineEdit {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 8px 12px;
    color: #cdd6f4;
}
QLineEdit:focus {
    border-color: #89b4fa;
}
QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #74c7ec;
}
QPushButton:pressed {
    background-color: #89dceb;
}
QPushButton#removeBtn {
    background-color: #f38ba8;
    padding: 6px 16px;
    font-size: 12px;
    border-radius: 6px;
}
QPushButton#removeBtn:hover {
    background-color: #eba0ac;
}
QPushButton#downloadBtn {
    background-color: #a6e3a1;
    padding: 6px 16px;
    font-size: 12px;
}
QPushButton#downloadBtn:hover {
    background-color: #94e2d5;
}
QPushButton#openFolderBtn {
    background-color: #cba6f7;
    padding: 6px 16px;
    font-size: 12px;
}
QPushButton#openFolderBtn:hover {
    background-color: #b4befe;
}
QLabel#sectionLabel {
    color: #a6adc8;
    font-size: 11px;
    font-weight: bold;
    padding: 4px 0;
    text-transform: uppercase;
}
QLabel#titleLabel {
    color: #cba6f7;
    font-size: 16px;
    font-weight: bold;
    padding: 8px;
}
QProgressBar {
    border: 1px solid #313244;
    border-radius: 4px;
    text-align: center;
    background-color: #181825;
    color: #cdd6f4;
    height: 20px;
}
QProgressBar::chunk {
    background-color: #89b4fa;
    border-radius: 3px;
}
QScrollBar:vertical {
    background: #181825;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
    border-bottom: 1px solid #313244;
}
QMenuBar::item:selected {
    background-color: #313244;
}
QMenu {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #313244;
}
QMenu::item:selected {
    background-color: #313244;
}
QGroupBox {
    border: 1px solid #313244;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
    color: #a6adc8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}
"""

LIGHT_THEME = """
QMainWindow, QWidget {
    background-color: #eff1f5;
    color: #4c4f69;
    font-family: "Segoe UI", "Malgun Gothic", sans-serif;
    font-size: 13px;
}
QSplitter::handle {
    background-color: #ccd0da;
    width: 2px;
}
QListWidget {
    background-color: #ffffff;
    border: 1px solid #ccd0da;
    border-radius: 6px;
    padding: 4px;
    outline: none;
}
QListWidget::item {
    padding: 8px 12px;
    border-radius: 4px;
    margin: 2px 0;
}
QListWidget::item:hover {
    background-color: #e6e9ef;
}
QListWidget::item:selected {
    background-color: #ccd0da;
}
QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    border: 1px solid #ccd0da;
    border-radius: 6px;
    padding: 8px;
    color: #4c4f69;
}
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #ccd0da;
    border-radius: 6px;
    padding: 8px 12px;
    color: #4c4f69;
}
QLineEdit:focus {
    border-color: #1e66f5;
}
QPushButton {
    background-color: #1e66f5;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #2a7de1;
}
QPushButton#removeBtn {
    background-color: #d20f39;
    color: #ffffff;
    padding: 6px 16px;
    font-size: 12px;
    border-radius: 6px;
}
QPushButton#downloadBtn {
    background-color: #40a02b;
    color: #ffffff;
    padding: 6px 16px;
    font-size: 12px;
}
QPushButton#openFolderBtn {
    background-color: #8839ef;
    color: #ffffff;
    padding: 6px 16px;
    font-size: 12px;
}
QPushButton#openFolderBtn:hover {
    background-color: #7287fd;
}
QLabel#sectionLabel {
    color: #6c6f85;
    font-size: 11px;
    font-weight: bold;
    padding: 4px 0;
}
QLabel#titleLabel {
    color: #8839ef;
    font-size: 16px;
    font-weight: bold;
    padding: 8px;
}
QProgressBar {
    border: 1px solid #ccd0da;
    border-radius: 4px;
    text-align: center;
    background-color: #ffffff;
    height: 20px;
}
QProgressBar::chunk {
    background-color: #1e66f5;
    border-radius: 3px;
}
QScrollBar:vertical {
    background: #eff1f5;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #ccd0da;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QMenuBar {
    background-color: #e6e9ef;
    color: #4c4f69;
    border-bottom: 1px solid #ccd0da;
}
QMenuBar::item:selected {
    background-color: #ccd0da;
}
QMenu {
    background-color: #eff1f5;
    color: #4c4f69;
    border: 1px solid #ccd0da;
}
QMenu::item:selected {
    background-color: #ccd0da;
}
QGroupBox {
    border: 1px solid #ccd0da;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
    color: #6c6f85;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}
"""

THEMES = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
}
