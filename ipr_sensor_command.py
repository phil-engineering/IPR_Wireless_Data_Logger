import time
from collections import deque
from datetime import datetime
import ipr_sensor_serial

class IprSensorCommand:
    """Controller class for sensor commands using SerialPort"""

    def __init__(self, serial_port):
        """
        Initialize sensor controller.

        Args:
            serial_port (SerialPort): Instance of SerialPort class
            start_cmd (bytes): Command to start sensor transmission
            stop_cmd (bytes): Command to stop sensor transmission
        """
        self.ipr_serial_port = serial_port
        self.set_initialize_cmd = bytearray(b'$\r\n')
        self.start_cmd = bytearray(b'<scanmb-start>\r\n')
        self.stop_cmd = bytearray(b'<scanmb-stop>\r\n')
        self.get_time_cmd = bytearray(b'time\r\n')
        self.set_tare_cmd = bytearray(b'tare all\r\n')
        self.get_name_cmd = bytearray(b'name\r\n')

    def start_sensor_transmit(self):
        """Start sensor data transmission"""
        self.ipr_serial_port.write(self.start_cmd)

    def stop_sensor_transmit(self):
        """Stop sensor transmission and clear buffer"""
        self.ipr_serial_port.write(self.stop_cmd)
        self.sensor_read_until_empty()

    def sensor_read_until_empty(self, timeout=5.0):
        """
        Read all bytes in the buffer until empty.

        Args:
            timeout (float): Maximum time to wait
        """
        data_not_found = 1
        start_time = time.time()

        while time.time() - start_time < timeout:
            data = self.ipr_serial_port.read()
            if data == b'' or data is None:
                data_not_found = 0
                break

        if data_not_found:
            print("Special case: Buffer not empty, forcing prompt")
            self.ipr_serial_port.write(b'\r\n')
            self.read_data_from_sensor()

    def read_data_from_sensor(self, timeout=2.0):
        """
        Read data from sensor until prompt (\\r\\n>) is found.

        Args:
            timeout (float): Maximum time to wait

        Returns:
            str: Data read from sensor
        """
        data_str = ""
        window = deque(maxlen=3)

        start_time = time.time()
        while time.time() - start_time < timeout:
            data = self.ipr_serial_port.read()

            if data:
                window.append(data)
                try:
                    data_str += data.decode('ascii')
                except UnicodeDecodeError:
                    data_str += data.decode('ascii', errors='ignore')

                # Check if last 3 bytes match the pattern \r\n>
                if len(window) == 3 and window[0] == b'\r' and window[1] == b'\n' and window[2] == b'>':
                    break
            else:
                time.sleep(0.01)  # Small delay if no data to prevent CPU spinning
        else:
            # Timeout occurred
            print(f"⚠ Warning: Timeout waiting for sensor response")
            # print(data_str)
            # print(window)

        return data_str

    def set_sensor_ready_for_cmd(self, attempts=3):
        """
        Send CR+LF multiple times to ensure sensor is ready for commands.

        Args:
            attempts (int): Number of times to send CR+LF
        """
        for i in range(attempts):
            self.ipr_serial_port.write(b'\r\n')
            self.read_data_from_sensor()

    def set_initialize(self):
        self.stop_sensor_transmit()
        self.set_sensor_ready_for_cmd()
        self.ipr_serial_port.write(self.set_initialize_cmd)

        time_str = self.read_data_from_sensor()

        # Filter for line starting with "Time"
        time_items = list(time_str.split('\r\n'))

        # First strip newlines, then filter
        cleaned = [item.replace('\n', '').strip() for item in time_items if item.strip()]

        # Remove items that are still non-text after cleaning
        cleaned = [item for item in cleaned if
                   item and not all(c in '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f' for c in item)]

        if cleaned:
            result = '\n'.join(cleaned[1:-1])
            # print(result)
            return result
        else:
            print("Could not parse time from response")
            return None

    def get_name(self):
        self.stop_sensor_transmit()
        self.set_sensor_ready_for_cmd()
        self.ipr_serial_port.write(self.get_name_cmd)

        time_str = self.read_data_from_sensor()

        # Filter for line starting with "Time"
        time_items = list(filter(lambda x: x.startswith("Name"), time_str.split('\r\n')))

        if time_items:
            return time_items[0]
        else:
            print("Could not parse time from response")
            return None

    def get_time(self):
        """
        Get current time from sensor.

        Returns:
            str: Time string from sensor, or None if error
        """
        self.stop_sensor_transmit()
        self.set_sensor_ready_for_cmd()
        self.ipr_serial_port.write(self.get_time_cmd)

        time_str = self.read_data_from_sensor()

        # Filter for line starting with "Time"
        time_items = list(filter(lambda x: x.startswith("Time"), time_str.split('\r\n')))

        if time_items:
            return time_items[0]
        else:
            print("Could not parse time from response")
            return None

    def set_time(self, date_time_obj):
        """
        Set sensor time.

        Args:
            date_time_obj (datetime): DateTime object with desired time

        Returns:
            str: Confirmation string from sensor, or None if error
        """
        self.stop_sensor_transmit()
        self.set_sensor_ready_for_cmd()

        # Format command: "time yyyy-mm-dd-hh-mm-00\r\n"
        # time_cmd = f"time {date_time_obj.strftime('%Y-%m-%d-%H-%M')}-00\r\n"
        # self.ipr_serial_port.write(time_cmd.encode('ascii'))
        _set_time_cmd = bytearray()
        _set_time_cmd.extend(map(ord, "time " + date_time_obj.strftime('%Y-%m-%d-%H-%M') + "-00\r\n"))

        self.ipr_serial_port.write(_set_time_cmd)

        time_str = self.read_data_from_sensor()

        # Filter for line starting with "Time"
        time_items = list(filter(lambda x: x.startswith("Time"), time_str.split('\r\n')))

        if time_items:
            return time_items[0]
        else:
            print("Could not parse time confirmation from response")
            return None

    def check_time_format(self, time_string):
        """
        Validate time format.

        Args:
            time_string (str): Time in format 'yyyy-mm-dd-hh-mm'

        Returns:
            tuple: (success: bool, message: str, datetime_obj: datetime or None)
        """
        try:
            # Parse the input string
            dt = datetime.strptime(time_string, '%Y-%m-%d-%H-%M')

            # Additional validation checks
            if dt.year < 1900 or dt.year > 2100:
                return False, "Year must be between 1900 and 2100", None

            # If we get here, the format is valid
            return True, f"Time format valid: {dt.strftime('%Y-%m-%d %H:%M')}", dt

        except ValueError as e:
            # Parse the error to give helpful feedback
            error_msg = str(e)

            if "does not match format" in error_msg:
                return False, "Invalid format. Expected: yyyy-mm-dd-hh-mm (e.g., 2024-12-07-14-30)", None
            elif "day is out of range" in error_msg:
                return False, "Invalid day for the given month", None
            elif "month must be" in error_msg:
                return False, "Month must be between 1-12", None
            elif "hour must be" in error_msg:
                return False, "Hour must be between 0-23", None
            elif "minute must be" in error_msg:
                return False, "Minute must be between 0-59", None
            else:
                return False, f"Invalid date/time: {error_msg}", None

        except Exception as e:
            return False, f"Unexpected error: {e}", None

    def set_time_interactive(self, max_attempts=3):
        """
        Interactive time setting with retry logic.

        Args:
            max_attempts (int): Maximum number of attempts

        Returns:
            tuple: (success: bool, message: str, datetime_obj: datetime or None)
        """
        attempt = 0

        while attempt < max_attempts:
            user_cmd = input("Enter date and time in the following format: yyyy-mm-dd-hh-mm: ")

            if user_cmd.lower() in ['quit', 'exit', 'cancel']:
                return False, "Cancelled by user", None

            success, message, dt_obj = self.check_time_format(user_cmd)

            if success:
                result = self.set_time(dt_obj)
                print(f"{message}")
                print(f"Sensor response: {result}")
                return success, message, dt_obj
            else:
                attempt += 1
                print(f"{message}")

                if attempt < max_attempts:
                    print(f"Please try again ({max_attempts - attempt} attempts remaining)")

        return False, "Maximum attempts reached", None

    def set_tare(self):
        """
        Set tare (zero) on sensor.

        Returns:
            str: Tare confirmation string, or None if error
        """
        self.stop_sensor_transmit()
        self.set_sensor_ready_for_cmd()
        self.ipr_serial_port.write(self.set_tare_cmd)

        tare_str = self.read_data_from_sensor()

        # Filter for line starting with "X" (or adjust based on your sensor response)
        tare_items = list(filter(lambda x: x.startswith("X"), tare_str.split('\r\n')))

        if tare_items:
            print(f"New tare: {tare_items[0]}")
            return tare_items[0]
        else:
            print("Could not parse tare confirmation from response")
            return None
