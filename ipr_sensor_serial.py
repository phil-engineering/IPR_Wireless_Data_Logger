import serial
import serial.tools.list_ports

# Global configuration flags for debugging purposes
DEBUG_MODE = False  # Enable/disable general debug information
DEBUG_SERIAL_RECEIVE = False  # Enable/disable serial data reception debugging


class IprSensorSerial:
    """Basic serial port communication class"""

    def __init__(self, port=None, baudrate=921600, timeout=0.5):
        """
        Initialize serial port connection.

        Args:
            port (str): Serial port name (e.g., 'COM3' or '/dev/ttyUSB0')
                       If None, will try to auto-detect
            baudrate (int): Baud rate (default: 921600)
            timeout (float): Read timeout in seconds (default: 1)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection = None
        self.is_open = False

        # Try to initialize connection
        if port:
            self.connect()

    def list_available_ports(self):
        """List all available serial ports"""
        ports = serial.tools.list_ports.comports()
        # ports = serial.tools.list_ports.comports()
        available = []

        print("\nAvailable serial ports:")
        print(f"ID : Port - Description")
        print("-" * 40)
        for i, port in enumerate(ports):
            print(f"  {i}: {port.device} - {port.description}")
            available.append(port.device)
        print("-" * 40)
        if not available:
            print("No serial ports found")

        return available

    def user_connect_to_port(self):

        available_serial_ports = self.list_available_ports()

        not_connected = True
        while not_connected:
            if len(available_serial_ports) >= 2:
                port_id = input("Enter the port ID to use: ")
                if port_id.isdigit() and 0 <= int(port_id) <= 9:
                    port_id = int(port_id)
                    if port_id < len(available_serial_ports):
                        self.connect(available_serial_ports[port_id])
                        not_connected = False
                    else:
                        print("Invalid input. Please enter a valid serial port ID.")
                else:
                    print("Invalid input. Please enter a number between 0 and 9.")

            elif len(available_serial_ports) == 1:
                print("Only 1 serial port found, trying to connect...")
                self.connect(available_serial_ports[0])
                not_connected = False
            else:
                print("Unable to connect, no serial port found")
                print("The script will terminate")
                return False
        return True

    def connect(self, port=None):
        """
        Connect to serial port.

        Args:
            port (str): Optional port name to connect to

        Returns:
            bool: True if connected successfully
        """
        if port:
            self.port = port

        if not self.port:
            print("Error: No port specified")
            return False

        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )

            self.is_open = True
            print(f"✓ Connected to {self.port} at {self.baudrate} baud")
            return True

        except serial.SerialException as e:
            print(f"✗ Failed to connect to {self.port}: {e}")
            self.is_open = False
            return False
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            self.is_open = False
            return False

    def disconnect(self):
        """Close the serial connection"""
        if self.serial_connection and self.is_open:
            try:
                self.serial_connection.close()
                self.is_open = False
                print(f"✓ Disconnected from {self.port}")
                return True
            except Exception as e:
                print(f"✗ Error disconnecting: {e}")
                return False
        return True

    def read(self, num_bytes=1):
        """
        Read bytes from serial port.

        Args:
            num_bytes (int): Number of bytes to read (default: 1)

        Returns:
            bytes: Data read from port, or None if error/timeout
        """
        if not self.is_open or not self.serial_connection:
            print("✗ Serial port not open")
            return None

        try:
            if self.serial_connection.in_waiting > 0:
                data = self.serial_connection.read(1)
                if DEBUG_MODE:
                    print(data)
                return data if data else None
            return None

        except serial.SerialException as e:
            print(f"✗ Read error: {e}")
            return None
        except Exception as e:
            print(f"✗ Unexpected read error: {e}")
            return None

    def write(self, data):
        """
        Write data to serial port.

        Args:
            data (bytes or str): Data to write

        Returns:
            int: Number of bytes written, or None if error
        """
        if not self.is_open or not self.serial_connection:
            print("✗ Serial port not open")
            return None

        try:
            # Convert string to bytes if needed
            if isinstance(data, str):
                data = data.encode('ascii')

            if DEBUG_MODE:
                print(data)

            bytes_written = self.serial_connection.write(data)  # Sending command
            self.serial_connection.flush()  # Ensure data is sent
            return bytes_written

        except serial.SerialException as e:
            print(f"✗ Write error: {e}")
            return None
        except Exception as e:
            print(f"✗ Unexpected write error: {e}")
            return None

    def available(self):
        """
        Check how many bytes are available to read.

        Returns:
            int: Number of bytes available, or 0 if error
        """
        if not self.is_open or not self.serial_connection:
            return 0

        try:
            return self.serial_connection.in_waiting
        except Exception as e:
            print(f"✗ Error checking available bytes: {e}")
            return 0

    def flush_input(self):
        """Clear input buffer"""
        if self.is_open and self.serial_connection:
            try:
                self.serial_connection.reset_input_buffer()
                return True
            except Exception as e:
                print(f"✗ Error flushing input: {e}")
                return False
        return False

    def flush_output(self):
        """Clear output buffer"""
        if self.is_open and self.serial_connection:
            try:
                self.serial_connection.reset_output_buffer()
                return True
            except Exception as e:
                print(f"✗ Error flushing output: {e}")
                return False
        return False

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    def __del__(self):
        """Destructor - ensure connection is closed"""
        self.disconnect()


    def serial_read_binary(self):
        """
        Read a single byte from the serial port.

        Returns:
            bytes: Single byte read from serial port
        """
        _data = self.serial_connection.read(1)
        if DEBUG_SERIAL_RECEIVE:
            print(_data)
        return _data

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