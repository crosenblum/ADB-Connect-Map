import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional


def adb_command(command: str) -> Optional[str]:
    """
    Executes an ADB command and returns the output as a string.
    
    Args:
        command (str): The ADB command to execute.
    
    Returns:
        Optional[str]: The output of the command as a string, or None if the command fails.
    """
    if not isinstance(command, str):
        raise ValueError(f"Expected a string for command, got {type(command)}")
    
    try:
        result = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        return result.decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        return None

def get_device_connection_type(serial: str) -> str:
    """
    Returns whether a device is connected via USB or Wi-Fi based on the adb devices -l output.
    
    Args:
        serial (str): The serial number of the device.
    
    Returns:
        str: "usb" if the device is connected via USB, "wifi" if connected via Wi-Fi.
    """
    devices_list = adb_command("adb devices -l")
    
    if devices_list:
        for line in devices_list.splitlines():
            if serial in line:
                if ":5555" in line:
                    return "wifi"
                else:
                    return "usb"
    return "offline"

def get_device_ip(serial: str) -> Optional[str]:
    """
    Retrieves the IP address of the device.
    
    Args:
        serial (str): The serial number of the device.
    
    Returns:
        Optional[str]: The IP address of the device, or None if it cannot be determined.
    """
    ip_address = adb_command(f"adb -s {serial} shell ip addr show wlan0 | grep inet")
    if ip_address:
        return ip_address.split()[1].split('/')[0]
    return None

def get_device_info(serial: str) -> Optional[Dict[str, str]]:
    """
    Retrieves information for a given device using its serial number.
    
    Args:
        serial (str): The serial number of the device.
    
    Returns:
        Optional[Dict[str, str]]: A dictionary containing 'model', 'device_type', 
                                  'serial_number', and 'ip_address', or None if any 
                                  information is unavailable.
    """
    model = adb_command(f"adb -s {serial} shell getprop ro.product.model")
    device_type = adb_command(f"adb -s {serial} shell getprop ro.product.device")
    serial_number = adb_command(f"adb -s {serial} shell getprop ro.serialno")
    
    connection_type = get_device_connection_type(serial)
    
    ip_address = None
    if connection_type == "wifi":
        ip_address = get_device_ip(serial)
    
    if connection_type == "usb":
        ip_address = None
    
    if model and device_type and serial_number:
        return {
            "model": model,
            "device_type": device_type,
            "serial_number": serial_number,
            "ip_address": ip_address
        }
    return None
    
def get_device_status(serial: str) -> str:
    """
    Retrieves the connection status of a device.
    
    Args:
        serial (str): The serial number of the device.
    
    Returns:
        str: The status of the device ('device', 'offline', etc.).
    """
    devices_list = adb_command("adb devices")
    if devices_list:
        for line in devices_list.splitlines():
            if serial in line:
                status = line.split('\t')[1]
                return status
    return "offline"

def update_device_map() -> None:
    """
    Updates the device_map.json file by extracting data from all connected devices.
    Skips devices that are offline and updates data for those that are connected.
    The information is added or updated for existing devices.
    """
    devices_list = adb_command("adb devices")
    try:
        with open("device_map.json", "r") as json_file:
            device_map = json.load(json_file)
    except FileNotFoundError:
        device_map = {"devices": []}

    device_index = {device["serial"]: idx for idx, device in enumerate(device_map["devices"])}

    if devices_list:
        for line in devices_list.splitlines():
            if line.strip() and line.strip() != "List of devices attached":
                serial = line.split('\t')[0]
                if re.match(r'^\d{1,3}(\.\d{1,3}){3}:\d+$', serial):
                    serial = ""
                if not serial:
                    continue
                
                status = get_device_status(serial)

                if status == "device":
                    if serial in device_index:
                        device = device_map["devices"][device_index[serial]]
                        updated = False

                        if not device.get("model"):
                            device["model"] = adb_command(f"adb -s {serial} shell getprop ro.product.model") or ""
                            updated = True
                        
                        if not device.get("device_type"):
                            device["device_type"] = adb_command(f"adb -s {serial} shell getprop ro.product.device") or ""
                            updated = True

                        connection_type = get_device_connection_type(serial)
                        
                        if connection_type == "wifi" and not device.get("ip_address"):
                            ip_address = adb_command(f"adb -s {serial} shell ip addr show wlan0 | grep inet") or ""
                            if ip_address:
                                device["ip_address"] = ip_address.split()[1].split('/')[0]
                            updated = True
                        
                        if connection_type == "usb" and not device.get("ip_address"):
                            device["ip_address"] = ""
                            updated = True

                        if device.get("status") != status:
                            device["status"] = status
                            updated = True

                        if updated:
                            device_map["devices"][device_index[serial]] = device
                    else:
                        device_info = get_device_info(serial)
                        if device_info:
                            new_device = {
                                "name": "",
                                "serial": serial,
                                "model": device_info.get("model", ""),
                                "device_type": device_info.get("device_type", ""),
                                "ip_address": device_info.get("ip_address", ""),
                                "status": status
                            }
                            device_map["devices"].append(new_device)
                            device_index[serial] = len(device_map["devices"]) - 1

                else:
                    existing_device = next((device for device in device_map['devices'] if device['serial'] == serial), None)
                    display_name = existing_device.get("name") or existing_device.get("model") or serial if existing_device else serial
                    print(f"Device '{display_name}' is offline. Skipping...")

    with open("device_map.json", "w") as json_file:
        json.dump(device_map, json_file, indent=4)

    # print("device_map.json has been updated.")

