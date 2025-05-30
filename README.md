# Serial Data Logger for Phyto Node

`serial-data-logger` is a Python tool designed to read, process, and export serial data transmitted over a serial port. It utilizes the FlatBuffers serialization library to decode structured data, converts raw byte measurements into analog voltages, and exports the results in JSON or CSV formats. This tool serves as a data receiver and logger on a Raspberry Pi, interfacing with the phyto-node project available at https://github.com/ChristophKarlHeck/phyto-node.

---

## Features

- **Serial Communication**: Reads structured binary data from a serial port.
- **FlatBuffers Decoding**: Decodes serialized messages using the FlatBuffers library.
- **Dynamic File Naming**: The output file is dynamically named based on the node number and the start time of logging (e.g., P1_2024-11-06 11:58:05.csv).
- **Data Conversion**: Converts 3-byte raw data into analog voltages using configurable parameters (`databits`, `vref`, `gain`).
- **Custom Export Options**:
  - Exports processed data to either JSON or CSV files.
  - Appends to existing files if specified.
- **Console Visualization**: Prints processed data in a human-readable format.

---

## Requirements

- **Python**: Version 3.8 or later
- **Libraries**:
  - `pyserial`
  - `flatbuffers`

Install dependencies using the provided `requirements.txt` file:
```bash
pip install -r requirements.txt
```
## Command-Line Arguments

| **Argument**   | **Required** | **Description**                                                         |
|-----------------|--------------|-------------------------------------------------------------------------|
| `--port`       | Yes          | Serial port to read from (e.g., `/dev/ttyS0` or `COM3`).                |
| `--baudrate`   | No           | Baud rate for serial communication (default: `115200`).                |
| `--format`     | Yes          | Output format: `csv` or `json`.                                         |
| `--path`       | No           | Path to save the output file (default: current directory `.`).          |

## Example Commands
### Log Data to a CSV File
Save to the current directory:
```bash
python3 main.py --port /dev/ttyS0 --baudrate 115200 --format csv
```
Save to a custom directory:
```bash
python3 main.py --port /dev/ttyACM1 --baudrate 115200 --format csv --path /media/chris/e110508e-b067-4ed5-87a8-5c548bdd8f77
```
### Log Data to a JSON File
```bash
python3 main.py --port /dev/ttyS0 --baudrate 115200 --format json
```

## Docker
### Build the Docker Image
```bash
docker build -t serial-data-logger:python3.11 .
```
### Run in Docker
```bash
docker run --name serial-data-logger-container \
  --restart=always \
  --device=/dev/ttyACM1:/dev/ttyACM1 \
  -v /media/chris/e110508e-b067-4ed5-87a8-5c548bdd8f77:/media/chris/e110508e-b067-4ed5-87a8-5c548bdd8f77 \
   --log-opt max-size=10m \
  --log-opt max-file=3 \
  -d \
  serial-data-logger:python3.11 \
  --port /dev/ttyACM1 --baudrate 115200 --format csv --path /media/chris/e110508e-b067-4ed5-87a8-5c548bdd8f77
```
### Explanation of the `docker run` Command:
1. `--name serial-data-logger-container`: Assigns a name to the container (`serial-data-logger-container`).
2. `--restart=always`: Ensures the container restarts automatically if it crashes.
3. `--device=/dev/ttyACM1:/dev/ttyACM1`: Gives the container access to the `/dev/ttyACM1` serial device on the host.
4. `-v /media/chris/e110508e-b067-4ed5-87a8-5c548bdd8f77:/media/chris/e110508e-b067-4ed5-87a8-5c548bdd8f77`: Mounts the host directory for saving output (e.g., CSV files) to the same path inside the container.
5. `serial-data-logger:python3.11`: Specifies the image to use for the container (`serial-data-logger` with Python 3.11).
6. <b>Script Arguments</b>
   * `--port /dev/ttyACM1`: Specifies the serial port.
   * `--baudrate 115200`: Sets the baud rate.
   * `--format csv`: Specifies the output format.
   * `--path /media/chris/e110508e-b067-4ed5-87a8-5c548bdd8f77`: Sets the directory where the output files will be saved.

### Check if the container is running

```bash
docker ps
```

### See Docker Container logs

```bash
docker logs -f serial-data-logger-container
```

## How It Works

### Data Workflow

1. **Serial Data Read**:
   - Reads structured binary data over a serial connection using `serial.Serial`.

2. **Dynamic File Naming**:

    - The filename is generated dynamically based on the node number and the start time of data logging

2. **Decoding**:
   - Decodes data using FlatBuffers.

3. **Processing**:
   - Converts 3-byte raw byte measurements into analog voltages using:
     - Configurable `databits` (default: `8388608`).
     - Configurable `vref` (default: `2.5V`).
     - Configurable `gain` (default: `4.0`).

4. **Output**:
   - Exports processed data to JSON or CSV, appending to existing files if applicable.
