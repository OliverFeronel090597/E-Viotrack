from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QTextEdit, QFrame, QPlainTextEdit, 
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from libs.DatabaseConnector import DatabaseConnector
from libs.Imagelabel import AutoImageLabel
from libs.ViolationTree import ViolationTree
from tabulate import tabulate

class HomePage(QWidget):
    def __init__(self, db: DatabaseConnector):
        super().__init__()
        self.db = db
        self.setObjectName("HomePage")
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.main_layout)

        self.init_top_row()

        self.init_violation_tree()

    def init_top_row(self):
        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        top_row.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.main_layout.addLayout(top_row)

        self.logo_label = AutoImageLabel(r"img/E-VioTrack.png", circle=True, size=(200, 200))
        top_row.addWidget(self.logo_label, alignment=Qt.AlignmentFlag.AlignTop)

        self.quote_card = QFrame()
        self.quote_card.setObjectName("QuoteCard")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(5)
        self.quote_card.setLayout(card_layout)

        self.quote_area = QTextEdit()
        self.quote_area.setObjectName("QuoteText")
        self.quote_area.setReadOnly(True)
        self.quote_area.setMinimumSize(500, 170)
        self.quote_area.viewport().setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        self.quote_area.setHtml("""
            <h2>E-Viotrack</h2>
            <p>“No escape, no excuses — violations get tagged.”</p>
            <p>“Drive smart. The system doesn’t blink.”</p>
            <p>“Every violation leaves a signal.”</p>
        """)
        card_layout.addWidget(self.quote_area)
        top_row.addWidget(self.quote_card, alignment=Qt.AlignmentFlag.AlignTop)

    def init_violation_tree(self):

        self.violation_layout = QHBoxLayout()
        self.main_layout.addLayout(self.violation_layout)
        self.violation_tree = ViolationTree()
        self.violation_layout.addWidget(self.violation_tree)

        self.delete_btn = QPushButton("Delete Selected Violation")
        self.delete_btn.setObjectName("DeleteViolationBtn")
        self.delete_btn.clicked.connect(self.violation_tree.remove_selected_violation)
        self.delete_btn.hide()
        print("[INFO] Delete button hide from Homepage class as it will not be use maybe in the functure")

        self.violation_layout.addWidget(self.delete_btn)

        self.violation_tree.driver_clicked.connect(self.on_driver_clicked)

        self.driver_details = QPlainTextEdit()
        self.driver_details.setObjectName("driver_details")

        self.violation_layout.addWidget(self.driver_details)

    def on_driver_clicked(self, driver_name: str):
        violations = self.db.get_all_violation_driver(driver_name)

        if not violations:
            self.driver_details.setPlainText("No violations found.")
            return

        # --- Monospaced font ---
        font = self.driver_details.font()
        font.setFamily("Courier New")  # Monospace
        font.setPointSize(10)
        self.driver_details.setFont(font)

        # Columns: Violation (5) and Date (7)
        headers = ["Violation", "Date"]
        col_indices = [4, 6]

        # Determine column widths (longest string in each column, including header)
        col_widths = []
        for i, idx in enumerate(col_indices):
            max_data_len = max(len(str(v[idx])) for v in violations) if violations else 0
            header_len = len(headers[i])
            col_widths.append(max(max_data_len, header_len) + 2)  # +2 padding

        # Helper functions
        def format_header_row():
            return "".join(headers[i].ljust(col_widths[i]) for i in range(len(headers)))

        def format_data_row(row):
            return "".join(str(row[idx]).ljust(col_widths[i]) for i, idx in enumerate(col_indices))

        # Build table
        lines = [format_header_row(), "-" * sum(col_widths)*2]
        for v in violations:
            lines.append(format_data_row(v))

        # Set text and scroll
        self.driver_details.setPlainText("\n".join(lines))
        self.driver_details.verticalScrollBar().setValue(
            self.driver_details.verticalScrollBar().maximum()
        )


    def handle_add_violation(self, rfid=None):
        #print(f"New RFID detected: {rfid}")
        if not rfid:
            return

        active_violations = self.db.get_active_violations_by_rfid(rfid)
        if not active_violations:
            return

        for violation in active_violations:
            self.violation_tree.add_violation(violation, on_top=False)