def is_device_authorized(serial: str) -> bool:
    """
    Checks if the device is authorized for ADB connections.
    
    Args:
        serial (str): The serial number of the device.
    
    Returns:
        bool: True if the device is authorized, False if unauthorized.
    """
    # Check the device status using `adb devices`
    devices_list = adb_command("adb devices")
    
    # Check if the command returned any data
    if devices_list:
        for line in devices_list.splitlines():
            if serial in line:
                status = line.split('\t')[1]
                if status == "device":
                    return True  # Authorized device
                elif status == "unauthorized":
                    return False  # Unauthorized device
    return False  # Device not found or any other status

def display_device_menu(devices: List[Dict[str, str]]) -> int:
    """
    Displays a CLI menu with all connected devices and returns the selected device index.
    
    Args:
        devices (List[Dict[str, str]]): A list of devices to display in the menu.
    
    Returns:
        int: The selected device index, or 0 if the user wants to exit.
    """
    # Software name and tagline (you can customize this)
    software_name = "ADB Device Manager"
    software_tagline = "Easily manage and connect your Android devices via ADB"

    # Print a decorative header
    print("=" * 55)
    print(f"{software_name}".center(50))
    print(f"{software_tagline}".center(50))
    print("=" * 55)
    
    print("\nSelect a device to connect to (or 0 to exit):\n")
    # Print the device options
    for index, device in enumerate(devices, start=1):
        device_name = device.get("name") or device.get("model") or device["serial"]
        print(f"{index}. {device_name} ({device['serial']})")
    
    # Get user input
    try:
        choice = int(input("\nSelect a number: "))
        if 0 <= choice <= len(devices):
            # Get the selected device's serial
            selected_device = devices[choice - 1]
            serial = selected_device['serial']
            
            # Check if the device is authorized
            if not is_device_authorized(serial):
                print(f"\nDevice {device_name} is unauthorized for ADB connection.")
                print("Please authorize the device via USB first and try again.")
                # Exit or ask the user to reconnect via USB
                return 0
            
            # Proceed with the selection
            return choice
            
        else:
            print("Invalid choice. Please enter a valid number.")
            # Recurse until valid input
            return display_device_menu(devices)
    except ValueError:
        print("Invalid input. Please enter a number.")
        # Recurse until valid input
        return display_device_menu(devices)
def main() -> None:
    """
    Main function to update the device map, display the menu, and connect to the selected device.
    """
    update_device_map()

    try:
        with open("device_map.json", "r") as json_file:
            device_map = json.load(json_file)
    except FileNotFoundError:
        print("No devices found.")
        return

    devices = [device for device in device_map["devices"] if device["status"] == "device"]

    if not devices:
        print("No devices are currently connected. Exiting.")
        return

    while True:
        choice = display_device_menu(devices)

        if choice == 0:
            print("Exiting...")
            break

        # Get the selected device from the list (adjust index as Python is 0-based)
        selected_device = devices[choice - 1]

        # Disconnect all devices except the selected one
        for device in devices:
            if device != selected_device:
                serial = device["serial"]
                print(f"Disconnecting {device['name']} ({serial})...")
                adb_command(f"adb -s {serial} disconnect")

        # Connect to the selected device
        serial = selected_device["serial"]
        connection_type = get_device_connection_type(serial)

        if connection_type == "wifi":
            # print(f"Connecting to {selected_device['name']} over Wi-Fi...")
            adb_command(f"adb connect {selected_device['ip_address']}:5555")
        elif connection_type == "usb":
            # print(f"Connecting to {selected_device['name']} via USB...")
            adb_command(f"adb -s {serial} usb")

        # Launch scrcpy to allow remote access to the device
        # print(f"Launching scrcpy for {selected_device['name']}...")

        # Suppress output by redirecting both stdout and stderr to os.devnull
        subprocess.run(["scrcpy", "-s", serial], stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))

        # Wait for user to manually stop scrcpy
        # print(f"Press Ctrl+C to exit scrcpy for {selected_device['name']}...")

        # After scrcpy is closed, exit the program instead of going back to the menu
        print("\nDisconnected.")

        # Exit the script immediately
        sys.exit()

if __name__ == "__main__":
    main()