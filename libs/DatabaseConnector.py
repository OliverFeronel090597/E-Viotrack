import sqlite3
import os
from typing import Optional, List, Dict, Any, Union
from warnings import deprecated
from datetime import datetime
import hashlib
import inspect

class DatabaseConnector:
    def __init__(self):
        """Initialize database connection with proper path handling."""
        self.base_path = "db"
        self.db_path = os.path.join(self.base_path, "RECORDS.db")
        self._ensure_database_directory()
        self._create_tables_if_not_exist()

    # ======================
    # DATABASE SETUP METHODS
    # ======================
    
    def _ensure_database_directory(self) -> None:
        """Ensure database directory exists or create it."""
        if not os.path.exists(self.base_path):
            try:
                os.makedirs(self.base_path)
                print(f"Created database directory at {self.base_path}")
            except PermissionError as e:
                raise PermissionError(f"Cannot create database directory: {e}")

    def connect(self) -> Optional[sqlite3.Connection]:
        """Establish database connection with error handling."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            return None

    def _create_tables_if_not_exist(self) -> None:
        """Initialize database schema."""
        schema = {
        "drivers": [
            "id INTEGER PRIMARY KEY AUTOINCREMENT",
            "driver_id TEXT UNIQUE NOT NULL",
            "rfid_serial TEXT UNIQUE NOT NULL",
            "full_name TEXT NOT NULL",
            "created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))",
            "vehicle TEXT NOT NULL"
        ],
        "system_users": [
            "id INTEGER PRIMARY KEY AUTOINCREMENT",
            "full_name TEXT NOT NULL",
            "user_name TEXT UNIQUE NOT NULL",
            "password TEXT NOT NULL",  # removed UNIQUE, multiple users can have same password
            "user_type TEXT NOT NULL"
        ],
        "violations": [
            "id INTEGER PRIMARY KEY AUTOINCREMENT",
            "user TEXT NOT NULL",
            "driver_name TEXT NOT NULL",
            "driver_id TEXT NOT NULL",
            "rfid_serial TEXT NOT NULL",
            "violation TEXT NOT NULL",
            "vehicle TEXT NOT NULL",
            "date TEXT NOT NULL",
            "amount REAL NOT NULL",
            "due_date TEXT NOT NULL",
            "paid INTEGER NOT NULL DEFAULT 0"  # BOOL replaced with INTEGER
        ],
        "violations_type": [
            "id INTEGER PRIMARY KEY AUTOINCREMENT",
            "violation_type TEXT UNIQUE NOT NULL",
            "amount REAL NOT NULL"
        ],
        "comports": [
            "port TEXT NOT NULL UNIQUE",
            "baudrate TEXT NOT NULL"
        ]
    }


        for table, columns in schema.items():
            cols = ", ".join(columns)
            self._execute(f"CREATE TABLE IF NOT EXISTS {table} ({cols})")

    # =====================
    # CORE QUERY EXECUTION
    # =====================
    
    def execute_query(
        
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch_one: bool = False,
        fetch_all: bool = False) -> Union[None, tuple, List[tuple]]:
        """Execute SQL query safely."""
        frame = inspect.stack()[1].frame
        cls = frame.f_locals.get('self').__class__.__name__ if 'self' in frame.f_locals else None
        func = inspect.stack()[1].function
        print(f"Called by: {cls}.{func}" if cls else f"Called by: {func}")
        
        with self.connect() as conn:
            if conn is None:
                return None
            cursor = conn.cursor()
            try:
                cursor.execute(query, params or ())
                if fetch_one:
                    return cursor.fetchone()
                if fetch_all:
                    return cursor.fetchall()
                conn.commit()
                return None
            except sqlite3.Error as e:
                print(f"Query execution error: {e}")
                return None

    def _execute(self, query: str):
        """Internal helper for table creation."""
        with self.connect() as conn:
            if conn:
                conn.execute(query)
                conn.commit()

    # =====================
    # SYSTEM USER FUNCTIONS
    # =====================

    def add_system_user(self, full_name: str, user_name: str, password: str, user_type: str) -> bool:
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        query = """
            INSERT INTO system_users (full_name, user_name, password, user_type)
            VALUES (?, ?, ?, ?)
        """
        result = self.execute_query(query, (full_name, user_name, password_hash, user_type))
        return result is None

    def get_system_user(self, user_name: str) -> Union[Dict[str, Any], None]:
        query = "SELECT id, full_name, user_name, password, user_type FROM system_users WHERE user_name=?"
        row = self.execute_query(query, (user_name,), fetch_one=True)
        if row:
            keys = ["id", "full_name", "user_name", "password", "user_type"]
            return dict(zip(keys, row))
        return None

    def authenticate_user(self, user_name: str, password: str) -> bool:
        user = self.get_system_user(user_name)
        if not user:
            return False
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        return password_hash == user["password"]

    def update_system_user(
        self,
        user_name: str,
        full_name: str = None,
        password: str = None,
        user_type: str = None
    ) -> bool:
        updates, params = [], []
        if full_name:
            updates.append("full_name=?")
            params.append(full_name)
        if password:
            updates.append("password=?")
            params.append(hashlib.sha256(password.encode('utf-8')).hexdigest())
        if user_type:
            updates.append("user_type=?")
            params.append(user_type)
        if not updates:
            return False
        query = f"UPDATE system_users SET {', '.join(updates)} WHERE user_name=?"
        params.append(user_name)
        result = self.execute_query(query, tuple(params))
        return result is None

    def delete_system_user(self, user_name: str) -> bool:
        query = "DELETE FROM system_users WHERE user_name=?"
        result = self.execute_query(query, (user_name,))
        return result is None

    def list_system_users(self) -> List[Dict[str, Any]]:
        query = "SELECT id, full_name, user_name, user_type FROM system_users"
        rows = self.execute_query(query, fetch_all=True)
        if not rows:
            return []
        keys = ["id", "full_name", "user_name", "user_type"]
        return [dict(zip(keys, row)) for row in rows]

    # =====================
    # DRIVER FUNCTIONS
    # =====================
    def add_driver(
        self,
        driver_id: str,
        rfid_serial: str,
        full_name: str,
        vehicle: str,
        created_at: str = None
    ) -> bool:
        created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
            INSERT INTO drivers (driver_id, rfid_serial, full_name, created_at, vehicle)
            VALUES (?, ?, ?, ?, ?)
        """
        result = self.execute_query(query, (driver_id, rfid_serial, full_name, created_at, vehicle))
        return result is None

    def update_driver(
        self,
        driver_id: str,
        rfid_serial: str = None,
        full_name: str = None,
        vehicle: str = None
    ) -> bool:
        updates, params = [], []
        if rfid_serial is not None:
            updates.append("rfid_serial=?")
            params.append(rfid_serial)
        if full_name is not None:
            updates.append("full_name=?")
            params.append(full_name)
        if vehicle is not None:
            updates.append("vehicle=?")
            params.append(vehicle)
        if not updates:
            return False
        params.append(driver_id)
        query = f"UPDATE drivers SET {', '.join(updates)} WHERE driver_id=?"
        result = self.execute_query(query, tuple(params))
        return result is None

    def load_drivers(self):
        query = "SELECT driver_id, rfid_serial, full_name, created_at, vehicle FROM drivers"
        return self.execute_query(query, fetch_all=True)

    def delete_driver(self, driver_id: str) -> bool:
        query = "DELETE FROM drivers WHERE driver_id=?"
        result = self.execute_query(query, (driver_id,))
        return result is None

    def select_driver(self, driver_id):
        query = "SELECT driver_id, rfid_serial, full_name, vehicle FROM drivers WHERE driver_id=?"
        return self.execute_query(query, (driver_id, ), fetch_one=True)

    # =====================
    # VIOLATION FUNCTIONS
    # =====================

    def add_violation(
        self,
        user: str,
        driver_name: str,
        driver_id: str,
        rfid_serial: str,
        violation: str,
        vehicle: str,
        date: str,
        amount: float,
        due_date: str,
        paid: int = 0
    ) -> bool:
        query = """
            INSERT INTO violations (
                user, driver_name, driver_id, rfid_serial,
                violation, vehicle, date, amount, due_date, paid
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        result = self.execute_query(query, (
            user, driver_name, driver_id, rfid_serial,
            violation, vehicle, date, amount, due_date, paid
        ))
        return result is None

    def update_violation(
        self,
        violation_id: int,
        user: str = None,
        violation: str = None,
        paid: int = None,
        due_date: str = None
    ) -> bool:
        updates, params = [], []
        if user is not None:
            updates.append("user=?")
            params.append(user)
        if violation is not None:
            updates.append("violation=?")
            params.append(violation)
        if paid is not None:
            updates.append("paid=?")
            params.append(paid)
        if due_date is not None:
            updates.append("due_date=?")
            params.append(due_date)
        if not updates:
            return False
        params.append(violation_id)
        query = f"UPDATE violations SET {', '.join(updates)} WHERE id=?"
        result = self.execute_query(query, tuple(params))
        return result is None

    def delete_violation(self, violation_id: str) -> bool:
        query = "DELETE FROM violations WHERE driver_id=?"
        result = self.execute_query(query, (violation_id,))
        return result is None

    def get_violation(self, violation_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM violations WHERE id=?"
        row = self.execute_query(query, (violation_id,), fetch_one=True)
        if row:
            keys = ["id", "user", "driver_name", "driver_id", "rfid_serial",
                    "violation", "vehicle", "date", "due_date", "paid"]
            return dict(zip(keys, row))
        return None


    def ger_all_violations(self):
        query = "SELECT * FROM violations"
        return self.execute_query(query, fetch_all=True)

    def get_active_violations_by_rfid(self, rfid_serial: str) -> List[Dict[str, Any]]:
        """
        Fetch all active (unpaid) violations for a specific RFID.
        Returns a list of dictionaries suitable for the ViolationTree.
        """
        query = """
            SELECT d.full_name, d.driver_id, d.rfid_serial, 
                v.violation, d.vehicle, v.date, v.due_date, v.amount, v.paid
            FROM violations v
            JOIN drivers d ON v.driver_id = d.driver_id
            WHERE v.paid = 0 AND d.rfid_serial = ?
            ORDER BY v.date DESC
        """
        rows = self.execute_query(query, (rfid_serial,), fetch_all=True)
        if not rows:
            return []

        keys = ["driver_name", "driver_id", "rfid_serial",
                "violation", "vehicle", "date", "due_date", "amount", "paid"]
        return [dict(zip(keys, row)) for row in rows]

# =====================
# VIOLATION_TYPE FUNCTIONS
# =====================
    def add_violation_type(self, violation_type: str, amount: float) -> bool:
        query = """
            INSERT INTO violations_type (violation_type, amount)
            VALUES (?, ?)
        """
        result = self.execute_query(query, (violation_type, amount))
        return result is None

    def update_violation_type(
        self,
        violation_id: int,
        violation_type: str = None,
        amount: float = None
    ) -> bool:
        updates, params = [], []

        if violation_type is not None:
            updates.append("violation_type=?")
            params.append(violation_type)

        if amount is not None:
            updates.append("amount=?")
            params.append(amount)

        if not updates:
            return False  # nothing to update

        params.append(violation_id)
        query = f"UPDATE violations_type SET {', '.join(updates)} WHERE id=?"
        result = self.execute_query(query, tuple(params))
        return result is None

    def delete_violation_type(self, violation_id: int) -> bool:
        query = "DELETE FROM violations_type WHERE id=?"
        result = self.execute_query(query, (violation_id,))
        return result is None

    def get_violation_type(self, violation_id: int):
        query = "SELECT id, violation_type, amount FROM violations_type WHERE id=?"
        row = self.execute_query(query, (violation_id,), fetch_one=True)
        if row:
            return {"id": row[0], "violation_type": row[1], "amount": row[2]}
        return None

    def list_violation_types(self):
        query = "SELECT id, violation_type, amount FROM violations_type ORDER BY violation_type"
        rows = self.execute_query(query, fetch_all=True)
        if not rows:
            return []

        return [
            {"id": r[0], "violation_type": r[1], "amount": r[2]}
            for r in rows
        ]

# =====================
# COMPORT FUNCTIONS
# =====================

    def add_comport(self, port: str, baudrate: str) -> bool:
        """
        Insert a new COM port entry.
        Returns True if successful, False on error (e.g., duplicate).
        """
        query = "INSERT OR REPLACE INTO comports (port, baudrate) VALUES (?, ?)"
        result = self.execute_query(query, (port, baudrate))
        return result is None

    def update_comport(self, port: str, baudrate: str) -> bool:
        """
        Update baudrate of an existing COM port.
        Returns True if successful, False if port does not exist.
        """
        query = "UPDATE comports SET baudrate=? WHERE port=?"
        result = self.execute_query(query, (baudrate, port))
        return result is None

    def delete_comport(self, port: str) -> bool:
        """
        Remove a COM port entry.
        Returns True if successful, False if port does not exist.
        """
        query = "DELETE FROM comports WHERE port=?"
        result = self.execute_query(query, (port,))
        return result is None

    def get_comport(self, port: str) -> Union[Dict[str, str], None]:
        """
        Fetch a single COM port entry by port name.
        Returns a dict with port and baudrate, or None if not found.
        """
        query = "SELECT port, baudrate FROM comports WHERE port=?"
        row = self.execute_query(query, (port,), fetch_one=True)
        if row:
            return {"port": row[0], "baudrate": row[1]}
        return None

    def list_comports(self) -> List[Dict[str, str]]:
        """
        List all COM ports stored in database.
        Returns a list of dicts.
        """
        query = "SELECT port, baudrate FROM comports ORDER BY port"
        rows = self.execute_query(query, fetch_all=True)
        if not rows:
            return []
        return [{"port": r[0], "baudrate": r[1]} for r in rows]
