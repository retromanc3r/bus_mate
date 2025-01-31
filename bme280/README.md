# BME280 Sensor Project

This project is for interfacing with the BME280 sensor using a Bus Pirate.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Wiring Diagram](#wiring-diagram)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Introduction

The BME280 sensor is used for measuring temperature, humidity, and pressure. This project provides a way to interface with the BME280 sensor using a Bus Pirate.

## Bus Pirates
 - BPv3 (Supported)
 - BPv4 (???)
 - BPv5 (Supported)
 - BPv6 (???)

## Features

- Read temperature, humidity, and pressure data from the BME280 sensor.
- Interface with the sensor using a Bus Pirate.
- Simple and easy-to-use code.

## Requirements

- Bus Pirate
- BME280 sensor
- Python 3.x
- `pyserial` library

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/bme280-project.git
    cd bme280-project
    ```

2. Install the required Python libraries:
    ```sh
    pip install pyserial
    ```

## Usage

1. Connect the BME280 sensor to the Bus Pirate.
2. Run the Python script to read data from the sensor:
    ```sh
    python read_bme280.py
    ```

## Bill of Materials (BOM)

Below is the list of components required for this project:

| Item             | Quantity | Description                          |
|------------------|----------|--------------------------------------|
| Bus Pirate       | 1        | A versatile tool for communicating with various devices. |
| BME280 Sensor    | 1        | Sensor for measuring temperature, humidity, and pressure. |
| Jumper Wires     | 5        | For connecting the BME280 sensor to the Bus Pirate. |
| Breadboard       | 1        | Optional, for easier wiring and prototyping. |

## Wiring Diagram

Below is the wiring diagram for connecting the BME280 sensor to the Bus Pirate:

| BME280 Pin | Bus Pirate Pin |
|------------|----------------|
| VCC        | 3.3V           |
| GND        | GND            |
| SCL        | CLK            |
| SDA        | MOSI           |
| CSB        | Not connected  |
| SDO        | Not connected  |


## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.

## Author

@retromanc3r

## Acknowledgements

Special thanks to GitHub Copilot for assistance in code optimization and debugging.