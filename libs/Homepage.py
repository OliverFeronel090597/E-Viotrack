from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QTextEdit, QFrame, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor
from libs.DatabaseConnector import DatabaseConnector
from libs.Imagelabel import AutoImageLabel
from libs.ViolationTree import ViolationTree

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

        # self.timer = QTimer()
        # self.timer.setInterval(5000)  # refresh every 5 seconds
        # self.timer.timeout.connect(self.update_driver_data)
        # self.timer.start()

    def init_top_row(self):
        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        top_row.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.main_layout.addLayout(top_row)

        self.logo_label = AutoImageLabel(r":/resources/E-VioTrack.png", circle=True, size=(200, 200))
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

        # self.delete_btn = QPushButton("Test")
        # self.delete_btn.setObjectName("DeleteViolationBtn")
        # self.delete_btn.clicked.connect(lambda: self.update_driver_data("Sarah Miller"))
        # #self.delete_btn.hide()
        # print("[INFO] Delete button hidden from Homepage class as it may be used in the future")
        # self.violation_layout.addWidget(self.delete_btn)

        self.violation_tree.driver_clicked.connect(self.on_driver_clicked)

        # --- Replace QPlainTextEdit with QTableWidget ---
        self.driver_table = QTableWidget()
        self.driver_table.setObjectName("driver_table")
        self.driver_table.setColumnCount(3)
        self.driver_table.setHorizontalHeaderLabels(["Name", "Violation", "Date"])
        self.driver_table.horizontalHeader().setStretchLastSection(True)
        self.driver_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.driver_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.driver_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.violation_layout.addWidget(self.driver_table)



    def handle_add_violation(self, rfid=None):
        if not rfid:
            return

        active_violations = self.db.get_active_violations_by_rfid(rfid)
        if not active_violations:
            return

        for violation in active_violations:
            self.violation_tree.add_violation(violation, on_top=False)

    def on_driver_clicked(self, driver_name: str):
        violations = self.db.get_all_violation_driver(driver_name)
        if not violations:
            self.driver_table.setRowCount(0)
            return

        self.driver_table.setRowCount(len(violations))

        for row_idx, violation in enumerate(violations):
            # Assuming idx 4 = Violation, idx 6 = Date
            name_item = QTableWidgetItem(driver_name)
            violation_item = QTableWidgetItem(str(violation[4]))
            date_item = QTableWidgetItem(str(violation[6]))

            # Alignments
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            violation_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Set items
            self.driver_table.setItem(row_idx, 0, name_item)
            self.driver_table.setItem(row_idx, 1, violation_item)
            self.driver_table.setItem(row_idx, 2, date_item)


        self.driver_table.resizeColumnsToContents()
        self.driver_table.resizeRowsToContents()

    def update_driver_data(self, driver_name: str = "Chris Wilson"):
        if not driver_name:
            print("$[WARN] No driver selected for update")
            return

        active_violations = self.db.get_active_violations_by_username(driver_name)
        self.violation_tree.update_driver_violations(driver_name, active_violations)
        print(f"$[INFO] Updated violations for {driver_name}")