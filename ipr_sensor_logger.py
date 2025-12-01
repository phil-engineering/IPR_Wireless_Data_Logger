import serial
import os
from datetime import datetime
import platform

MAX_FILE_SIZE = 150e6           # 150 MB (~2.5h)
SAVE_FILE_EVERY_SIZE = 100e3    # 100 kB

RPi = 0
WINDOWS = 1

if platform.system() == 'Windows':
    import keyboard
    PLATFORM = WINDOWS
    USB_COM_NAME = "COM5"
else:
    PLATFORM = RPi
    USB_COM_NAME = "/dev/ttyUSB0"

print("Sensor connected to: {}".format(USB_COM_NAME))

# Prepare the folder to save the data
current_directory = os.getcwd()
path_logfile = current_directory + "/Logging_data/"
os.makedirs(path_logfile, exist_ok=True)
print("Saving the logging file to: {}".format(path_logfile))

def get_new_filename():
    now = datetime.now()
    date_time_filename = "{}{}{}_{}-{}-{}.bin".format(now.year, now.month, now.day, now.hour, now.minute, now.second)
    print(date_time_filename)
    return date_time_filename


_serial_port = serial.Serial()

try:
    _serial_port.port = USB_COM_NAME  # COM port
    _serial_port.baudrate = 921600  # Baudrate
    _serial_port.timeout = 1  # 1 second timeout
    _serial_port.open()  # Try to open serial port
except Exception as _error:  # Catch the error is serial port is not able to connect
    print(_error)


_array = bytearray()
_array.extend(map(ord, "<scanmb-start>"))
_serial_port.write(_array)  # Sending the start sequence

# Get new filename
logfile_name = get_new_filename()
# Open logging file
f = open(path_logfile + logfile_name, "ab")

logfile_size_counter = 0
isKeyPressed = False
while not isKeyPressed:
    # Read data from sensor
    _data = _serial_port.read(1)

    # Write data to file
    f.write(_data)

    # Check file size every x KB
    if logfile_size_counter >= SAVE_FILE_EVERY_SIZE:
        logfile_size_counter = 0
        # Check file size once in a while
        filesize = os.path.getsize(path_logfile + logfile_name)
        if filesize >= MAX_FILE_SIZE:
            f.close()
            logfile_name = get_new_filename()
            f = open(path_logfile + logfile_name, "ab")
    else:
        logfile_size_counter += 1

    # if PLATFORM is WINDOWS:
    #     # Check keyboard for pressed key
    #     if keyboard.is_pressed('q'):  # if key 'q' is pressed
    #        break  # finishing the loop

print('Program has terminated')
f.close()
_serial_port.close()
