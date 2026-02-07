from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QWidget
import os
import re


class StylesheetModifier:
    def __init__(self, path,  parent: QWidget=None):
        self.file_path = path
        self.parent = parent
        self.last_mtime = None

        self.expanded_qss = None

        self.parent.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        # Timer for live reload
        self.timer = QTimer(parent)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.check_file)
        self.timer.start()

        # First load
        self.check_file()

    # ---------------------------------------------------------
    # Extracts variables from :root { --x: value; }
    # ---------------------------------------------------------
    def parse_root_variables(self, qss_text: str) -> dict:
        variables = {}

        root_match = re.search(r":root\s*\{([^}]*)\}", qss_text, re.MULTILINE)
        if not root_match:
            return variables

        root_block = root_match.group(1)

        for line in root_block.split(";"):
            if ":" in line:
                name, value = line.split(":", 1)
                name = name.strip()
                value = value.strip()
                if name.startswith("--"):
                    variables[name] = value

        return variables

    # ---------------------------------------------------------
    # Expands var(--x) inside stylesheet
    # ---------------------------------------------------------
    def expand_variables(self, qss_text: str, variables: dict) -> str:
        def repl(match):
            var_name = match.group(1)
            return variables.get(var_name, match.group(0))

        return re.sub(r"var\((--[a-zA-Z0-9\-]+)\)", repl, qss_text)

    # ---------------------------------------------------------
    # Check and reload stylesheet
    # ---------------------------------------------------------
    def check_file(self):
        if not os.path.exists(self.file_path):
            return

        current_mtime = os.path.getmtime(self.file_path)

        if self.last_mtime is None or current_mtime != self.last_mtime:
            self.last_mtime = current_mtime

            with open(self.file_path, "r", encoding="utf-8") as f:
                original_qss = f.read()

            # Extract tokens
            variables = self.parse_root_variables(original_qss)

            # Replace tokens
            self.expanded_qss = self.expand_variables(original_qss, variables)

            # Remove the :root block (Qt will choke on it)
            self.expanded_qss = re.sub(r":root\s*\{[^}]*\}", "", self.expanded_qss)

            # Apply
            self.parent.setStyleSheet(self.expanded_qss)

    def save_actual_qss(self, qss_path: str):
        if not hasattr(self, "expanded_qss"):
            return  # nothing to save yet

        with open(qss_path, "w", encoding="utf-8") as f:
            f.write(self.expanded_qss)
