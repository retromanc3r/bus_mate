import serial
import time
import re

DEBUG = False  # Set to True to enable verbose debugging output
BP_PORT = "/dev/ttyACM0"  # Update this with your system's Bus Pirate serial port
BAUD_RATE = 115200

# BME280 I2C Address
BME280_ADDRESS = 0x77

# Compensation parameters (to be read from the sensor)
dig_T1 = dig_T2 = dig_T3 = 0

def open_serial_connection():
    """Open a serial connection to the Bus Pirate."""
    try:
        ser = serial.Serial(BP_PORT, BAUD_RATE, timeout=1)
        time.sleep(0.5)  # Allow Bus Pirate to initialize
        ser.reset_input_buffer()  # Flush any existing data
        print("[*] Serial connection established.")
        return ser
    except serial.SerialException as e:
        print(f"[!] Serial error: {e}")
        return None

def read_until_prompt(ser, timeout=3):
    """Read from the serial buffer until the Bus Pirate's command prompt is detected."""
    response = []
    timeout_time = time.time() + timeout  # Set timeout

    while time.time() < timeout_time:
        if ser.in_waiting > 0:
            new_data = ser.read(ser.in_waiting).decode(errors='ignore').strip()
            if new_data:
                response.append(new_data)
                if re.search(r"(I2C>|HiZ>)", new_data):
                    break  # Exit loop when we see the command prompt
        time.sleep(0.1)  # Prevent high CPU usage

    return "\n".join(response).strip()

def send_command(ser, command, delay=1):
    """Send a command to the Bus Pirate and capture the full I2C response while filtering noise."""
    ser.reset_input_buffer()  # Flush buffer before writing
    ser.write((command + "\r\n").encode())
    time.sleep(delay)  # Allow response time

    response = []
    timeout = time.time() + 3  # 3-second timeout

    while time.time() < timeout:
        if ser.in_waiting > 0:
            new_data = ser.read(ser.in_waiting).decode(errors='ignore').strip()
            if new_data:
                if re.match(r'^\s*(\d+\.\d+V\s*)+$', new_data) or "GND" in new_data:
                    continue  # Ignore voltage readings and interactive noise
                response.append(new_data)
                if DEBUG:
                    print(f"[DEBUG] Captured Response Chunk:\n{new_data}")
                if "I2C>" in new_data:
                    break
        time.sleep(0.05)  # Reduce sleep time to speed up response handling

    full_response = "\n".join(response).strip()
    if DEBUG:
        print(f"[DEBUG] Full Command Response:\n{full_response}")
    return full_response

def extract_rx_data(response):
    """Extract all RX data (e.g., 'RX: 0x60') from a multiline Bus Pirate response."""
    if DEBUG:
        print(f"[DEBUG] Raw Response Before Processing:\n{repr(response)}")
    
    response = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', response)  # Remove ANSI escape sequences
    response = " ".join(response.split())  # Normalize whitespace
    
    rx_matches = re.findall(r'RX:\s*(0x[0-9A-Fa-f].*(?:\s0x[0-9A-Fa-f]+)*)', response)
    
    if DEBUG:
        print(f"[DEBUG] Found RX Matches: {rx_matches}")
    
    if rx_matches:
        extracted_bytes = re.findall(r'0x[0-9A-Fa-f]+', rx_matches[0])  # Extract full hex bytes
        return extracted_bytes  # Return all extracted RX values as a list
    
    if DEBUG:
        print("[!] No RX data found in response.")
        print(f"[DEBUG] Cleaned Response Buffer:\n{response}")
    return None

def get_chip_id(ser):
    """Interact with the BME280 to retrieve the Chip ID directly from send_command()."""
    print("[*] Communicating with BME280...")
    print("[*] Reading Chip ID...")
    send_command(ser, "[0xEE 0xD0]")  # Send command first (ignore the echoed response)
    chip_id_response = send_command(ser, "[0xEFr:1]")  # Now, actually capture the response
    chip_id = extract_rx_data(chip_id_response)
    if chip_id:
        print(f"[*] Chip ID: {chip_id[0]}")
        if chip_id[0] != "0x60":
            print(f"[!] Warning: Unexpected Chip ID! Expected 0x60, got {chip_id[0]}")
        return chip_id[0]
    else:
        print("[!] Failed to read Chip ID from response!")
        if DEBUG:
            print(f"[DEBUG] Full Response Buffer:\n{repr(chip_id_response)}")
        return None

