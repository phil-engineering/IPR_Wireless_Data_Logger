import queue
import time

from ipr_sensor_command import IprSensorCommand
from ipr_sensor_serial import IprSensorSerial
from ipr_sensor_logging import IprSensorSerialLoggerThread

ipr_serial = IprSensorSerial()
if not ipr_serial.user_connect_to_port():
    exit(0)

ipr_cmd = IprSensorCommand(ipr_serial)

# Create queue for thread communication
data_queue = queue.Queue(maxsize=1000)

# Create and start logger thread
logger = IprSensorSerialLoggerThread(
    serial_port=ipr_serial,
    data_queue=data_queue,
    debug=True  # Set to False to disable console output
)
logger.stop_logging()
logger.start()

time.sleep(0.5)

def main():
    # Main loop - process commands
    while True:
        # Wait for user input command
        user_cmd = input("> ")

        if user_cmd == "menu" or user_cmd == "?":
            print("Available commands:")
            print("[menu] or [?]: Access this menu")
            print("[init]: List the sensor information, name, and time")
            print("[get_material]: Display the sensor's material")
            print("[get_name]: Display the sensor's name")
            print("[set_name]: Change the sensor's name")
            print("[set_tare]: Apply a new tare")
            print("[get_time]: Display the sensor's internal time")
            print("[set_time]: Change the sensor's internal time")
            print("[start_recording]: Start recording sensor data to a BIN file")
            print("[stop_recording]: Stop the sensor's recording")

        elif user_cmd == "init":
            if logger.is_logging():
                logger.stop_logging()
            print(ipr_cmd.set_initialize())
            print(ipr_cmd.get_name())
            print(ipr_cmd.get_time())

        elif user_cmd == "get_name":
            if logger.is_logging():
                logger.stop_logging()
            print(ipr_cmd.get_name())

        elif user_cmd == "set_name":
            if logger.is_logging():
                logger.stop_logging()
            print(ipr_cmd.set_name())

        elif user_cmd == "get_time":
            if logger.is_logging():
                logger.stop_logging()
            print(ipr_cmd.get_time())

        elif user_cmd == "set_time":
            if logger.is_logging():
                logger.stop_logging()
            ipr_cmd.set_time_interactive()

        elif user_cmd == "set_tare":
            if logger.is_logging():
                logger.stop_logging()
            ipr_cmd.set_tare()

        elif user_cmd == "start_recording":
            ipr_cmd.start_sensor_transmit()
            logger.start_logging()
            time.sleep(0.01)

        elif user_cmd == "stop_recording":
            if logger.is_logging():
                logger.stop_logging()
            ipr_cmd.stop_sensor_transmit()

        else:
            print("Invalid command")


if __name__ == "__main__":
    main()
