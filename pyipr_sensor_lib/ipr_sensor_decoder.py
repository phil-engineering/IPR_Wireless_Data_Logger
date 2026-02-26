from pyipr_sensor_lib.ipr_parser import *


class IPRSensorDecoder:
    """
    Decoder class for IPR sensor data that handles strain, environmental, and acceleration measurements.

    This class processes binary packets from IPR sensors and decodes them into readable measurements.
    It supports three types of sensor data:
    - Strain: Measures deformation along XYZ axes and principal strains
    - Environmental: Monitors battery, pressure, humidity, and temperature
    - Acceleration: Tracks movement along XYZ axes

    The decoder handles binary packet validation, parsing, and scaling of raw sensor values
    into meaningful physical units.
    """

    # Constants for strain measurement axes (0-2 represent X, Y, Z respectively)
    STRAIN_AXIS_X = 0
    STRAIN_AXIS_Y = 1
    STRAIN_AXIS_Z = 2

    # Constants for acceleration measurement axes (0-2 represent X, Y, Z respectively)
    ACCEL_AXIS_X = 0
    ACCEL_AXIS_Y = 1
    ACCEL_AXIS_Z = 2

    # Constants for environmental measurements (0-3 represent different sensor readings)
    ENVIRONMENT_VBAT = 0  # Battery voltage
    ENVIRONMENT_PRES = 1  # Pressure
    ENVIRONMENT_HUMI = 2  # Humidity
    ENVIRONMENT_TEMP = 3  # Temperature

    # Constants to identify packet types in the data stream
    TYPE_STRAIN = 0  # Strain measurement packet
    TYPE_ENVIRONMENT = 1  # Environmental measurement packet
    TYPE_ACCELERATION = 2  # Acceleration measurement packet

    def __init__(self):
        """
        Initialize the IPR sensor decoder with default values and required objects.

        Sets up:
        - Data storage (_list_of_data)
        - Parser object for processing IPR packets
        - Packet type tracking
        - Packet validity flag
        """
        self._list_of_data = 0
        self.ipr_parser_obj = IPRParser()  # Initialize parser for IPR packets
        self.packet_type = 0  # Track current packet type
        self.is_packet_valid = False  # Flag for packet validation status

        print("Initiating IPRSensorDecoder -> DONE")

    def load_from_binary_file(self, filepath, filename):
        """
        Read and decode IPR sensor data from a binary file.

        The method reads binary data and splits it into individual telegrams based on
        the '0x08' marker that indicates the start of a new packet.

        Args:
            filepath (str): Path to the directory containing the file
            filename (str): Name of the binary file to process

        Returns:
            list: List of telegrams extracted from the file, each telegram represents
                 a separate sensor measurement
        """
        # Open file in binary read mode
        with open(filepath + filename, 'rb') as file:
            file_content = file.read()

        # Process content into telegrams
        packet_list = list()
        tmp_str = ""
        # Split data on 0x08 marker bytes
        for byte_data in file_content:
            if byte_data == 0x8:  # Check for telegram separator
                packet_list.append(tmp_str)
                tmp_str = ""
            else:
                tmp_str += f"{byte_data:02x}"  # Convert bytes to hex string

        return packet_list

    def save_binary_data(self, filepath, filename, raw_data):
        """
        Append binary sensor data to a file.

        Args:
            filepath (str): Directory path for saving the file
            filename (str): Name of the file to save data to
            raw_data (bytes/bytearray): Binary sensor data to be written

        Notes:
            - Opens file in append binary mode ('ab')
            - Creates new file if it doesn't exist
            - Appends to existing file if it exists
            - Preserves binary format of the data

        Raises:
            Exception: Captures and reports file operation errors (permissions, disk space, etc.)
        """
        try:
            with open(filepath + filename, 'ab') as file:
                file.write(raw_data)
        except Exception as e:
            print(f"Error saving file: {e}")

    def analyse_packet(self, packet):
        """
        Analyze and decode an IPR sensor packet based on its type.

        This method:
        1. Creates a new parser instance for the packet
        2. Validates the telegram format
        3. Converts hex to bytes and extracts header
        4. Identifies packet type (strain/environment/acceleration)
        5. Processes data according to packet type
        6. Sets validity flag based on successful processing

        Args:
            packet: Raw packet data to analyze

        Notes:
            - Different packet types have different minimum length requirements
            - Sets is_packet_valid flag to indicate successful processing
            - Handles three types of measurements: strain, environment, and acceleration
        """
        self.ipr_parser_obj = IPRParser(packet)

        # Validate telegram format
        if self.ipr_parser_obj.parser_check_telegram_validity(packet):
            # Convert hex to bytes and extract header
            self.ipr_parser_obj.parser_hex_to_byte(packet, len(packet))
            self.ipr_parser_obj.parser_get_header()

            # Process based on packet type
            if self.ipr_parser_obj.parser_get_id_name() == "STRAIN":
                if len(packet) >= self.ipr_parser_obj.MIN_PACKET_LENGTH_STRAIN:
                    self.packet_type = self.TYPE_STRAIN
                    self.ipr_parser_obj.parser_get_strain()
                    self.ipr_parser_obj.parser_scale_strain_xyz()
                    self.ipr_parser_obj.parser_scale_strain_p1p2()
                    self.is_packet_valid = True
                else:
                    self.is_packet_valid = False
                    print("STRAIN: Data string too short to be process - Length:{} - Data: {}".format(len(packet),packet))

            elif self.ipr_parser_obj.parser_get_id_name() == "ENVIRONMENT":
                if len(packet) >= self.ipr_parser_obj.MIN_PACKET_LENGTH_ENVIRONMENT:
                    self.packet_type = self.TYPE_ENVIRONMENT
                    self.ipr_parser_obj.parser_get_environment()
                    self.ipr_parser_obj.parser_scale_environment()
                    self.is_packet_valid = True
                else:
                    self.is_packet_valid = False
                    print("ENVIRONMENT: Data string too short to be process")

            elif self.ipr_parser_obj.parser_get_id_name() == "ACCELERATION":
                if len(packet) >= self.ipr_parser_obj.MIN_PACKET_LENGTH_ACCELERATION:
                    self.packet_type = self.TYPE_ACCELERATION
                    self.ipr_parser_obj.parser_get_acceleration()
                    self.ipr_parser_obj.parser_scale_acceleration()
                    self.is_packet_valid = True
                else:
                    self.is_packet_valid = False
                    print("ACCELERATION: Data string too short to be process")
        else:
            self.is_packet_valid = False

    def print_strain(self):
        """
        Print formatted strain measurements for all axes.

        Outputs:
        - XYZ strain values in microStrain units
        - Principal strains (P1, P2) in microStrain
        - Principal strain angle in degrees
        """
        print("STRAIN X: {:.2f} uStrain ; STRAIN Y: {:.2f} uStrain ; STRAIN Z: {:.2f} uStrain"
              .format(self.ipr_parser_obj.parser_scale_strain_xyz()[0],
                      self.ipr_parser_obj.parser_scale_strain_xyz()[1],
                      self.ipr_parser_obj.parser_scale_strain_xyz()[2]))
        print("STRAIN P1: {:.2f} uStrain ; STRAIN P2: {:.2f} uStrain ; STRAIN ANGLE: {:.2f} degrees"
              .format(self.ipr_parser_obj.parser_scale_strain_p1p2()[3],
                      self.ipr_parser_obj.parser_scale_strain_p1p2()[4],
                      self.ipr_parser_obj.parser_scale_strain_p1p2()[5]))

    def print_environment(self):
        """
        Print formatted environmental measurements.

        Outputs:
        - Battery voltage in Volts (V)
        - Pressure in hectoPascals (hP)
        - Humidity in percentage (%)
        - Temperature in Celsius (°C)
        """
        print("VBATT: {:.2f} V ; PRESSURE: {:.2f} hP ; HUMIDITY: {:.2f}% ; TEMPERATURE: {:.2f}°C"
              .format(self.ipr_parser_obj.parser_scale_environment()[0],
                      self.ipr_parser_obj.parser_scale_environment()[1],
                      self.ipr_parser_obj.parser_scale_environment()[2],
                      self.ipr_parser_obj.parser_scale_environment()[3]))

    def print_acceleration(self):
        """
        Print formatted acceleration measurements for all axes.

        Outputs:
        - XYZ acceleration values in G forces
        """
        print("ACC. X: {:.2f} G ; ACC. Y: {:.2f} G ; ACC. Z: {:.2f} G"
              .format(self.ipr_parser_obj.parser_scale_acceleration()[0],
                      self.ipr_parser_obj.parser_scale_acceleration()[1],
                      self.ipr_parser_obj.parser_scale_acceleration()[2]))

    def get_strain_xyz(self, axis=0, scaled=True):
        """
        Get strain value for a specific axis.

        Args:
            axis (int): Axis index (0=X, 1=Y, 2=Z)
            scaled (bool): Whether to return scaled values (default True)

        Returns:
            float: Strain value for specified axis, or -1 if invalid axis
        """
        if axis in range(0, 3):
            if scaled:
                return self.ipr_parser_obj.parser_scale_strain_xyz()[axis]
            else:
                return self.ipr_parser_obj.parser_get_strain()[axis]
        else:
            return -1

    def get_acceleration_xyz(self, axis=0, scaled=True):
        """
        Get acceleration value for a specific axis.

        Args:
            axis (int): Axis index (0=X, 1=Y, 2=Z)
            scaled (bool): Whether to return scaled values (default True)

        Returns:
            float: Acceleration value in G forces for specified axis, or -1 if invalid axis
        """
        if axis in range(0, 3):
            if scaled:
                return self.ipr_parser_obj.parser_scale_acceleration()[axis]
            else:
                return self.ipr_parser_obj.parser_get_acceleration()[axis]
        else:
            return -1

    def get_environment(self, axis=0, scaled=True):
        """
        Get environmental measurement for a specific sensor.

        Args:
            axis (int): Sensor index (0=Battery, 1=Pressure, 2=Humidity, 3=Temperature)
            scaled (bool): Whether to return scaled values (default True)

        Returns:
            float: Environmental measurement for specified sensor, or -1 if invalid sensor
        """
        if axis in range(0, 4):
            if scaled:
                return self.ipr_parser_obj.parser_scale_environment()[axis]
            else:
                return self.ipr_parser_obj.parser_get_environment()[axis]
        else:
            return -1

    def get_packet_type(self):
        """
        Get the type of the current packet.

        Returns:
            int: Packet type (TYPE_STRAIN, TYPE_ENVIRONMENT, or TYPE_ACCELERATION)
        """
        return self.packet_type

    def ipr_decoder_is_packet_valid(self):
        """
        Check if the current packet was successfully decoded.

        Returns:
            bool: True if packet is valid and properly decoded, False otherwise
        """
        return self.is_packet_valid