import socket
import re

# This file decodes a TCP stream that's connected via an RS452 ethernet adapter connected to the RS422 bus on an Advantage Air
# controller.  Not every message is processed, CRCs are ignored, and bus acks/naks etc are essentially ignored also, this
# mostly serves to document the structure of each register, and understand how each component communicates.

# There are probably many errors!
# Usage: Edit the ip in main() to suit your environment
# This code could be trivially changed to support a usb serial adapter

def decode_aircon_error(data: str):
    if len(data) < 14:
        return "Incomplete AirCon Error data"

    # The AirCon error message consists of 5 ASCII characters followed by two reserved bytes (0x00)
    error_code = data[:10]  # First 5 characters (each 2 hex digits)
    reserved = data[10:14]  # Last 2 reserved bytes (should be '0000')

    # Convert hex-encoded error code to ASCII string
    error_code_str = bytes.fromhex(error_code).decode('ascii')

    # Lookup table for known error codes
    error_descriptions = {
        "AA1": "Communication error between Advantage Air componentry and A/C unit",
        "AA2": "Multiple unit controllers detected",
        "AA3": "Communication error",
        "AA4": "System is not detecting any temperature sensors",
        "AA81": "Wall sensor detected but no zone allocated or multiple zones allocated",
        "AA82": "Wall sensor detected but no zone allocated or multiple zones allocated",
        "AA83": "Wall sensor detected but no zone allocated or multiple zones allocated",
        "AA86": "Wireless wall sensor detected with low battery reading",
        "AA89": "Multiple sensors detected on the same zone"
    }

    # Get description for the error code or use a default message
    description = error_descriptions.get(error_code_str, f"Unknown Error Code: {error_code_str}")

    return {
        "Error Code": error_code_str,
        "Description": description,
        "Reserved": reserved
    }

def decode_set_uid(data: str):
    if len(data) < 12:  # Ensure there is enough data to process
        return "Incomplete Set UID data"

    # Extract the UID, which is the first 3 bytes (6 hex digits)
    unit_uid = data[0:6]

    # The remaining bytes (if any) are typically zeros, so we will capture them for completeness
    additional_data = data[6:]

    return {
        "orig": data,
        "Unit UID": unit_uid,
        "Additional Data": additional_data  # This is typically zeros but included for completeness
    }


def decode_zone_config(data):
    if len(data) >= 14:
        bytes_data = bytes.fromhex(data[:14])
        zones = bytes_data[1]
        constant_zones = bytes_data[2]
        zone_1 = bytes_data[3]
        zone_2 = bytes_data[4]
        zone_3 = bytes_data[5]
        filter_status = bytes_data[6]
        return f"Zones: {zones}, Constant Zones: {constant_zones}, Zone 1: {zone_1}, Zone 2: {zone_2}, Zone 3: {zone_3}, Filter Status: {filter_status}"
    else:
        return "Incomplete Zone Config data"
    

def decode_zone_config_cb(data: str):
    if len(data) < 14:
        return "Incomplete Zone Config CB data"

    bytes_data = bytes.fromhex(data[:14])

    _, num_zones, num_const_zones, const_zone1, const_zone2, const_zone3, filter_status = bytes_data

    return {
        "Header": bytes_data[0],
        "Number of Zones": num_zones,
        "Number of Constant Zones": num_const_zones,
        "Constant Zone 1": const_zone1,
        "Constant Zone 2": const_zone2,
        "Constant Zone 3": const_zone3,
        "Filter Clean Status": filter_status
    }

def decode_unit_type(data: str):
    if len(data) < 6:
        return "Incomplete Unit Type / Activation Status data"

    unit_type = int(data[0:2], 16)
    activation_status = int(data[2:4], 16)

    unit_type_map = {
        0x11: "Daikin",
        0x12: "Panasonic",
        0x13: "Fujitsu",
        0x19: "Samsung DVM"
    }

    activation_status_map = {
        0: "No Code",
        1: "Expired",
        2: "Code Enabled"
    }

    return {
        "Unit Type": unit_type_map.get(unit_type, f"Unknown (0x{unit_type:02X})"),
        "Activation Status": activation_status_map.get(activation_status, f"Unknown ({activation_status})")
    }

