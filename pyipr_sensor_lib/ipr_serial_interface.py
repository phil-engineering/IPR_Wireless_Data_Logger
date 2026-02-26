import serial

# Global configuration flags for debugging purposes
DEBUG_MODE = False  # Enable/disable general debug information
DEBUG_SERIAL_RECEIVE = False  # Enable/disable serial data reception debugging


def format_command(text):
    """
    Formats a command string for serial transmission by converting it to a bytearray
    and adding a carriage return.

    Args:
        text (str): The command text to format

    Returns:
        bytearray: Formatted command ready for serial transmission
    """
    _array = bytearray()
    _array.extend(map(ord, "{}\r".format(text)))
    return _array


class IPRSerialInterface:
    """
    A class to handle serial communication with IPR sensors.
    Provides methods for configuring the serial connection, sending commands,
    and reading data in both binary and text modes.
    """

    def __init__(self):
        """
        Initialize the IPR Serial Interface.
        Sets up the serial port object and initial state variables.
        """
        if DEBUG_MODE:
            print("Python serial port library version: {}".format(serial.VERSION))

        # Initialize serial port object with default settings
        self._serial_port_obj = serial.Serial()
        # Flag to track if sensor is in binary reading mode
        self.is_binary_reading_running = True
        print("Initiating IPRSerialInterface -> DONE")

    def serial_setup(self, com_port_name):
        """
        Configure the serial port settings.

        Args:
            com_port_name (str): Name of the COM port to use (e.g., 'COM1')
        """
        self._serial_port_obj.port = com_port_name
        self._serial_port_obj.baudrate = 921600  # High baudrate for fast data transfer
        self._serial_port_obj.timeout = 0.25  # Quarter second timeout for operations

    def serial_open(self):
        """
        Open the serial port connection.
        Only opens the port if it's not already open.

        Raises:
            Exception: If unable to open the serial port
        """
        try:
            if not self._serial_port_obj.isOpen():
                self._serial_port_obj.open()
                print("Connected to USB port : {}".format(self._serial_port_obj.isOpen()))
        except Exception as _error:
            print(_error)

    def serial_close(self):
        """Close the serial port connection."""
        self._serial_port_obj.close()

    def serial_read_binary(self):
        """
        Read a single byte from the serial port.

        Returns:
            bytes: Single byte read from serial port
        """
        _data = self._serial_port_obj.read(1)
        if DEBUG_SERIAL_RECEIVE:
            print(_data)
        return _data

    def serial_ipr_get_system_status(self):
        """
        Query the sensor's system status.

        Returns:
            str: System status information with trailing '>' removed
        """
        self.serial_ipr_check_if_data_reading()
        self._serial_port_obj.write(format_command("$"))
        _telegram = self.serial_ipr_read_text_from_sensor()
        return ''.join(_telegram)[:-1]

    def serial_ipr_get_sensor_tare(self):
        """
        Retrieve the tare value stored in sensor's memory.

        Returns:
            str: Tare value information
        """
        self.serial_ipr_check_if_data_reading()
        self._serial_port_obj.write(format_command("tare"))
        _telegram = self.serial_ipr_read_text_from_sensor()
        return ''.join(_telegram).split("tare\n")[-1][:-1]

    def serial_ipr_get_sensor_material_type(self):
        """
        Query the sensor's configured material type.

        Returns:
            str: Material type information
        """
        self.serial_ipr_check_if_data_reading()
        self._serial_port_obj.write(format_command("material"))
        _telegram = self.serial_ipr_read_text_from_sensor()
        return ''.join(_telegram).split("Material = ")[-1][:-1]

    def serial_ipr_get_sensor_gain(self):
        """
        Retrieve the gain/multiplier value from sensor's memory.

        Returns:
            str: Gain value information
        """
        self.serial_ipr_check_if_data_reading()
        self._serial_port_obj.write(format_command("transfer"))
        _telegram = self.serial_ipr_read_text_from_sensor()
        return ''.join(_telegram).split("transfer\n")[-1][:-1]

    def serial_ipr_get_sensor_strain_offset(self):
        """
        Retrieve the strain offset value from sensor's memory.

        Returns:
            str: Offset value information
        """
        self.serial_ipr_check_if_data_reading()
        self._serial_port_obj.write(format_command("offset"))
        _telegram = self.serial_ipr_read_text_from_sensor()
        return ''.join(_telegram).split("offset\n")[-1][:-1]

    def serial_ipr_get_sensor_name(self):
        """
        Retrieve the sensor name from device memory.

        Returns:
            str: Sensor name
        """
        self.serial_ipr_check_if_data_reading()
        self._serial_port_obj.write(format_command("name"))
        _telegram = self.serial_ipr_read_text_from_sensor()
        return ''.join(_telegram).split("Name : ")[-1][:-1]

    def serial_ipr_set_sensor_name(self, sensor_name):
        """
        Set a new name for the sensor.

        Args:
            sensor_name (str): New name to set for the sensor
        """
        self.serial_ipr_check_if_data_reading()
        self._serial_port_obj.write(format_command("name {}".format(sensor_name)))
        self.serial_ipr_read_text_from_sensor()

    def serial_ipr_start_binary_read(self):
        """
        Start binary data stream from sensor to PC.
        Sets the binary reading flag to True.
        """
        self._serial_port_obj.write(format_command("<scanmb-start>"))
        self.is_binary_reading_running = True

    def serial_ipr_stop_binary_read(self):
        """
        Stop binary data stream from sensor.
        Sets the binary reading flag to False.
        """
        self._serial_port_obj.write(format_command("<scanmb-stop>"))
        self.is_binary_reading_running = False

    def serial_ipr_check_if_data_reading(self):
        """
        Check if sensor is in binary reading mode and stop if necessary.
        Clears any remaining bytes in the buffer after stopping.
        """
        if self.is_binary_reading_running:
            self.serial_ipr_stop_binary_read()
            _stop_character_found = False
            _telegram = list()
            while not _stop_character_found:
                data = self.serial_read_binary()
                if data == b'':  # Empty byte indicates timeout reached
                    _stop_character_found = True

    def serial_ipr_read_telegram(self):
        """
        Read a complete telegram from the serial port in binary mode.
        Looks for Start of Frame (SOF) character (0x08) and collects all preceding data.

        Returns:
            str: Complete telegram in hexadecimal format
        """
        _start_char_found = False
        _telegram = list()
        while not _start_char_found:
            data = self.serial_read_binary().hex()
            if data == '08':  # Start of Frame character
                _start_char_found = True
            else:
                _telegram.append(data)
        return ''.join(_telegram)

    def serial_ipr_read_text_from_sensor(self):
        """
        Read text response from sensor until end character ('>') is found.
        Filters out unwanted control characters and formats the response.

        Returns:
            list: List of characters forming the complete response
        """
        _stop_character_found = False
        _telegram = list()
        while not _stop_character_found:
            data = self.serial_read_binary()
            if data == b'>':
                _stop_character_found = True
            else:
                if data not in (b'\n', b'\r', b'$'):
                    _telegram.append(data.decode("utf-8"))
                elif data == b'\r':
                    if len(_telegram) >= 1:
                        if _telegram[-1] != "\n":
                            _telegram.append("\n")
        return _telegram