def configure_bme280(ser):
    """Configure the BME280 to start measurements (needed before reading data)."""
    if DEBUG:
        print("[*] Configuring BME280 for measurement...")
    send_command(ser, "[0xEE 0xF4 0x55]")  # Write 0x55 to control register 0xF4 to start measurement
    time.sleep(1)  # Wait for measurement to complete
    control_status = extract_rx_data(send_command(ser, "[0xEFr:1]"))  # Read back the control register
    if DEBUG:
        print(f"[*] Control Register Status: {control_status[0]}")

def read_sensor_data(ser):
    """Read 8 bytes from the BME280 starting at register 0xF7."""
    send_command(ser, "[0xEE 0xF7]")  # Request data from register 0xF7
    raw_sensor_data = send_command(ser, "[0xEFr:8]")  # Read 8 bytes
    time.sleep(1)  # Wait for data to be read

    if DEBUG:
        print(f"[DEBUG] Raw Sensor Response: {raw_sensor_data}")
    
    extracted_data = extract_rx_data(raw_sensor_data)
    if extracted_data is None:
        print(f"[!] Error: Expected 8 bytes, got {0}")
        return None

    if DEBUG:
        print(f"[DEBUG] Extracted Sensor Data (Raw Hex): {extracted_data}")

    sensor_bytes = [int(byte, 16) for byte in extracted_data[:8]]  # Convert hex values to integers
    
    if DEBUG:
        print(f"[*] Raw Sensor Data (Parsed): {sensor_bytes}")

    adc_T = (sensor_bytes[3] << 16) | (sensor_bytes[4] << 8) | sensor_bytes[5]
    adc_T >>= 4  # Right shift to align bits
    
    if DEBUG:
        print(f"[*] Parsed ADC Temperature: {adc_T}")

    return adc_T

def read_calibration_data(ser):
    """Read the BME280 calibration data necessary for temperature compensation."""
    global dig_T1, dig_T2, dig_T3
    if DEBUG:
        print("[*] Reading calibration data...")
    
    send_command(ser, "[0xEE 0x88]")  # Request the first block of calibration data (6 bytes from register 0x88)
    raw_calib_data = send_command(ser, "[0xEFr:6]")  # Read first 6 bytes

    if DEBUG:
        print(f"[DEBUG] Raw Calibration Response: {raw_calib_data}")

    extracted_data = extract_rx_data(raw_calib_data)
    if extracted_data is None or len(extracted_data) < 6:
        print(f"[!] Error: Expected 6 bytes, got {len(extracted_data) if extracted_data else 0}")
        print("[!] Failed to read calibration data!")
        return False

    if DEBUG:
        print(f"[DEBUG] Extracted Calibration Bytes: {extracted_data}")

    calib_data_bytes = [int(byte, 16) for byte in extracted_data[:6]]  # Convert hex values to integers

    dig_T1 = (calib_data_bytes[1] << 8) | calib_data_bytes[0]
    dig_T2 = (calib_data_bytes[3] << 8) | calib_data_bytes[2]
    dig_T3 = (calib_data_bytes[5] << 8) | calib_data_bytes[4]

    if DEBUG:
        print(f"[*] Calibration Data: dig_T1={dig_T1}, dig_T2={dig_T2}, dig_T3={dig_T3}")
        
    return True