def decode_zone_state(data: str):
    if len(data) < 14:
        return "Incomplete Zone State data"

    bytes_data = bytes.fromhex(data[:14])

    zone_number = bytes_data[0]
    zone_open = bool(bytes_data[1] & 0x80)
    zone_percent = bytes_data[1] & 0x7F
    sensor_type = bytes_data[2]
    set_temp = bytes_data[3] / 2.0
    measured_temp_int = bytes_data[4]
    measured_temp_decimal = bytes_data[5]
    # Byte 6 is ignored

    sensor_type_map = {
        0: "No Sensor",
        1: "RF",
        2: "Wired",
        3: "RF2CAN Booster",
        4: "RF_X"
    }

    return {
        "Zone Number": zone_number,
        "Zone Open": zone_open,
        "Zone Percent": zone_percent,
        "Sensor Type": sensor_type_map.get(sensor_type, f"Unknown ({sensor_type})"),
        "Set Temperature (°C)": set_temp,
        "Measured Temperature": f"{measured_temp_int}.{measured_temp_decimal}°C"
    }

# def decode_unit_type(data):
#     # Implement decoding logic for Unit Type / Activation Status messages
#     if len(data) >= 4:
#         unit_type = data[0:2]
#         activation_status = data[2:4]
#         return f"Unit Type: {unit_type}, Activation Status: {activation_status}"
#     else:
#         return "Incomplete Unit Type / Activation Status data"


def decode_zone_config_jz13(data: str):
    if len(data) < 14:
        return "Incomplete Zone Config JZ13 data"

    bytes_data = bytes.fromhex(data[:14])

    zone_number = bytes_data[0]
    min_damper = bytes_data[1]
    max_damper = bytes_data[2]
    motion_status = bytes_data[3]
    motion_config = bytes_data[4]
    motion_zone_error = bytes_data[5]
    cb_rssi = bytes_data[6]

    return {
        "Zone Number": zone_number,
        "Min Damper": min_damper,
        "Max Damper": max_damper,
        "Motion Status": motion_status,
        "Motion Config": motion_config,
        "Motion Zone Error": motion_zone_error,
        "CB RSSI": cb_rssi
    }


def decode_system_status(data):
    if len(data) >= 14:
        system_state = 'On' if data[0:2] == '01' else 'Off'
        mode_map = { '01': 'Cool', '02': 'Heat', '03': 'Vent', '04': 'Auto', '05': 'Dry', '06': 'MyAuto' }
        fan_map = {'00': 'Off', '01': 'Low', '02': 'Medium', '03': 'High', '04': 'Auto', '05': 'AutoAA' }

        mode = mode_map.get(data[2:4], 'Unknown')
        fan = fan_map.get(data[4:6], 'Unknown')
        set_temp = int(data[6:8], 16) / 2.0
        myzone_id = data[8:10]
        fresh_air_status = 'On' if data[10:12] == '01' else 'Off'
        return {
            "System State": system_state,
            "Mode": mode,
            "Fan": fan,
            "Set Temp (°C)": set_temp,
            "MyZone ID": myzone_id,
            "Fresh Air Status": fresh_air_status
        }
    else:
        return "Incomplete System Status data"

def decode_firmware_status(data: str):
    if len(data) < 14:
        return "Incomplete Firmware Status data"

    fw_major = int(data[0:2], 16)
    fw_minor = int(data[2:4], 16)
    cb_type = int(data[4:6], 16)
    rf_fw_major = int(data[6:8], 16)
    # Assuming bytes 8-14 are reserved/ignored
    return {
        "Firmware Major": fw_major,
        "Firmware Minor": fw_minor,
        "Control Box Type": cb_type,
        "RF Firmware Major": rf_fw_major
    }

