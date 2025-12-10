# IPR Sensor Interface - User Manual

## Table of Contents
1. [Getting Started](#getting-started)
2. [Basic Operations](#basic-operations)
3. [Recording Data](#recording-data)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)

---

## Getting Started

### What You Need
- IPR sensor device
- USB cable (or appropriate serial connection)
- Computer with Python 3.6 or newer installed
- PySerial library installed (`pip install pyserial`)

### First Time Setup

1. **Connect your sensor**
   - Plug the IPR sensor into your computer via USB
   - Wait for your operating system to recognize the device
   - On Windows, the device will appear as a COM port (e.g., COM3, COM4)
   - On Mac/Linux, it will appear as /dev/ttyUSB0 or similar

2. **Launch the program**
   - Open a terminal or command prompt
   - Navigate to the folder containing the program files
   - Run: `python ipr_sensor.py`

3. **Select your port**
   - The program will display all available serial ports
   - If only one port is found, it will connect automatically
   - If multiple ports are shown, enter the ID number of your sensor

4. **Verify connection**
   - You should see a green checkmark: "✓ Connected to [PORT] at 921600 baud"
   - If connection fails, check your cable and try again

---

## Basic Operations

### Viewing the Command Menu

At any time, type `menu` or `?` to see all available commands:

```
> menu
```

### Initializing the Sensor

Before using the sensor, it's recommended to initialize it:

```
> init
```

This command will:
- Display sensor information
- Show the sensor's current name
- Display the sensor's internal time

**Example output:**
```
IPR Sensor v2.1
Material: Steel
Name: Sensor_Lab_01
Time: 2024-12-10-14-30-00
```

### Checking Sensor Information

**Get sensor name:**
```
> get_name
Name: Sensor_Lab_01
```

**Get sensor time:**
```
> get_time
Time: 2024-12-10-14-30-00
```

---

## Recording Data

### Starting a Recording Session

1. **Start recording:**
   ```
   > start_recording
   Sensor recording enabled
   ```

2. **The program will:**
   - Begin transmitting data from the sensor
   - Create a `Logging_data/` folder (if it doesn't exist)
   - Start saving data to a timestamped binary file
   - Display the filename being created

3. **While recording:**
   - The sensor continuously streams data
   - Data is automatically saved to disk
   - Files are limited to 150 MB (approximately 2.5 hours)
   - New files are created automatically when the limit is reached

### Stopping a Recording Session

```
> stop_recording
Sensor recording disabled
```

This will:
- Stop the sensor from transmitting
- Close the current log file
- Leave the background thread ready for the next recording

### Understanding Log Files

**File location:** `./Logging_data/`

**File naming format:** `YYYYMMDD_HH-MM-SS.bin`
- Example: `20241210_14-30-45.bin`
- YYYY = Year (2024)
- MM = Month (12)
- DD = Day (10)
- HH-MM-SS = Hour-Minute-Second (14:30:45)

**File format:** Binary data from the sensor (requires sensor-specific software to decode)

---

## Configuration

### Setting Sensor Name

To change the sensor's identification name:

```
> set_name
Enter new sensor name: Lab_Sensor_A
```

The sensor will confirm the name change.

### Setting Sensor Time

The sensor has an internal clock that should be synchronized with your computer:

```
> set_time
Enter date and time in the following format: yyyy-mm-dd-hh-mm: 2024-12-10-14-30
Time format valid: 2024-12-10 14:30
Sensor response: Time: 2024-12-10-14-30-00
```

**Time format rules:**
- Use 24-hour format (not AM/PM)
- Format: `yyyy-mm-dd-hh-mm`
- Example: `2024-12-10-14-30` means December 10, 2024 at 2:30 PM
- You have 3 attempts to enter a valid time
- Type `quit`, `exit`, or `cancel` to abort

**Common mistakes:**
- ❌ `2024-12-10 14:30` (spaces instead of dashes)
- ❌ `12-10-2024-14-30` (wrong date order)
- ❌ `2024-12-10-2-30` (missing leading zero)
- ✅ `2024-12-10-14-30` (correct format)

### Applying a Tare (Zeroing)

Taring removes the current load reading and sets it as the new zero point:

```
> set_tare
New tare: X: 0.000, Y: 0.000, Z: 0.000
```

**When to use tare:**
- At the beginning of a measurement session
- After placing a container on the sensor
- When you want to measure relative changes from the current state

---

## Troubleshooting

### Connection Issues

**Problem:** "No serial ports found"
- **Solution:** Check that the sensor is plugged in and powered on
- **Solution:** Try a different USB port
- **Solution:** Check if device drivers are installed (especially on Windows)

**Problem:** "Failed to connect to [PORT]"
- **Solution:** Close any other programs that might be using the port
- **Solution:** Unplug and replug the sensor
- **Solution:** Restart the program

### Communication Errors

**Problem:** "Timeout waiting for sensor response"
- **Solution:** The sensor may not be responding. Try:
  - Running the `init` command to reset communication
  - Stopping any active recording with `stop_recording`
  - Unplugging and reconnecting the sensor

**Problem:** Commands don't seem to work
- **Solution:** If recording is active, stop it first with `stop_recording`
- **Solution:** Most configuration commands require recording to be stopped

### Data Logging Issues

**Problem:** Can't find log files
- **Solution:** Files are saved in `Logging_data/` in the same folder as the program
- **Solution:** Check that you have write permissions in the program directory

**Problem:** "Permission denied" when logging
- **Solution:** Close any other programs that might have the log files open
- **Solution:** Run the program with appropriate permissions
- **Solution:** Check available disk space

**Problem:** Log files seem incomplete
- **Solution:** Always use `stop_recording` to properly close files
- **Solution:** Don't close the program while recording is active

### Time Setting Issues

**Problem:** "Invalid format" error
- **Solution:** Carefully check your format: `yyyy-mm-dd-hh-mm`
- **Solution:** Use leading zeros (e.g., `09` not `9` for September)
- **Solution:** Use 24-hour time (e.g., `14` for 2 PM, not `2`)

**Problem:** "Invalid day for the given month"
- **Solution:** Remember different months have different numbers of days
- **Solution:** February has 28 days (29 in leap years)
- **Solution:** April, June, September, November have 30 days

---

## Best Practices

1. **Always initialize the sensor** when you first connect by running `init`

2. **Set the time** at the start of each session to ensure accurate timestamps

3. **Apply tare** before starting measurements if you need relative readings

4. **Stop recording properly** using `stop_recording` before closing the program

5. **Organize your data** by creating descriptive sensor names for different setups

6. **Monitor disk space** when recording for extended periods

7. **Keep log files organized** by moving completed sessions to dated folders

8. **Test your setup** with a short recording before starting long measurement sessions

---

## Quick Reference Card

| Command           | Purpose | When to Use |
|-------------------|---------|-------------|
| `menu` or `?`     | Show all commands | When you forget a command |
| `init`            | Initialize sensor | First thing after connecting |
| `get_name`        | Check sensor name | Verify which sensor is connected |
| `set_name`        | Change sensor name | Identify different sensors |
| `get_time`        | Check sensor time | Verify time synchronization |
| `set_time`        | Set sensor time | At start of session |
| `set_tare`        | Zero the sensor | Before measurements |
| `start_recording` | Begin logging data | Start data collection |
| `stop_recording`  | End logging | Finish data collection |

---

## Getting Help

If you encounter issues not covered in this manual:

1. Check the README.md file for technical details
2. Review the error messages carefully - they often indicate the problem
3. Try restarting both the program and the sensor
4. Contact your sensor manufacturer for device-specific questions

---

**Document Version:** 1.0  
**Last Updated:** December 2025