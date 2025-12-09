import serial
import serial.tools.list_ports

DEBUG_MODE = 0

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
            print("  No serial ports found")

        return available

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