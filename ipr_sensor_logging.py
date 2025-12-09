import os
import threading
import queue
import time
from datetime import datetime

MAX_FILE_SIZE = 150e6           # 150 MB (~2.5h)
SAVE_FILE_EVERY_SIZE = 100e3    # 100 kB


class IprSensorSerialLoggerThread(threading.Thread):
    """Thread that continuously reads from serial port and logs to file"""

    def __init__(self, serial_port, data_queue, debug=False):
        """
        Initialize the logger thread.

        Args:
            serial_port: Your serial port object (with read() method)
            data_queue (queue.Queue): Queue for passing data to main thread
            debug (bool): Print data to console if True
        """
        super().__init__(daemon=True)
        self.serial_port = serial_port
        self.data_queue = data_queue
        self.debug = debug

        # Control flags
        self._stop_event = threading.Event()
        self._logging_enabled = threading.Event()
        self._logging_enabled.set()  # Start with logging enabled

    def run(self):
        """Main thread loop - this runs continuously"""
        log_file_handle = None
        logfile_size_counter = 0

        # Prepare the folder to save the data
        current_directory = os.getcwd()
        path_logfile = current_directory + "/Logging_data/"
        os.makedirs(path_logfile, exist_ok=True)
        print("Saving the logging file to: {}".format(path_logfile))

        try:
            while not self._stop_event.is_set():
                if self._logging_enabled.is_set():
                    # Logging is enabled - open file if needed
                    if log_file_handle is None:
                        # Get new filename
                        logfile_name = self.get_new_filename()
                        log_file_handle = open(path_logfile + logfile_name, "ab")

                    # Read from serial port
                    try:
                        # Read data from sensor
                        data = self.serial_port.read(1)

                        if data:
                            # Write data to file
                            log_file_handle.write(data)
                        else:
                            time.sleep(0.001)  # No data, small delay

                        # Check file size every x KB
                        if logfile_size_counter >= SAVE_FILE_EVERY_SIZE:
                            logfile_size_counter = 0
                            # Check file size once in a while
                            filesize = os.path.getsize(path_logfile + logfile_name)
                            if filesize >= MAX_FILE_SIZE:
                                f.close()
                                logfile_name = self.get_new_filename()
                                f = open(path_logfile + logfile_name, "ab")
                        else:
                            logfile_size_counter += 1

                    except Exception as e:
                        print(f"Error reading serial: {e}")
                        time.sleep(0.1)
                else:
                    # Logging disabled - close file if open
                    if log_file_handle is not None:
                        log_file_handle.close()
                        log_file_handle = None
                    time.sleep(0.01)  # Wait while paused

            # Thread stopping - close file if open
            if log_file_handle is not None:
                log_file_handle.close()

        except Exception as e:
            print(f"Fatal error in logger thread: {e}")
            if log_file_handle is not None:
                log_file_handle.close()

    # Control methods
    def start_logging(self):
        """Enable logging"""
        self._logging_enabled.set()
        print("Sensor recording enabled")

    def stop_logging(self):
        """Disable logging (thread keeps running)"""
        self._logging_enabled.clear()
        print("Sensor recording disabled")

    def shutdown(self):
        """Stop the thread completely"""
        self._stop_event.set()
        print("Thread shutting down")

    def is_logging(self):
        """Check if currently logging"""
        return self._logging_enabled.is_set()

    def get_status(self):
        """Get current status"""
        if not self.is_alive():
            return "STOPPED"
        elif self.is_logging():
            return "LOGGING"
        else:
            return "IDLE"

    def get_new_filename(self):
        now = datetime.now()
        date_time_filename = "{}{}{}_{}-{}-{}.bin".format(now.year, now.month, now.day, now.hour, now.minute,
                                                          now.second)
        print(date_time_filename)
        return date_time_filename
