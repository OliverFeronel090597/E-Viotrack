*# E-Viotrack

E-Viotrack is a desktop application for managing RFID-based vehicle tracking and violation management. It interfaces with long-range RFID readers via serial connection, validates scanned RFID tags against a local SQLite database, and displays real-time violation information for drivers.

## Overview

The system reads RFID tag IDs from long-range RFID hardware and queries a database to retrieve associated driver information and any active unpaid violations. Results are displayed immediately in an intuitive GUI based on PyQt6.

## Features

- **RFID Tag Reading**: Connects to long-range RFID readers via RS232/USB serial connection
- **Real-time Validation**: Instantly checks driver records and violation status in SQLite database
- **Violation Tracking**: Detects and displays active unpaid violations for scanned drivers
- **Driver Management**: Edit driver profiles, violation records, and violation types
- **Activity Logging**: Comprehensive logging of all scan activities and system events
- **User-Friendly GUI**: Modern PyQt6-based interface with animated transitions
- **Settings Management**: Configure RFID reader parameters and application behavior
- **Admin Panel**: Administrative interface for user and violation management

## Requirements

- Python 3.10 or newer
- PyQt6 6.7.0 or newer
- pyserial 3.6 or newer (for serial communication with RFID reader)

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd E_Viotrack
```

### 2. Create Virtual Environment (Recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python E_Viotrack.py
```

The application will launch with the main interface, displaying the home page with options to scan RFID tags, access admin features, or view logs.

## Project Structure

```
E-Viotrack/
├── E_Viotrack.py              # Main application entry point
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── db/                        # SQLite database files
├── libs/                      # Core application modules
├──
   ├── Homepage.py            # Home page interface
   ├── LogPage.py             # Activity logs display
   ├── Adminpage.py           # Admin panel
   ├── AdvancePage.py         # Advanced settings
   ├── ReadSerial.py          # RFID serial communication
   ├── DatabaseConnector.py   # SQLite database operations
   ├── NotificationManager.py # User notifications
   ├── CustomTable.py         # Custom table widget
   ├── Animatedstack.py       # Animated page transitions
   ├── GlobalVariable.py      # Global configuration
   ├── Settings.py            # RFID manager settings
   ├── Hasher.py              # Password hashing utilities
```

## Key Components

### Core Modules

- **E_Viotrack.py**: Main application window handling UI layout and navigation
- **ReadSerial.py**: Manages serial communication with RFID hardware
- **DatabaseConnector.py**: Handles all SQLite database operations for drivers and violations
- **NotificationManager.py**: Displays user notifications and alerts
- **Settings.py (RFIDManager)**: Manages RFID reader configuration and parameters

### UI Pages

- **HomePage.py**: Main interface for RFID scanning and results display
- **AdminPage.py**: Administrative interface for managing drivers and violations
- **LogPage.py**: View activity logs and scan history
- **AdvancePage.py**: Advanced configuration options
- **AboutDialog**: Application information and credits

### Database

The application uses SQLite to store:
- Driver/user profiles
- RFID tag mappings
- Violation records and types
- User activity logs

## Hardware Setup

The application is designed to work with long-range RFID readers connected via:
- **Serial Connection**: RS232 to USB adapter
- **Standard USB**: Direct USB connection to RFID reader

Ensure your RFID reader is properly connected and recognized by the system before launching the application.

## Configuration

Settings can be configured through:
1. **Settings Page**: Access from the main menu for RFID reader parameters
2. **Advanced Settings**: For detailed configuration options
3. **Admin Panel**: For database and user management

## Features in Detail

### Scanning Workflow
1. RFID reader detects a tag
2. Application reads the tag ID via serial communication
3. Database lookup matches tag to a driver record
4. Violation status is queried
5. Results are displayed with color indicators (pass/fail)
6. Event is logged to activity history

### Admin Functions
- Add/edit/delete driver records
- Manage violation types
- Record new violations
- Review activity logs
- User account management

## Support

For issues, bug reports, or feature requests, please refer to the project's issue tracker or documentation.
contact: oliver.feronel1@gmail.com

## License

Qt6 GUI Framework (LGPLv3): <a href="https://www.qt.io/licensing" style="color:#1E90FF;">Qt6 Licensing

## Author

Oliver Feronel
---

**Status**: Active Development
