# E-Viotrack

E-Viotrack is a Python-based application designed to interface with long-range RFID readers and validate scanned RFID tags against a local SQLite database.

The system checks whether a driver or user associated with an RFID tag has any active unpaid violations and displays the result in real time.

## Requirments
- Python version 13.3 or newer
- PyQt6 or (PySide) semilar with minor code change its out UI builder
- pyserial enable out app to read COM's

## Features

- Connects to long-range RFID reader hardware  
- Reads and processes RFID tag IDs  
- Queries user/driver records from an SQLite (`.db`) database  
- Detects and displays active unpaid violations  
- Provides immediate visual feedback  
- Built with PyQt6 for the UI  

## Components

- **Python backend** for logic and database operations  
- **RFID hardware integration** (serial/TCP depending on reader model)  
- **SQLite database** for storing users and violations  
- **PyQt6 GUI** for display and interaction  

## Status

This document is the initial overview; more detailed documentation (API, schema, architecture) can be added once the project structure is finalized.
