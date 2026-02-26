import queue
import time

from ipr_sensor_command import IprSensorCommand
from ipr_sensor_serial import IprSensorSerial
from ipr_sensor_logging import IprSensorSerialLoggerThread
from ipr_sensor_database import IprSensorDatabase

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

# Create publisher instance
publisher = IprSensorDatabase(
    broker='weather.computatrum.cloud',
    port=1883,
    sensor_id=1,
    serial_obj=ipr_serial
)

def main():
    # Main loop - process commands
    while True:
        # Wait for user input command
        user_cmd = input("> ")

        if user_cmd == "menu" or user_cmd == "?":
            print("Available commands:")
            print("[menu] or [?]: Access this menu")
            print("[quit_program]: Quit the program")
            print("---- Direct Sensor Commands ----")
            print("[init]: List the sensor information, name, and time")
            print("[get_material]: Display the sensor's material")
            print("[get_name]: Display the sensor's name")
            print("[set_name]: Change the sensor's name")
            print("[set_tare]: Apply a new tare")
            print("[get_time]: Display the sensor's internal time")
            print("[set_time]: Change the sensor's internal time")
            print("[start_recording]: Start recording sensor data to a BIN file")
            print("[stop_recording]: Stop the sensor's recording")
            print("---- Database Related ----")
            print("[init_db_connect]: Connect to the database")
            print("[start_recording_no_log]: Start recording sensor data to database without logging")
            print("[stop_recording_no_log]: Stop the sensor's recording to database")

        elif user_cmd == "":
            pass

        elif user_cmd == "init":
            if logger.is_logging():
                logger.stop_logging()
            print(ipr_cmd.set_initialize())
            print(ipr_cmd.get_name())

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

        # Functions related to remote database
        elif user_cmd == "init_db_connect":
            if logger.is_logging():
                logger.stop_logging()

            if not publisher.is_running():
                ipr_cmd.start_sensor_transmit()
                # Start publishing
                publisher.start()
                publisher.pause()

            print("The database is initialized")

        elif user_cmd == "start_recording_no_log":
            if publisher.is_running() and publisher.is_paused():
                publisher.resume()

            time.sleep(0.01)

        elif user_cmd == "stop_recording_no_log":
            if publisher.is_running():
                publisher.stop()

            time.sleep(0.01)

        elif user_cmd == "quit_program":
            break

        else:
            print("Invalid command")


if __name__ == "__main__":
    main()
