# Bus Mate - Universal Bus Pirate Automation Suite

Bus Mate is a universal automation suite designed to streamline communication with various sensors and peripherals using the Bus Pirate 5. This project provides a collection of Python scripts to automate tasks such as sensor initialization, data retrieval, and I2C/SPI/UART communication.

## Features

- ✅ Supports multiple protocols: I2C, SPI, UART
- ✅ Automates Bus Pirate initialization & configuration
- ✅ Includes ready-to-use sensor scripts (BME280, more coming!)
- ✅ Provides debugging tools for serial communication
- ✅ Continuous polling & real-time data visualization (future feature)

## Supported Devices

| Device                        | Protocol | Status       |
|-------------------------------|----------|--------------|
| BME280 (Temp/Pressure/Humidity)| I2C      | ✅ Implemented|
| ATECC608A (Crypto Co-Processor) | I2C    | 🚧 In Progress|
| MCP9808 (High-Precision Temp) | I2C      | 🔜 Planned|
| BMP388 (Barometric Pressure)  | I2C      | 🔜 Planned|
| Generic UART Devices          | UART     | 🔜 Planned    |
| Generic SPI Devices           | SPI      | 🔜 Planned    |

## Hardware Requirements

- Bus Pirate 5 (or compatible device)
- Supported sensors and peripherals
- Computer with Python 3 installed

## Software Requirements

- Python libraries: `pyserial`, `time`, `re`

Install dependencies using:

```sh
pip install pyserial
```

## Installation

Clone this repository:

```sh
git clone https://github.com/yourusername/bus-mate.git
cd bus-mate
```

Connect the Bus Pirate to your system.

Identify the correct serial port:

```sh
ls /dev/ttyACM*  # Linux/macOS
Get-WMIObject Win32_SerialPort  # Windows
```

Update the serial port in the script:

```python
BP_PORT = "/dev/ttyACM0"  # Change if needed
```

Run a script (e.g., BME280 interface):

```sh
python3 bpi2c_bme280.py
```

## Example: Running the BME280 Script

1. Initializes the Bus Pirate and enables I2C mode.
2. Performs an I2C scan to detect connected devices.
3. Validates the BME280 Chip ID to ensure proper communication.
4. Reads calibration data from the BME280 sensor.
5. Continuously reads temperature data, applying compensation formulas.

### Expected Output

```
[*] Serial connection established.
[*] Checking Bus Pirate state...
[*] Bus Pirate is already in I2C mode.
[*] Bus Pirate is now in I2C mode.
[*] Enabling power supply to BME280...
[*] Power supply to BME280 is now enabled.
[*] I2C initialization complete.
[*] Running an I2C scan...
[*] I2C Address: 0x77 0xEE 0xEF
[*] Communicating with BME280...
[*] Reading Chip ID...
[*] Chip ID: 0x60
[*] Temperature ADC Value: 524968
[*] Temperature: 23.36°C
```

## Troubleshooting

1. **Bus Pirate is not detected?**
    - Check if the correct port is used (`/dev/ttyACM0` or `COMx`).
    - Run `dmesg | grep tty` on Linux to list active serial ports.

2. **No I2C device detected?**
    - Ensure the sensor is properly wired and powered.
    - Try enabling the power supply manually in Bus Pirate (`W` command).

3. **Incorrect temperature readings?**
    - Verify calibration values are correctly read.
    - Check sensor power (should be 3.3V).

## Future Improvements

- Expand support for more sensors and bus protocols
- Improve error handling and robustness
- Implement logging and data visualization tools
- Develop a GUI for ease of use

🚀 Happy Hacking with Bus Mate!
