import argparse
import serial
import flatbuffers
import json
import csv
import os
import time
from datetime import datetime, timedelta
from SerialMail.SerialMail import SerialMail
from SerialMail.Value import Value

def extract_serial_mail_data(serial_mail):
    # Extract voltage values (inputs)
    ch0_length = serial_mail.Ch0Length()
    raw_input_bytes_ch0 = []
    for i in range(ch0_length):
        ch0 = serial_mail.Ch0(i)
        byte_dict = {"Data0": ch0.Data0(), "Data1": ch0.Data1(), "Data2": ch0.Data2()}
        raw_input_bytes_ch0.append(byte_dict)

    ch1_length = serial_mail.Ch1Length()
    raw_input_bytes_ch1 = []
    for i in range(ch1_length):
        ch1 = serial_mail.Ch1(i)
        byte_dict = {"Data0": ch1.Data0(), "Data1": ch1.Data1(), "Data2": ch1.Data2()}
        raw_input_bytes_ch1.append(byte_dict)

    voltages_ch0, measurements_ch0 = get_analog_inputs(raw_input_bytes_ch0)
    voltages_ch1, measurements_ch1 = get_analog_inputs(raw_input_bytes_ch1)

    # Extract other fields
    node = int(serial_mail.Node())

    return voltages_ch0, voltages_ch1, raw_input_bytes_ch0, raw_input_bytes_ch1, measurements_ch0, measurements_ch1, node


def read_serial_mail(serial_connection):
    """
    Reads a serialized FlatBuffers message from the serial connection and decodes it.
    
    The function uses a synchronization marker (0xAAAA) to align with the start of a valid message,
    reads the size field to determine the message length, and then processes the message if valid.

    Args:
        serial_connection: The serial connection object.

    Returns:
        A SerialMail object if a valid message is read and decoded, None otherwise.
    """
    buffer = bytearray()
    sync_marker = b'\xAA\xAA'

    while True:
        try:
            # Read data from the serial port
            chunk = serial_connection.read(1024)  # Adjust chunk size as needed
            if not chunk:
                continue  # Wait for data if nothing is read
            buffer.extend(chunk)

            # Synchronize to the marker
            marker_index = buffer.find(sync_marker)
            if marker_index != -1:
                buffer = buffer[marker_index + len(sync_marker):]  # Align to the start of the message
            else:
                if len(buffer) > 2048:  # Avoid infinite buffer growth
                    buffer.clear()
                continue  # Wait for synchronization

            # Check if there is enough data to read the size field (4 bytes)
            if len(buffer) < 4:
                continue  # Not enough data for size field

            # Read the size field (first 4 bytes after the sync marker)
            size = int.from_bytes(buffer[:4], byteorder='little')

            # Validate the size field
            if size < 24 or size > 1024:  # Adjust limits based on schema expectations
                print(f"Invalid message size: {size}. Skipping bytes.")
                buffer.pop(0)  # Skip one byte and keep searching
                continue

            # Check if the full message is available
            if len(buffer) < size + 4:
                continue  # Wait for more data

            # Extract the message
            message = buffer[4:size + 4]
            buffer = buffer[size + 4:]  # Remove processed message

            # Decode the FlatBuffers message
            try:
                serial_mail = SerialMail.GetRootAs(message, 0)
                return serial_mail  # Return the decoded object
            except Exception as e:
                print(f"Failed to decode FlatBuffers data: {e}")
                continue

        except Exception as e:
            print(f"Error while reading serial data: {e}")
            return None


def get_analog_inputs(raw_input_bytes, databits=8388608, vref=2.5, gain=4.0):
    """
    Calculate analog values from 3-byte measurements.

    Args:
        byte_inputs (list of list of int): List of 3-byte measurements, where each measurement is a list of three uint8 values.
        databits (int): Number of data bits (e.g., 24 for 24-bit resolution).
        vref (float): Reference voltage.
        gain (float): Gain applied to the measurement.

    Returns:
        list of float: Calculated analog voltages in millivolts.
    """
    inputs = []
    measurements = []

    for byte_dict in raw_input_bytes:
        # Extract the bytes from the dictionary
        byte0 = byte_dict["Data0"]
        byte1 = byte_dict["Data1"]
        byte2 = byte_dict["Data2"]

        # Combine the 3 bytes into a single integer
        measurement = ((byte0 << 16) | (byte1 << 8) | (byte2))
        measurements.append(measurement)

        # Calculate the voltage
        voltage = (float(measurement) / databits - 1)  # Normalize measurement
        voltage = voltage * vref / gain  # Apply reference voltage and gain
        voltage *= 1000  # Convert to millivolts

        inputs.append(round(voltage,4))

    return inputs, measurements


def write_to_json(filename, voltages_ch0, voltages_ch1, raw_input_bytes_ch0, raw_input_bytes_ch1, measurements_ch0, measurements_ch1, node):

    ch0_value = measurements_ch0[0] if len(measurements_ch0) == 1 else measurements_ch0
    ch1_value = measurements_ch1[0] if len(measurements_ch1) == 1 else measurements_ch1

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")

    # Prepare data to save
    data = {
        "Datetime": timestamp,
        "RawInputBytesCh0": raw_input_bytes_ch0,
        "MeasurementCh0": ch0_value,
        "VoltagesCh0": voltages_ch0,  # Keep as a list of dicts
        "RawInputBytesCh1": raw_input_bytes_ch1,
        "MeasurementCh1": ch1_value,
        "VoltagesCh1": voltages_ch0,  # Keep as a list of dicts
        "Node": node
    }

    # Check if the file exists and initialize if necessary
    if not os.path.isfile(filename):
        with open(filename, mode="w") as jsonfile:
            json.dump([], jsonfile)  # Write an empty JSON array

    # Read existing content
    with open(filename, mode="r") as jsonfile:
        try:
            existing_data = json.load(jsonfile)
            if not isinstance(existing_data, list):
                raise ValueError("JSON file must contain a list at the root.")
        except json.JSONDecodeError:
            existing_data = []  # If file is empty or invalid, start with an empty list

    # Append the new record
    existing_data.append(data)

    # Write the updated JSON array back to the file
    with open(filename, mode="w") as jsonfile:
        json.dump(existing_data, jsonfile, indent=4)  # Write with formatting for readability


