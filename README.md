# Serial Data Logger

A Python script for continuous data logging from a serial sensor device with automatic file rotation and cross-platform support.

## Features

- **Serial Communication**: Reads data from a sensor via USB serial port at 921600 baud
- **Automatic File Rotation**: Creates new log files when size exceeds 150 MB (~2.5 hours of data)
- **Cross-Platform**: Works on both Windows (COM5) and Raspberry Pi (/dev/ttyUSB0)
- **Binary Logging**: Saves raw sensor data in `.bin` format with timestamped filenames
- **Continuous Operation**: Runs indefinitely until manually stopped

## Requirements

```
pyserial
keyboard (Windows only)
```

## Usage

1. Connect your sensor to the appropriate USB port (COM5 on Windows, /dev/ttyUSB0 on Linux/RPi)
2. Run the script:
   ```bash
   python ipr_sensor_logger.py
   ```
3. Data is saved to `./Logging_data/` directory with timestamped filenames (format: `YYYYMMDD_HH-MM-SS.bin`)
4. Stop the script with Ctrl+C

## Configuration

- `MAX_FILE_SIZE`: Maximum size per log file (default: 150 MB)
- `SAVE_FILE_EVERY_SIZE`: File size check interval (default: 100 KB)
- `USB_COM_NAME`: Serial port name (auto-detected based on platform)
- Baudrate: 921600 bps

## How It Works

1. Opens serial connection and sends `<scanmb-start>` command to sensor
2. Continuously reads data byte-by-byte from the serial port
3. Writes data to binary log file
4. Monitors file size and creates new files when limit is reached
5. Files are named with timestamp for easy organization