def decode_register(register_id, data):
    descriptions = {
        '01': 'Zone CFG    ',
        '02': 'Unit Type   ',
        '03': 'Zone State  ',
        '04': 'Zone Cfg    ',
        '05': 'Sys Status  ',
        '06': 'FW Vers     ',
        '07': 'Tablet?     ',
        '08': 'AC Error    ',
        '09': 'Activation  ',
        '12': 'Sensor Pair ',
        '13': 'Info Byte   ',
        '0a': 'UID         '
    }

    description = descriptions.get(register_id, 'Unknown     ')

    if register_id == '01':
        return description, decode_zone_config(data)
    elif register_id == '02':
        return description, decode_unit_type(data)
    elif register_id == '03':
        return description, decode_zone_state(data)
    elif register_id == '04':
        return description, decode_zone_config_jz13(data)
    elif register_id == '05':
        return description, decode_system_status(data)
    elif register_id == '06':
    # Skipping the locking stuff because don't want to play there
        return description, decode_firmware_status(data)
    elif register_id == '08':
        return description, decode_aircon_error(data)
    elif register_id == '0a':
        return description, decode_set_uid(data)
    # Add more decoding based on register_id

    return description, data  # Default return if not specifically handled


def parse_u_message(message):
    message = message.decode('utf-8', errors='ignore').strip()

    if len(message) == 0: # ignore blank messages
        return

    if message.startswith("Ping"): # ignore pings
        return

    components = message.split()

    if len(components) < 2: # ignore anything with no content
        return

    # Extract the type of message (setCAN or getCAN)
    message_type = components[0]
    if message_type not in ["setCAN", "getCAN", "ackCAN"]:
        print(f"Unrecognized CAN message type: '{message}'")
        return

    origin_map = {
        "01": "Tablet",
        "03": "CB    "
    }

    # Extract the CAN frames

    for can_data in components[1:]:
        # Ensure CAN message has the minimum required length
        if can_data == "1":
            continue

        if len(can_data) < 14:
            print(f"Incomplete CAN message: '{can_data}', '{message}'")
            continue

        # Split CAN message components based on the protocol description
        unit_type = can_data[0:2]  # First two characters: unit type
        origin_dest = can_data[2:4]  # Next two characters: origin/destination
        origin_name = origin_map.get(origin_dest,origin_dest)
        unit_id = can_data[4:9]  # Next five characters: unit ID
        register_id = can_data[9:11]  # Next two characters: register ID
        data = can_data[11:]  # The remaining characters: data

        # Decode the register data based on the register ID
        description, decoded_data = decode_register(register_id, data)

        parsed_message = {
            'type': message_type,
            'unit_type': unit_type,
            'origin_dest': origin_dest,
            'unit_id': unit_id,
            'register_id': register_id,
            'data': decoded_data,
            'description': description
        }
        print(f"{message_type} unit:{unit_id} from:{origin_name} register:{register_id}:{description} {decoded_data}  ")
        #print(f"Parsed CAN Message: {parsed_message}")


def main():
    ip = "192.168.1.2"
    port = 10002
    buffer = b""  # Use bytes instead of string

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))

    try:
        while True:
            data = sock.recv(1024)  # Read raw bytes from the socket
            if data:
                buffer += data
                # Find and parse all <U>...</U=...> messages
                u_messages = re.findall(rb'<U>(.*?)</U=[0-9a-fA-F]{2}>', buffer)
                for message in u_messages:
                    parse_u_message(message)
                # Clean up the buffer by removing parsed messages
                buffer = re.sub(rb'<U>(.*?)</U=[0-9a-fA-F]{2}>', b'', buffer)
            else:
                break
    except KeyboardInterrupt:
        print("User interrupted the connection.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
