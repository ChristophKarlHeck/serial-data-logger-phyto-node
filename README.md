# Serial Data Logger for Phyto Node Classifier

`serial-data-logger` is a Python-based tool for reading, processing, and exporting serial data transmitted via a serial port. It decodes structured data using the FlatBuffers serialization library, converts raw byte measurements into analog voltages, and exports the results to JSON or CSV formats.

---

## Features

- **Serial Communication**: Reads structured binary data from a serial port.
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
| `--file`       | Yes          | Output file name (e.g., `measurement`).                |
| `--format`     | Yes          | Output format: `csv` or `json`.                                         |

## Example Commands
### Log Data to a CSV File
```bash
python3 main.py --port /dev/ttyS0 --baudrate 115200 --file measurement --format csv
```
### Log Data to a JSON File
```bash
python3 main.py --port /dev/ttyS0 --baudrate 115200 --file measurement --format json
```

## How It Works

### Data Workflow

1. **Serial Data Read**:
   - Reads structured binary data over a serial connection using `serial.Serial`.

2. **Decoding**:
   - Decodes data using FlatBuffers.

3. **Processing**:
   - Converts 3-byte raw byte measurements into analog voltages using:
     - Configurable `databits` (default: `8388608`).
     - Configurable `vref` (default: `2.5V`).
     - Configurable `gain` (default: `4.0`).

4. **Output**:
   - Exports processed data to JSON or CSV, appending to existing files if applicable.
