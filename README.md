# IPR Sensor Interface

A Python-based command-line interface for communicating with and logging data from IPR sensors via serial connection.

## Documentation
- [Installation Manual](Docs/WiFi_Instructions_rev2.2.docx)
- [User Manual](Docs/USER_MANUAL.md)


## Features

- **Serial Communication**: Automatic port detection and connection management
- **Sensor Control**: Initialize, configure, and control sensor operations
- **Data Logging**: Continuous background logging of sensor data to binary files
- **Time Management**: Get and set sensor internal time
- **Tare Operations**: Apply zero-point calibration
- **Name Configuration**: Read and modify sensor identification

## Requirements

- Python 3.6+
- PySerial library

### Installation

```bash
pip install pyserial
```

## Project Structure

```
├── ipr_sensor.py              # Main entry point and command interface
├── ipr_sensor_serial.py       # Serial port communication wrapper
├── ipr_sensor_command.py      # Sensor command protocols
└── ipr_sensor_logging.py      # Background data logging thread
```

## Quick Start

1. Connect your IPR sensor via serial (USB or other)
2. Run the main script:
   ```bash
   python ipr_sensor.py
   ```
3. Select your serial port from the list
4. Use the interactive command menu (type `menu` or `?`)

## Available Commands

| Command | Description |
|---------|-------------|
| `menu` or `?` | Display command menu |
| `init` | List sensor information, name, and time |
| `get_material` | Display the sensor's material |
| `get_name` | Display the sensor's name |
| `set_name` | Change the sensor's name |
| `set_tare` | Apply a new tare (zero calibration) |
| `get_time` | Display the sensor's internal time |
| `set_time` | Change the sensor's internal time |
| `start_recording` | Start recording sensor data to a BIN file |
| `stop_recording` | Stop the sensor's recording |

## Usage Examples

### Initialize Sensor
```
> init
```
This will display sensor information including name and current time.

### Set Sensor Time
```
> set_time
Enter date and time in the following format yyyy-mm-dd-hh-mm: 2024-12-10-14-30
```

### Start Data Recording
```
> start_recording
```
Data will be continuously logged to binary files in the `Logging_data/` directory.

### Stop Data Recording
```
> stop_recording
```

## Data Logging

- Log files are saved to `./Logging_data/` directory (created automatically)
- Files are in binary format with timestamp naming: `YYYYMMDD_HH-MM-SS.bin`
- Maximum file size: 150 MB (approximately 2.5 hours of data)
- Files automatically roll over when size limit is reached
- Logging runs in a background thread for non-blocking operation

## Configuration

### Serial Port Settings
Default configuration (in `ipr_sensor_serial.py`):
- **Baud rate**: 921600
- **Data bits**: 8
- **Parity**: None
- **Stop bits**: 1
- **Timeout**: 0.5 seconds

### Logging Settings
Adjustable in `ipr_sensor_logging.py`:
- `MAX_FILE_SIZE`: 150 MB (file rollover threshold)
- `SAVE_FILE_EVERY_SIZE`: 100 kB (file size check interval)

## Architecture

### IprSensorSerial
Handles low-level serial port communication with automatic port detection and connection management.

### IprSensorCommand
Implements sensor command protocol including:
- Command transmission and response parsing
- Time format validation
- Interactive command interfaces

### IprSensorSerialLoggerThread
Background thread that continuously:
- Reads data from the serial port
- Writes data to timestamped binary files
- Manages file rotation based on size limits
- Can be paused/resumed without stopping the thread

## Error Handling

The program includes robust error handling for:
- Serial port connection failures
- Timeout during sensor communication
- Invalid time format entries (with retry logic)
- Buffer overflow conditions
- File I/O errors during logging

## Notes

- The logger thread starts automatically but logging is initially disabled
- Most commands will automatically stop logging if it's running
- The program uses daemon threads that clean up automatically on exit
- Command responses are parsed to extract relevant information

## Troubleshooting

**Port not detected:**
- Ensure sensor is connected and powered
- Check USB cable connection
- Verify correct drivers are installed

**Timeout errors:**
- Check baud rate matches sensor configuration
- Ensure sensor is powered and responding
- Try reconnecting the sensor

**Logging issues:**
- Verify write permissions in the current directory
- Check available disk space
- Ensure the sensor is transmitting data

## License

MIT License
Copyright (c) 2024 Philippe Bourgault

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Author

Philippe Bourgault