def read_temperature(ser):
    """Read raw temperature data from the BME280 and apply compensation."""
    global dig_T1, dig_T2, dig_T3
    configure_bme280(ser)  # Ensure the sensor is configured before reading
    adc_T = read_sensor_data(ser)  # Read raw temperature data
    if adc_T is None:
        print("[!] Failed to extract full temperature data!")
        return None

    var1 = (((adc_T >> 3) - (dig_T1 << 1)) * dig_T2) >> 11
    var2 = (((((adc_T >> 4) - dig_T1) * ((adc_T >> 4) - dig_T1)) >> 12) * dig_T3) >> 14
    t_fine = var1 + var2
    temp = (t_fine * 5 + 128) >> 8
    temperature = temp / 100.0

    print(f"[*] Temperature: {temperature:.2f}°C")
    return temperature

def initialize_bus_pirate(ser):
    """Initialize the Bus Pirate, enable power, and ensure communication is working."""
    print("[*] Checking Bus Pirate state...")
    ser.reset_input_buffer()  # Flush buffer before reading
    ser.write(b"\r\n")  # Wake up Bus Pirate
    time.sleep(1)

    response = ""
    for attempt in range(5):
        ser.write(b"\r\n")  # Retry sending a newline
        time.sleep(1)  # Allow response to process
        response = ser.read(ser.in_waiting).decode(errors='ignore').strip()
        if response:
            break  # If we get a response, continue
        print(f"[!] No response detected, retrying... ({attempt + 1}/5)")
        time.sleep(2)

    if DEBUG:
        print(f"[DEBUG] Bus Pirate Initial Response:\n{response}")

    if not response.strip():
        print("[!] No valid response received from Bus Pirate! Try unplugging and re-plugging it.")
        ser.close()
        return None

    if "VT100 compatible color mode?" in response:
        print("[*] VT100 prompt detected, disabling color mode...")
        ser.write(b"n\r\n")  # Send "n" to disable color mode
        time.sleep(1.5)
        response = ser.read(ser.in_waiting).decode(errors='ignore').strip()

    if "I2C>" in response:
        print("[*] Bus Pirate is already in I2C mode.")
    elif "HiZ>" in response:
        print("[*] Bus Pirate is in HiZ mode, switching to I2C...")
        ser.reset_input_buffer()  # Flush buffer before switching mode
        time.sleep(1)
        ser.write(b"m\r\n")  # Enter mode selection menu
        time.sleep(2.5)  # Allow the menu to appear
        response = ser.read(ser.in_waiting).decode(errors='ignore').strip()
        if DEBUG:
            print(f"[DEBUG] Mode Selection Response:\n{response}")

        if "Mode selection" not in response:
            print("[!] Unexpected response while selecting mode!")
            ser.close()
            return None

        ser.write(b"5\r\n")  # Select I2C mode (option 5)
        time.sleep(3.5)  # Allow mode switching
        response = ser.read(ser.in_waiting).decode(errors='ignore').strip()
        if "Use previous settings?" in response:
            ser.write(b"n\r\n")  # Choose "No" to set fresh settings
            time.sleep(2)

        response = ser.read(ser.in_waiting).decode(errors='ignore').strip()
        if "I2C speed" in response:
            ser.write(b"400\r\n")  # Set I2C speed to 400kHz
            time.sleep(2)

        response = ser.read(ser.in_waiting).decode(errors='ignore').strip()
        if "Clock stretching" in response:
            ser.write(b"1\r\n")  # Choose "OFF" (default)
            time.sleep(2)

        time.sleep(3)  # Ensure transition completes
        ser.reset_input_buffer()  # Final buffer flush
        ser.write(b"\r\n")
        time.sleep(1)
        response = ser.read(ser.in_waiting).decode(errors='ignore').strip()
        
        if "I2C>" not in response:
            print(f"[!] Unexpected response: {response}")
            print("[!] Bus Pirate failed to enter I2C mode!")
            ser.close()
            return None

    print("[*] Bus Pirate is now in I2C mode.")
    print("[*] Enabling power supply to BME280...")
    ser.write(b"W\r\n")  # Send `W` command
    time.sleep(2)  # Allow time for power menu
    response = ser.read(ser.in_waiting).decode(errors='ignore').strip()
    if "Volts" in response:
        ser.write(b"3.30\r\n")  # Set voltage to 3.30V
        time.sleep(2)
    response = ser.read(ser.in_waiting).decode(errors='ignore').strip()
    if "Maximum current" in response:
        ser.write(b"\r\n")  # Press enter to accept default current setting
        time.sleep(2)
    response = ser.read(ser.in_waiting).decode(errors='ignore').strip()
    if "Power supply:Enabled" not in response:
        print("[!] Warning: Power supply may not have been enabled correctly!")
    print("[*] Power supply to BME280 is now enabled.")
    return ser