def write_to_csv(filename, measurements_ch0, measurements_ch1, last_timestep):
    # Check if the file exists to decide whether to write a header

    file_exists = os.path.isfile(filename)

    assert len(measurements_ch0) == len(measurements_ch1), "Channels must have the same length."

    # Open the CSV file in append mode
    with open(filename, mode="a", newline="") as csvfile:
        # Define CSV fieldnames and writer
        fieldnames = ["datetime", "CH1", "CH2"]
        csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header only if the file does not exist
        if not file_exists:
            csv_writer.writeheader()

        # Get the current timestamp with microseconds
        timestamp = datetime.now()

        increment = (timestamp-last_timestep) / len(measurements_ch0)

        # Write the data row
        for ch0, ch1 in zip(measurements_ch0, measurements_ch1):
            csv_writer.writerow({
                "datetime": last_timestep.strftime("%Y-%m-%d %H:%M:%S:%f"),
                "CH1": ch0,
                "CH2": ch1
            })
            last_timestep += increment

    return timestamp


def print_serial_mail_data(voltages_ch0, voltages_ch1, raw_input_bytes_ch0, raw_input_bytes_ch1, node):
    # Print data to the console in the specified format
    print("\nReceived SerialMail:")
    print(f"Node:{node}")

    print(f"RawInputBytesCh0 ({len(raw_input_bytes_ch0)}):")
    for i, raw_input_byte in enumerate(raw_input_bytes_ch0):
        print(f"  Input {i}: ({raw_input_byte['Data0']}, {raw_input_byte['Data1']}, {raw_input_byte['Data2']})")

    print(f"InputVoltagesCh0 ({len(voltages_ch0)}):")
    for i, voltage in enumerate(voltages_ch0, start=1):
        print(f"  InputVoltage {i}: {voltage:.3f}")

    print(f"RawInputBytesCh1 ({len(raw_input_bytes_ch1)}):")
    for i, raw_input_byte in enumerate(raw_input_bytes_ch1):
        print(f"  Input {i}: ({raw_input_byte['Data0']}, {raw_input_byte['Data1']}, {raw_input_byte['Data2']})")

    print(f"InputVoltagesCh1 ({len(voltages_ch1)}):")
    for i, voltage in enumerate(voltages_ch1, start=1):
        print(f"  InputVoltage {i}: {voltage:.3f}")


def get_dynamic_filename(node, format):
    """
    Generate a dynamic filename using the node number and the current timestamp.

    Args:
        node (int): The node number from FlatBuffers.

    Returns:
        str: A dynamically generated filename.
    """
    # Get the current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S:%f")

    # Format the filename
    filename = f"P{node}_{timestamp}.{format}"

    return filename



def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Read and decode SerialMail data from a serial port.")
    parser.add_argument("--port", type=str, required=True, help="Serial port (e.g., /dev/ttyS0 or COM3)")
    parser.add_argument("--baudrate", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("--format", type=str, choices=["csv", "json"], required=True, help="Output format (csv or json)")
    parser.add_argument("--path", type=str, default=".", help="Path to save the output file (default: current directory)")
    args = parser.parse_args()

    # Open the serial connection
    serial_connection = serial.Serial(port=args.port, baudrate=args.baudrate, timeout=1)
    print(f"Listening for data on port {args.port} at {args.baudrate} baud...")

    # Initialize filename as None
    filename = None
    last_timestep = datetime.now() - timedelta(seconds=1)
    file_rotation_time = datetime.now() + timedelta(hours=12)

    try:
        while True:
            # Attempt to read and decode SerialMail data
            serial_mail = read_serial_mail(serial_connection)
            if serial_mail:
                # Extract data
                voltages_ch0, voltages_ch1, raw_input_bytes_ch0, raw_input_bytes_ch1, measurements_ch0, measurements_ch1, node = extract_serial_mail_data(serial_mail)

                if filename is None or datetime.now() >= file_rotation_time:
                    base_filename = get_dynamic_filename(node, args.format)
                    filename = os.path.join(args.path, base_filename)
                    file_rotation_time = datetime.now() + timedelta(hours=12)
                    print(f"Data will be saved to {filename}")
                
                # Print data
                #print_serial_mail_data(voltages_ch0, voltages_ch1, raw_input_bytes_ch0, raw_input_bytes_ch1, node)

                # Write data to the selected file format
                if args.format == "csv":
                    try:
                        last_timestep = write_to_csv(filename, measurements_ch0, measurements_ch1, last_timestep)
                        print(f"Data successfully written to {filename} in CSV format.")
                    except Exception as e:
                        print(f"Failed to write data to {filename} in CSV format: {e}")
                elif args.format == "json":
                    try:
                        write_to_json(filename, voltages_ch0, voltages_ch1, raw_input_bytes_ch0, raw_input_bytes_ch1, measurements_ch0, measurements_ch1, node)
                        print(f"Data successfully written to {filename} in JSON format.")
                    except Exception as e:
                        print(f"Failed to write data to {filename} in JSON format: {e}")
                else:
                    print(f"Unsupported format: {args.format}")

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        serial_connection.close()

if __name__ == "__main__":
    main()