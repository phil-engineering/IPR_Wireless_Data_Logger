import queue
import time

# from ipr_sensor_serial_logger import *
from ipr_sensor_command import IprSensorCommand
from ipr_sensor_serial import IprSensorSerial
from ipr_sensor_logging import SerialLoggerThread

ipr_serial = IprSensorSerial()
available_serial_ports = ipr_serial.list_available_ports()

not_connected = True
while not_connected:
    if len(available_serial_ports) >= 2:
        port_id = input("Enter the port ID to use: ")
        if port_id.isdigit() and 0 <= int(port_id) <= 9:
            port_id = int(port_id)
            if port_id < len(available_serial_ports):
                ipr_serial.connect(available_serial_ports[port_id])
                not_connected = False
            else:
                print("Invalid input. Please enter a valid serial port ID.")
        else:
            print("Invalid input. Please enter a number between 0 and 9.")

    elif len(available_serial_ports) == 1:
        print("Only 1 serial port found, trying to connect...")
        ipr_serial.connect(available_serial_ports[0])
        not_connected = False
    else:
        print("No serial port found")
        print("The script will terminate")
        exit(0)  # Exits entire program


ipr_cmd = IprSensorCommand(ipr_serial)

# Create queue for thread communication
data_queue = queue.Queue(maxsize=1000)

# Create and start logger thread
logger = SerialLoggerThread(
    serial_port=ipr_serial,
    data_queue=data_queue,
    debug=True  # Set to False to disable console output
)
logger.stop_logging()
logger.start()



time.sleep(1)

def main():
    # Main loop - process commands
    while True:
        user_cmd = input("> ")

        if user_cmd == "menu" or user_cmd == "?":
            print("Available commands:")
            print("[menu] or [?]: Access this menu")
            print("[init]: List the sensor information, name, and time")
            print("[get_time]: Display the sensor's internal time")
            print("[set_time]: Change the sensor's internal time")
            print("[get_name]: Display the sensor's name")
            print("[set_tare]: Apply a new tare")
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
                # ipr_cmd.stop_sensor_transmit()
            print(ipr_cmd.get_name())

        elif user_cmd == "get_time":
            if logger.is_logging():
                logger.stop_logging()
                # ipr_cmd.stop_sensor_transmit()
            print(ipr_cmd.get_time())

        elif user_cmd == "set_time":
            if logger.is_logging():
                logger.stop_logging()
                ipr_cmd.stop_sensor_transmit()
            ipr_cmd.set_time_interactive()

        elif user_cmd == "set_tare":
            if logger.is_logging():
                logger.stop_logging()
                ipr_cmd.stop_sensor_transmit()
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
