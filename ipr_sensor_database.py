#!/usr/bin/env python3
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import struct
import zlib
import time
import math
import random
import threading

from pyipr_sensor_lib.ipr_sensor_decoder import IPRSensorDecoder
from pyipr_sensor_lib.ipr_serial_interface import IPRSerialInterface


class IprSensorDatabase:
    """Threaded MQTT sensor data publisher with start/pause/stop control"""

    def __init__(self, broker='weather.computatrum.cloud', port=1883,
                 user='ipr_sensor_admin', password='iprsensor2025',
                 sensor_id=1, sample_rate=1000, env_sample_rate=1,
                 serial_obj=0):

        # MQTT Configuration
        self.broker = broker
        self.port = port
        self.user = user
        self.password = password
        self.sensor_id = sensor_id
        self.sample_rate = sample_rate
        self.env_sample_rate = env_sample_rate
        # self.com_port = com_port

        # Thread control
        self._thread = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Start unpaused

        # MQTT client
        self.client = None

        # Sensor objects
        self.serial_obj = serial_obj
        self.ipr_obj = None

        # Statistics
        self.sample_count = 0
        self.is_connected = False
        self._last_error = None

    def _setup_serial(self):
        """Initialize serial interface"""
        try:
            # self.serial_obj = IPRSerialInterface()
            # self.serial_obj.serial_setup(self.com_port)
            # self.serial_obj.serial_open()
            # print(self.serial_obj.serial_ipr_get_system_status())

            # self.serial_obj.serial_ipr_start_binary_read()
            self.ipr_obj = IPRSensorDecoder()

            # print(self.serial_obj.get_name())
            return True
        except Exception as e:
            # print(f"✗ Error setting up serial port {self.com_port}: {e}")
            print(f"  Make sure the port is not already in use by another program")
            self._last_error = str(e)
            return False

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback for when the client connects to the broker"""
        if reason_code == 0:
            print(f"✓ Connected successfully to {self.broker}:{self.port}")
            self.is_connected = True
        else:
            print(f"✗ Failed to connect: {reason_code}")
            self.is_connected = False

    def _on_publish(self, client, userdata, mid, reason_code, properties):
        """Callback for when a message is published"""
        pass

    def _setup_mqtt(self):
        """Initialize MQTT client"""
        try:
            self.client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
            self.client.username_pw_set(self.user, self.password)
            self.client.on_connect = self._on_connect
            self.client.on_publish = self._on_publish

            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            time.sleep(1)  # Wait for connection
            return True
        except Exception as e:
            print(f"✗ Error connecting to MQTT broker: {e}")
            self._last_error = str(e)
            return False

    def _generate_strain_data(self):
        """Get strain sensor data"""
        return {
            'strain_x': self.ipr_obj.get_strain_xyz(0),
            'strain_y': self.ipr_obj.get_strain_xyz(1),
            'strain_z': self.ipr_obj.get_strain_xyz(2),
            'strain_p1': 0,
            'strain_p2': 0,
            'strain_pdeg': random.uniform(-180, 180)
        }

    def _generate_accel_data(self):
        """Simulate accelerometer data"""
        t = time.time()
        return {
            'accel_x': 0.2 * math.sin(2 * math.pi * 5 * t) + 0.02 * random.gauss(0, 1),
            'accel_y': 0.2 * math.cos(2 * math.pi * 5 * t) + 0.02 * random.gauss(0, 1),
            'accel_z': 9.81 + 0.05 * random.gauss(0, 1)
        }

    def _generate_env_data(self):
        """Get environmental sensor data"""
        return {
            'v_batt': self.ipr_obj.get_environment(0),
            'temperature': self.ipr_obj.get_environment(3),
            'humidity': self.ipr_obj.get_environment(2),
            'pressure': self.ipr_obj.get_environment(1)
        }

    def _pack_high_freq_data(self, strain_x, strain_y, strain_z, strain_p1,
                             strain_p2, strain_pdeg, accel_x, accel_y,
                             accel_z, timestamp_ns):
        """Pack high-frequency data (1000 Hz): 9 floats + timestamp"""
        return struct.pack(
            '<9fQ',
            strain_x, strain_y, strain_z,
            strain_p1, strain_p2, strain_pdeg,
            accel_x, accel_y, accel_z,
            timestamp_ns
        )

    def _pack_env_data(self, v_batt, temperature, humidity, pressure,
                       timestamp_ns, sensor_id):
        """Pack environmental data (1 Hz): 4 floats + timestamp + sensor_id"""
        return struct.pack(
            '<4fQB',
            v_batt, temperature, humidity, pressure,
            timestamp_ns,
            sensor_id
        )

    def _run(self):
        """Main thread loop"""
        # Initialize variables at the top to avoid UnboundLocalError
        buffer_high_freq = []
        last_env_time = 0

        try:
            # Setup serial connection
            if not self._setup_serial():
                print("Failed to setup serial connection. Thread exiting.")
                return

            # Setup MQTT connection
            if not self._setup_mqtt():
                print("Failed to setup MQTT connection. Thread exiting.")
                # Clean up serial if MQTT fails
                if self.serial_obj:
                    try:
                        self.serial_obj.serial_close()
                    except:
                        pass
                return

            print(f"Sensor ID: {self.sensor_id}")
            print(f"High-frequency data: {self.sample_rate} Hz (strain + accel)")
            print(f"Environmental data: {self.env_sample_rate} Hz")
            print("Thread started. Use pause()/resume()/stop() to control\n")

            sample_interval = 1.0 / self.sample_rate

            while not self._stop_event.is_set():
                # Check if paused
                self._pause_event.wait()

                # Check again if we should stop (in case stopped while paused)
                if self._stop_event.is_set():
                    break

                start_time = time.time()
                timestamp_ns = int(time.time_ns())

                try:
                    self.ipr_obj.analyse_packet(self.serial_obj.serial_ipr_read_telegram())

                    if self.ipr_obj.ipr_decoder_is_packet_valid():
                        if self.ipr_obj.get_packet_type() == self.ipr_obj.TYPE_STRAIN:
                            strain_data = self._generate_strain_data()
                            accel_data = self._generate_accel_data()

                            packet = self._pack_high_freq_data(
                                strain_data['strain_x'],
                                strain_data['strain_y'],
                                strain_data['strain_z'],
                                strain_data['strain_p1'],
                                strain_data['strain_p2'],
                                strain_data['strain_pdeg'],
                                accel_data['accel_x'],
                                accel_data['accel_y'],
                                accel_data['accel_z'],
                                timestamp_ns
                            )
                            buffer_high_freq.append(packet)
                            self.sample_count += 1

                        # Send environmental data
                        if time.time() - last_env_time >= (1.0 / self.env_sample_rate):
                            if self.ipr_obj.get_packet_type() == self.ipr_obj.TYPE_ENVIRONMENT:
                                env_data = self._generate_env_data()
                                env_packet = self._pack_env_data(
                                    env_data['v_batt'],
                                    env_data['temperature'],
                                    env_data['humidity'],
                                    env_data['pressure'],
                                    timestamp_ns,
                                    self.sensor_id
                                )

                                compressed_env = zlib.compress(env_packet, level=6)
                                result = self.client.publish(
                                    f'sensor/{self.sensor_id}/env',
                                    compressed_env,
                                    qos=1
                                )

                                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                                    print(f"[ENV] Batt:{env_data['v_batt']:.2f}V "
                                          f"Temp:{env_data['temperature']:.1f}°C "
                                          f"Humidity:{env_data['humidity']:.1f}% "
                                          f"Pressure:{env_data['pressure']:.1f}hPa")

                                last_env_time = time.time()

                    # Send high-frequency batch
                    if len(buffer_high_freq) >= self.sample_rate:
                        batch = b''.join(buffer_high_freq)
                        compressed = zlib.compress(batch, level=6)

                        result = self.client.publish(
                            f'sensor/{self.sensor_id}/data',
                            compressed,
                            qos=1
                        )

                        if result.rc == mqtt.MQTT_ERR_SUCCESS:
                            compression_ratio = len(batch) / len(compressed)
                            bandwidth_kbps = (len(compressed) * 8) / 1024
                            print(f"[DATA] Sent {len(buffer_high_freq)} samples | "
                                  f"{len(batch)} → {len(compressed)} bytes | "
                                  f"{compression_ratio:.1f}x compression | "
                                  f"{bandwidth_kbps:.1f} kbps")

                        buffer_high_freq = []

                except Exception as e:
                    print(f"✗ Error reading/publishing sensor data: {e}")
                    # Continue running, just skip this iteration

                # Maintain sample rate
                elapsed = time.time() - start_time
                sleep_time = max(0, sample_interval - elapsed)
                time.sleep(sleep_time)

        except Exception as e:
            print(f"✗ Fatal error in sensor thread: {e}")
            self._last_error = str(e)

        finally:
            # Cleanup - send remaining data
            if buffer_high_freq and self.client:
                try:
                    batch = b''.join(buffer_high_freq)
                    compressed = zlib.compress(batch, level=6)
                    self.client.publish(f'sensor/{self.sensor_id}/data', compressed, qos=1)
                    print(f"Sent final {len(buffer_high_freq)} samples")
                except Exception as e:
                    print(f"Error sending final data: {e}")

            # Close MQTT connection
            if self.client:
                try:
                    self.client.loop_stop()
                    self.client.disconnect()
                except Exception as e:
                    print(f"Error closing MQTT: {e}")

            # # Close serial connection
            # if self.serial_obj:
            #     try:
            #         self.serial_obj.disconnect()
            #     except Exception as e:
            #         print(f"Error closing serial: {e}")

            print(f"Thread stopped. Total samples sent: {self.sample_count}")

    def start(self):
        """Start the sensor publishing thread"""
        if self._thread is not None and self._thread.is_alive():
            print("Thread is already running")
            return False

        self._stop_event.clear()
        self._pause_event.set()
        self.sample_count = 0
        self._last_error = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return True

    def pause(self):
        """Pause data publishing (thread keeps running but doesn't send data)"""
        if self._thread is None or not self._thread.is_alive():
            print("Thread is not running")
            return False

        self._pause_event.clear()
        print("Data publishing paused")
        return True

    def resume(self):
        """Resume data publishing"""
        if self._thread is None or not self._thread.is_alive():
            print("Thread is not running")
            return False

        self._pause_event.set()
        print("Data publishing resumed")
        return True

    def stop(self):
        """Stop the thread completely"""
        if self._thread is None:
            return False

        print("Stopping sensor thread...")
        self._stop_event.set()
        self._pause_event.set()  # Unpause if paused, so thread can exit
        self._thread.join(timeout=5)

        if self._thread.is_alive():
            print("Warning: Thread did not stop within timeout")
            return False
        return True

    def is_running(self):
        """Check if thread is running"""
        return self._thread is not None and self._thread.is_alive()

    def is_paused(self):
        """Check if thread is paused"""
        return not self._pause_event.is_set()

    def get_last_error(self):
        """Get the last error message"""
        return self._last_error


# # Example usage
# if __name__ == "__main__":
#     # Create publisher instance
#     publisher = SensorPublisher(
#         broker='weather.computatrum.cloud',
#         port=1883,
#         sensor_id=1,
#         com_port='COM5'
#     )
#
#     # Start publishing
#     if publisher.start():
#         print("Publisher started successfully")
#     else:
#         print("Failed to start publisher")
#         exit(1)
#
#     try:
#         # Simulate control from another program
#         time.sleep(5)
#
#         if publisher.is_running():
#             print("\n--- Pausing for 3 seconds ---")
#             publisher.pause()
#
#             time.sleep(3)
#             print("\n--- Resuming ---")
#             publisher.resume()
#
#             time.sleep(5)
#
#         print("\n--- Stopping ---")
#         publisher.stop()
#
#         if publisher.get_last_error():
#             print(f"Last error: {publisher.get_last_error()}")
#
#     except KeyboardInterrupt:
#         print("\nStopping...")
#         publisher.stop()

# #!/usr/bin/env python3
# import paho.mqtt.client as mqtt
# from paho.mqtt.enums import CallbackAPIVersion
# import struct
# import zlib
# import time
# import math
# import random
# from pyipr_sensor_lib.ipr_sensor_decoder import IPRSensorDecoder
# from pyipr_sensor_lib.ipr_serial_interface import IPRSerialInterface
#
# # Configuration
# MQTT_BROKER = 'weather.computatrum.cloud'
# MQTT_PORT = 1883
# MQTT_USER = 'ipr_sensor_admin'
# MQTT_PASS = 'iprsensor2025'
# SENSOR_ID = 1
# SAMPLE_RATE = 1000  # Hz for high-frequency data
# ENV_SAMPLE_RATE = 1  # Hz for environmental data
#
# # Setup the serial interface for the strain sensor
# obj = IPRSerialInterface()
# obj.serial_setup("COM5")        # Change the COM port to the one used by the sensor
# obj.serial_open()               # Open the serial port with predefined setting for the strain sensor
# print(obj.serial_ipr_get_system_status())               # Print the sensor status
# obj.serial_ipr_start_binary_read()      # Start the binary datastream from the sensor
#
# # Create a parser object
# ipr_obj = IPRSensorDecoder()
#
# def generate_strain_data():
#     """Simulate strain sensor data"""
#     t = time.time()
#     # base = 0.5 * math.sin(2 * math.pi * 10 * t) + 0.05 * random.gauss(0, 1)
#     return {
#         'strain_x': ipr_obj.get_strain_xyz(0),
#         'strain_y': ipr_obj.get_strain_xyz(1),
#         'strain_z': ipr_obj.get_strain_xyz(2),
#         'strain_p1': 0,
#         'strain_p2': 0,
#         'strain_pdeg': random.uniform(-180, 180)
#     }
#
#
# def generate_accel_data():
#     """Simulate accelerometer data"""
#     t = time.time()
#     return {
#         'accel_x': 0.2 * math.sin(2 * math.pi * 5 * t) + 0.02 * random.gauss(0, 1),
#         'accel_y': 0.2 * math.cos(2 * math.pi * 5 * t) + 0.02 * random.gauss(0, 1),
#         'accel_z': 9.81 + 0.05 * random.gauss(0, 1)  # Gravity + noise
#     }
#
#
# def generate_env_data():
#     """Simulate environmental sensor data"""
#     return {
#         'v_batt': ipr_obj.get_environment(0),  # Battery voltage
#         'temperature': ipr_obj.get_environment(3),  # Celsius
#         'humidity': ipr_obj.get_environment(2),  # Percent
#         'pressure': ipr_obj.get_environment(1)  # hPa
#     }
#
#
# def pack_high_freq_data(strain_x, strain_y, strain_z, strain_p1, strain_p2, strain_pdeg,
#                         accel_x, accel_y, accel_z, timestamp_ns):
#     """
#     Pack high-frequency data (1000 Hz): 9 floats + timestamp
#     Total: 9*4 + 8 = 44 bytes per sample
#     """
#     return struct.pack(
#         '<9fQ',  # < = little-endian, 9f = 9 floats, Q = uint64
#         strain_x, strain_y, strain_z,
#         strain_p1, strain_p2, strain_pdeg,
#         accel_x, accel_y, accel_z,
#         timestamp_ns
#     )
#
#
# def pack_env_data(v_batt, temperature, humidity, pressure, timestamp_ns, sensor_id):
#     """
#     Pack environmental data (1 Hz): 4 floats + timestamp + sensor_id
#     Total: 4*4 + 8 + 1 = 25 bytes
#     """
#     return struct.pack(
#         '<4fQB',  # 4 floats, uint64, uint8
#         v_batt, temperature, humidity, pressure,
#         timestamp_ns,
#         sensor_id
#     )
#
#
# def on_connect(client, userdata, flags, reason_code, properties):
#     """Callback for when the client connects to the broker"""
#     if reason_code == 0:
#         print(f"✓ Connected successfully to {MQTT_BROKER}:{MQTT_PORT}")
#     else:
#         print(f"✗ Failed to connect: {reason_code}")
#
#
# def on_publish(client, userdata, mid, reason_code, properties):
#     """Callback for when a message is published"""
#     pass  # Can add logging here if needed
#
#
# def main():
#     # Connect to MQTT with new API
#     client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
#     client.username_pw_set(MQTT_USER, MQTT_PASS)
#     client.on_connect = on_connect
#     client.on_publish = on_publish
#
#     try:
#         client.connect(MQTT_BROKER, MQTT_PORT, 60)
#         client.loop_start()
#         time.sleep(1)  # Wait for connection
#     except Exception as e:
#         print(f"✗ Error connecting to MQTT broker: {e}")
#         print(f"  Make sure {MQTT_BROKER}:{MQTT_PORT} is reachable")
#         return
#
#     print(f"Sensor ID: {SENSOR_ID}")
#     print(f"High-frequency data: {SAMPLE_RATE} Hz (strain + accel)")
#     print(f"Environmental data: {ENV_SAMPLE_RATE} Hz (temp, humidity, pressure, battery)")
#     print("Press Ctrl+C to stop\n")
#
#     buffer_high_freq = []
#     last_env_time = 0
#     sample_interval = 1.0 / SAMPLE_RATE
#     sample_count = 0
#
#     try:
#         while True:
#             start_time = time.time()
#             timestamp_ns = int(time.time_ns())
#
#             ipr_obj.analyse_packet(obj.serial_ipr_read_telegram())
#             if ipr_obj.ipr_decoder_is_packet_valid():
#
#                 if ipr_obj.get_packet_type() == ipr_obj.TYPE_STRAIN:
#                     # ipr_obj.print_environment()
#                     # print(ipr_obj.get_strain_xyz(0), ' ; ', ipr_obj.get_strain_xyz(1), ' ; ', ipr_obj.get_strain_xyz(2))
#                     # Generate high-frequency sensor data
#                     strain_data = generate_strain_data()
#                     accel_data = generate_accel_data()
#
#                     # Pack high-frequency data
#                     packet = pack_high_freq_data(
#                         strain_data['strain_x'],
#                         strain_data['strain_y'],
#                         strain_data['strain_z'],
#                         strain_data['strain_p1'],
#                         strain_data['strain_p2'],
#                         strain_data['strain_pdeg'],
#                         accel_data['accel_x'],
#                         accel_data['accel_y'],
#                         accel_data['accel_z'],
#                         timestamp_ns
#                     )
#                     buffer_high_freq.append(packet)
#                     sample_count += 1
#
#                 # Send environmental data once per second
#                 if time.time() - last_env_time >= (1.0 / ENV_SAMPLE_RATE):
#                     if ipr_obj.get_packet_type() == ipr_obj.TYPE_ENVIRONMENT:
#
#                         env_data = generate_env_data()
#                         env_packet = pack_env_data(
#                             env_data['v_batt'],
#                             env_data['temperature'],
#                             env_data['humidity'],
#                             env_data['pressure'],
#                             timestamp_ns,
#                             SENSOR_ID
#                         )
#
#                         # Compress and send environmental data
#                         compressed_env = zlib.compress(env_packet, level=6)
#                         result = client.publish(f'sensor/{SENSOR_ID}/env', compressed_env, qos=1)
#
#                         if result.rc == mqtt.MQTT_ERR_SUCCESS:
#                             print(f"[ENV] Batt:{env_data['v_batt']:.2f}V Temp:{env_data['temperature']:.1f}°C "
#                                   f"Humidity:{env_data['humidity']:.1f}% Pressure:{env_data['pressure']:.1f}hPa")
#                         else:
#                             print(f"✗ Failed to publish environmental data: {result.rc}")
#
#                         last_env_time = time.time()
#
#             # Send high-frequency batch every second (1000 samples)
#             if len(buffer_high_freq) >= SAMPLE_RATE:
#                 # Combine all packets
#                 batch = b''.join(buffer_high_freq)
#
#                 # Compress
#                 compressed = zlib.compress(batch, level=6)
#
#                 # Publish to MQTT
#                 result = client.publish(f'sensor/{SENSOR_ID}/data', compressed, qos=1)
#
#                 if result.rc == mqtt.MQTT_ERR_SUCCESS:
#                     compression_ratio = len(batch) / len(compressed)
#                     bandwidth_kbps = (len(compressed) * 8) / 1024  # kbps
#                     print(f"[DATA] Sent {len(buffer_high_freq)} samples | "
#                           f"{len(batch)} → {len(compressed)} bytes | "
#                           f"{compression_ratio:.1f}x compression | "
#                           f"{bandwidth_kbps:.1f} kbps")
#                 else:
#                     print(f"✗ Failed to publish high-freq data: {result.rc}")
#
#                 buffer_high_freq = []
#
#             # Sleep to maintain sample rate
#             elapsed = time.time() - start_time
#             sleep_time = max(0, sample_interval - elapsed)
#             time.sleep(sleep_time)
#
#     except KeyboardInterrupt:
#         print("\n\nStopping...")
#
#         # Send any remaining data
#         if buffer_high_freq:
#             batch = b''.join(buffer_high_freq)
#             compressed = zlib.compress(batch, level=6)
#             client.publish(f'sensor/{SENSOR_ID}/data', compressed, qos=1)
#             print(f"Sent final {len(buffer_high_freq)} samples")
#
#         client.loop_stop()
#         client.disconnect()
#         print(f"Total samples sent: {sample_count}")
#
#
# if __name__ == "__main__":
#     main()
#