def i2c_write(ser, address, data):
    """Perform an I2C write to the given address with data."""
    cmd = f"[0x{address:02X} {' '.join(f'0x{byte:02X}' for byte in data)}]"
    send_command(ser, cmd, delay=0.1)  # No need to return echoed response

def i2c_read(ser, address, num_bytes):
    """Perform an I2C read while ensuring RX data is captured before being lost."""
    ser.reset_input_buffer()  # Flush buffer before reading
    cmd = f"[0x{address:02X}r:{num_bytes}]"
    send_command(ser, cmd, delay=0.2)

    response = ""  # Accumulate response
    timeout = time.time() + 2  # Set timeout
    found_rx = False  # Track if RX data was found

    while time.time() < timeout:
        time.sleep(0.1)  # Allow response to arrive
        if ser.in_waiting > 0:
            new_data = ser.read(ser.in_waiting).decode(errors='ignore').strip()
            if new_data:
                if re.match(r'^\s*(3\.[23]V\s*)+$', new_data):
                    continue  # Ignore voltage readings
                response += new_data + "\n"  # Accumulate response
                if DEBUG:
                    print(f"[DEBUG] Received Data Chunk:\n{new_data}")
                match = re.search(r'RX:\s*(0x[0-9A-Fa-f]+)', response)
                if match:
                    extracted_value = match.group(1)
                    found_rx = True
                    if DEBUG:
                        print(f"[DEBUG] Extracted I2C Data: {extracted_value}")
                    break  # Stop reading as soon as we capture RX data

    if not found_rx:
        print(f"[!] Error: Timeout while waiting for response from 0x{address:02X}")
        if DEBUG:
            print(f"[DEBUG] Full Response Captured:\n{response}")
        return None

    return extracted_value

def clean_response(response):
    """Clean up unwanted characters, including voltage readings and ANSI escape sequences."""
    response = re.sub(r'\x1B\[?.*?[a-zA-Z]', '', response)  # Remove ANSI escape sequences
    response = response.replace("\r", "").replace("\n", " ")  # Normalize whitespace
    response = re.sub(r'(\s*3\.[23]V\s*)+', '', response)  # Remove voltage readings like "3.3V" or "3.2V"
    match = re.findall(r'0x[0-9A-Fa-f]+', response)  # Extract valid I2C response values (hex data)
    return " ".join(match) if match else "No Data"

def main():
    """Main function to initialize the Bus Pirate and read temperature data from the BME280."""
    ser = open_serial_connection()
    if not ser:
        return

    if initialize_bus_pirate(ser):
        print("[*] I2C initialization complete.")
        print("[*] Running an I2C scan...")
        response = send_command(ser, "scan")
        response = clean_response(response).replace("I2C>", "").strip()
        print(f"[*] I2C Address: {response}")
        get_chip_id(ser)  # Read the calibration data from the BME280 (Chip ID)
        configure_bme280(ser)  # Configure the BME280 for measurement mode
        adc_T = read_sensor_data(ser)  # Read the raw sensor data from the BME280
        if adc_T is not None:
            if DEBUG:
                print(f"[*] Temperature ADC Value: {adc_T}")
        else:
            print("[!] Error reading sensor data.")
        if read_calibration_data(ser):
            while True:
                read_temperature(ser)
                time.sleep(1)
        else:
            print("[!] Error reading calibration data.")
    else:
        print("[!] Error initializing the Bus Pirate.")

    ser.close()  # Close the serial connection
    print("[*] Serial connection closed.")

if __name__ == "__main__":
    main()
