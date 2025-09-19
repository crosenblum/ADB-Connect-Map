# ADB Connect Map

**ADB Connect Map** is a tool that scans and maps all devices that can be connected via ADB, whether through USB or Wi-Fi. It generates and maintains a `device_map.json` file with up-to-date device information. This map is then used to create a user-friendly menu, allowing you to easily connect to your devices via `scrcpy` for remote access and control.

## Features
- Automatically scans and updates a `device_map.json` with detailed device information.
- Displays a user-friendly CLI menu for selecting a device to connect to.
- Supports both USB and Wi-Fi connections.
- Uses `scrcpy` to remotely access Android devices.
- Easy device selection and connection, with error handling and device authorization checks.

## Requirements

- Python 3.x
- `adb` (Android Debug Bridge) installed and properly configured
- `scrcpy` installed on your system (for screen mirroring)

## Installation

### 1. Clone the repository:

```bash
git clone https://github.com/yourusername/adb-device-manager.git
cd adb-device-manager
```

### 2. Install the required Python dependencies:

```bash
pip install -r requirements.txt
```

### 3. Install `scrcpy` and `adb` if not already installed:

#### For **Windows**:
- [Install ADB](https://developer.android.com/studio/command-line/adb) and make sure it’s added to your system's PATH.
- Download `scrcpy` from [the official GitHub releases page](https://github.com/Genymobile/scrcpy/releases).

#### For **macOS**:
```bash
brew install scrcpy
brew install android-platform-tools
```

#### For **Linux**:
```bash
sudo apt install scrcpy
sudo apt install android-tools-adb
vbnet
Copy code
```

## Usage

### 1. Update the device map:
Before using the tool, you need to scan your connected devices to populate the `device_map.json` file.

Run the following command to update the device map:

```bash
python update_device_map.py
```

### 2. Start the CLI menu:
After updating the device map, run the following command to start the device selection menu:

```bash
python connect_device.py
```

The CLI will present a list of available devices and ask you to select one to connect to. You can exit at any time by selecting option `0`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)
