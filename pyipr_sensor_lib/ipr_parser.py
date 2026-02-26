from array import array


class IPRParser:
    """
    A parser for handling different types of IPR (Industrial Packet Reader) telegrams:
    - Strain measurements
    - Environmental readings
    - Acceleration data
    """

    # Minimum required length for different packet types
    MIN_PACKET_LENGTH_STRAIN = 27
    MIN_PACKET_LENGTH_ENVIRONMENT = 20
    MIN_PACKET_LENGTH_ACCELERATION = 20

    def __init__(self, packet=0):
        """
        Initialize the parser with optional packet data.

        Args:
            packet: Initial packet data (default: 0)
        """
        # Store raw byte data and track invalid packets
        self._byte_data = list()
        self.invalid_data_list = list()
        self.invalid_data_number = 0

        # Header information arrays
        # [ID, ID_CRC, Sequence, Timestamp]
        self.raw_header = array('f', [-1, -1, -1, -1])
        self.packet_type = None

        # Raw measurement arrays
        # Strain measurements [X, Y, Z, Principal1, Principal2, Angle]
        self.raw_strain = array('f', [-1, -1, -1, -1, -1, -1])
        # Environmental measurements [Battery Voltage, Pressure, Humidity, Temperature]
        self.raw_env = array('f', [-1, -1, -1, -1])
        # Acceleration measurements [X, Y, Z]
        self.raw_acc = array('f', [-1, -1, -1])

        # Scaled (converted to real units) measurement arrays
        self.scaled_strain = array('f', [-1, -1, -1, -1, -1, -1])
        self.scaled_env = array('f', [-1, -1, -1, -1])
        self.scaled_acc = array('f', [-1, -1, -1])

        self.packet = packet

    def parser_set_packet(self, packet):
        """Set a new packet for parsing."""
        self.packet = packet

    @staticmethod
    def parser_compute_crc(byte0):
        """
        Compute CRC (Cyclic Redundancy Check) for the first byte.
        Returns XOR of bits 1 and 0 of BYTE 0.
        """
        return bool(int(byte0, 16) & 0x02) ^ bool(int(byte0, 16) & 0x01)

    @staticmethod
    def convert_numeric_to_scale(value_to_convert, in_min, in_max, out_min, out_max):
        """
        Convert raw sensor values to scaled real-world units using linear interpolation.

        Args:
            value_to_convert: Raw sensor value
            in_min: Minimum input range
            in_max: Maximum input range
            out_min: Minimum output range
            out_max: Maximum output range

        Returns:
            float: Scaled value in real-world units
        """
        _interpolation = 0
        if value_to_convert != 0:
            _slope = (out_max - out_min) / (in_max - in_min)
            _offset = out_min - _slope
            # Linear interpolation: Y = A*X + B
            _interpolation = _slope * value_to_convert + _offset
        return _interpolation

    def parser_hex_to_byte(self, _data, _length):
        """
        Convert hexadecimal string to bytes, processing two characters at a time.
        Stores results in self._byte_data.
        """
        self._byte_data = list()
        for i in range(0, _length, 2):
            self._byte_data.append(_data[i:i + 2])

        if len(self._byte_data) >= 2:
            previous_byte = '00'
            new_byte_list = list()
            for current_byte in self._byte_data:
                if previous_byte == '07':
                    previous_byte = '00'
                    if current_byte == '55':
                        new_byte_list.append('08')
                    elif current_byte == 'aa':
                        new_byte_list.append('07')
                else:
                    if current_byte == '07':
                        previous_byte = current_byte
                    else:
                        new_byte_list.append(current_byte)

            self._byte_data = new_byte_list.copy()

    def parser_check_telegram_validity(self, telegram):
        """
        Validate incoming telegram data.

        Checks:
        1. Minimum length
        2. Valid CRC

        Returns:
            bool: True if telegram is valid, False otherwise
        """
        _is_valid = False
        if len(telegram) >= 1:
            self.parser_hex_to_byte(telegram, 2)  # Convert first byte for CRC check
            _id_crc_computed = self.parser_compute_crc(self._byte_data[0])

            if (self.parser_get_id_crc() != _id_crc_computed) or (len(telegram) <= 20):
                self.invalid_data_list.append(telegram)
                self.invalid_data_number += 1
            else:
                _is_valid = True
        else:
            self.invalid_data_list.append(telegram)
            self.invalid_data_number += 1

        return _is_valid

    def parser_get_id(self):
        """Extract telegram ID from first two bits of BYTE 0."""
        self.raw_header[0] = int(self._byte_data[0], 16) & 0x03
        return self.raw_header[0]

    def parser_get_id_name(self):
        """
        Convert telegram ID to packet type name.

        ID mapping:
        0x00 -> STRAIN
        0x01 -> ENVIRONMENT
        0x02 -> ACCELERATION
        """
        if self.parser_get_id() == 0x00:
            self.packet_type = "STRAIN"
        elif self.parser_get_id() == 0x01:
            self.packet_type = "ENVIRONMENT"
        elif self.parser_get_id() == 0x02:
            self.packet_type = "ACCELERATION"
        else:
            self.packet_type = "PACKET ERROR"
        return self.packet_type

    def parser_get_id_crc(self):
        """Extract CRC bit (3rd bit) from BYTE 0."""
        self.raw_header[1] = (int(self._byte_data[0], 16) & 0x04) >> 2
        return self.raw_header[1]

    def parser_get_sequence(self):
        """Extract sequence number bits from BYTE 0."""
        self.raw_header[2] = int(self._byte_data[0], 16) & 0x38
        return self.raw_header[2]

    def parser_get_timestamp(self):
        """
        Extract timestamp from header bytes.
        Combines bits from BYTE 0-4 to form complete timestamp.
        """
        self.raw_header[3] = (((int(self._byte_data[4], 16) & 0x01) << 26) +
                              (int(self._byte_data[3], 16) << 18) +
                              (int(self._byte_data[2], 16) << 10) +
                              (int(self._byte_data[1], 16) << 2) +
                              ((int(self._byte_data[0], 16) & 0xC0) >> 6))
        return self.raw_header[3]

    def parser_get_header(self):
        """Extract all header information from packet."""
        self.parser_get_id()
        self.parser_get_id_crc()
        self.parser_get_sequence()
        self.parser_get_timestamp()

    def parser_get_strain(self):
        """
        Extract strain measurements from packet.
        Returns array containing:
        - XYZ strain values (indexes 0-2)
        - Principal strains P1, P2 (indexes 3-4)
        - Angle (index 5)
        """
        # Extract strain XYZ from bytes 4-8
        self.raw_strain[0] = ((int(self._byte_data[5], 16) & 0x3F) << 7) + ((int(self._byte_data[4], 16) & 0xFE) >> 1)
        self.raw_strain[1] = ((int(self._byte_data[7], 16) & 0x07) << 10) + (int(self._byte_data[6], 16) << 2) + (
                    (int(self._byte_data[5], 16) & 0xC0) >> 6)
        self.raw_strain[2] = (int(self._byte_data[8], 16) << 5) + ((int(self._byte_data[7], 16) & 0xF8) >> 3)

        # Extract principal strains and angle from bytes 9-13
        self.raw_strain[3] = ((int(self._byte_data[10], 16) & 0x1F) << 8) + int(self._byte_data[9], 16)
        self.raw_strain[4] = (
                    ((int(self._byte_data[12], 16) & 0x03) << 11) + ((int(self._byte_data[11], 16) & 0x1F) << 3) + (
                        (int(self._byte_data[10], 16) & 0xE0) >> 5))
        self.raw_strain[5] = ((int(self._byte_data[13], 16) & 0x7F) << 6) + ((int(self._byte_data[12], 16) & 0xFC) >> 2)
        return self.raw_strain

    def parser_get_environment(self):
        """
        Extract environmental measurements from packet.
        Returns array containing:
        - Battery voltage (index 0)
        - Pressure (index 1)
        - Humidity (index 2)
        - Temperature (index 3)
        """
        self.raw_env[0] = ((int(self._byte_data[5], 16) & 0x02) << 7) + ((int(self._byte_data[4], 16) & 0xFE) >> 1)
        self.raw_env[1] = (int(self._byte_data[6], 16) << 6) + ((int(self._byte_data[5], 16) & 0xFC) >> 2)
        self.raw_env[2] = ((int(self._byte_data[8], 16) & 0x03) << 8) + int(self._byte_data[7], 16)
        self.raw_env[3] = ((int(self._byte_data[9], 16) & 0x1F) << 6) + ((int(self._byte_data[8], 16) & 0xFC) >> 2)
        return self.raw_env

    def parser_get_acceleration(self):
        """
        Extract acceleration measurements from packet.
        Returns array containing XYZ acceleration values.
        """
        self.raw_acc[0] = ((int(self._byte_data[5], 16) & 0x1F) << 7) + ((int(self._byte_data[4], 16) & 0xFE) >> 1)
        self.raw_acc[1] = ((int(self._byte_data[7], 16) & 0x01) << 11) + (int(self._byte_data[6], 16) << 3) + (
                    (int(self._byte_data[5], 16) & 0xE0) >> 5)
        self.raw_acc[2] = ((int(self._byte_data[8], 16) & 0x1F) << 7) + ((int(self._byte_data[7], 16) & 0xFE) >> 1)
        return self.raw_acc

    def parser_scale_strain_xyz(self):
        """Convert raw strain XYZ values to microstrain units (-3000 to 3000)."""
        self.scaled_strain[0] = self.convert_numeric_to_scale(self.raw_strain[0], 1, 8191, -3000, 3000)
        self.scaled_strain[1] = self.convert_numeric_to_scale(self.raw_strain[1], 1, 8191, -3000, 3000)
        self.scaled_strain[2] = self.convert_numeric_to_scale(self.raw_strain[2], 1, 8191, -3000, 3000)
        return self.scaled_strain

    def parser_scale_strain_p1p2(self):
        """
        Convert raw principal strains and angle to real units:
        - P1, P2: microstrain (-3000 to 3000)
        - Angle: degrees (-90 to 90)
        """
        self.scaled_strain[3] = self.convert_numeric_to_scale(self.raw_strain[3], 1, 8191, -3000, 3000)
        self.scaled_strain[4] = self.convert_numeric_to_scale(self.raw_strain[4], 1, 8191, -3000, 3000)
        self.scaled_strain[5] = self.convert_numeric_to_scale(self.raw_strain[5], 1, 8191, -90, 90)
        return self.scaled_strain

    def parser_scale_environment(self):
        """
        Convert raw environmental values to real units:
        - Battery voltage: V (0 to 4)
        - Pressure: hP (0 to 1200)
        - Humidity: % (0 to 100)
        - Temperature: °C (-60 to 115)
        """
        self.scaled_env[0] = self.convert_numeric_to_scale(self.raw_env[0], 1, 511, 0, 4)
        self.scaled_env[1] = self.convert_numeric_to_scale(self.raw_env[1], 1, 16383, 0, 1200)
        self.scaled_env[2] = self.convert_numeric_to_scale(self.raw_env[2], 1, 1023, 0, 100)
        self.scaled_env[3] = self.convert_numeric_to_scale(self.raw_env[3], 1, 2047, -60, 115)
        return self.scaled_env

    def parser_scale_acceleration(self):
        """Convert raw acceleration values to g units (-16g to 16g)."""
        self.scaled_acc[0] = self.convert_numeric_to_scale(self.raw_acc[0], 1, 4095, -16, 16)
        self.scaled_acc[1] = self.convert_numeric_to_scale(self.raw_acc[1], 1, 4095, -16, 16)
        self.scaled_acc[2] = self.convert_numeric_to_scale(self.raw_acc[2], 1, 4095, -16, 16)
        return self.scaled_acc