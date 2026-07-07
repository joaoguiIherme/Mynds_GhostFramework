<h3 align="center">
    <img src="https://user-images.githubusercontent.com/54115104/116760735-6da1e780-aa1e-11eb-8c6f-530386487671.png" alt="logo" height="250px">
</h3>

<p align="center">
    <b>Ghost Framework</b>
    <br>
    Android post-exploitation framework that uses the Android Debug Bridge (ADB) to remotely access an Android device.
</p>

---

## What is it

Ghost Framework is a command-line post-exploitation tool for Android. It connects to a device over **ADB via TCP/IP** (default port `5555`) and gives you an interactive console to control it remotely: run shell commands, transfer files, take screenshots, read device information, and toggle settings.

It is built for **authorized security testing and research only**. Use it only on devices you own or have explicit written permission to test.

## Requirements

- Linux
- Python **3.7+**
- `pip3` and `git`
- Target device with **ADB over TCP/IP enabled** and reachable on the network

## Installation (Linux)

Install directly with `pip3`:

```bash
pip3 install git+https://github.com/EntySec/Ghost
```

Or clone and install from source:

```bash
git clone https://github.com/EntySec/Ghost
cd Ghost
pip3 install .
```

After install, launch the console:

```bash
ghost
```

## Usage

Start Ghost and you get the main console:

```
(ghost)>
```

### Main console commands

| Command | Description |
|---------|-------------|
| `connect <host>:[port]` | Connect to a device over ADB (port defaults to `5555`). |
| `devices` | List all connected devices with their IDs. |
| `interact <id>` | Open the interactive session for a connected device. |
| `disconnect <id>` | Disconnect a device. |
| `exit` | Disconnect all devices and quit. |

Once you `interact` with a device, the prompt changes and the device modules become available.

### Device modules

| Module | Description |
|--------|-------------|
| `shell <command>` | Run a shell command on the device. |
| `list <remote_path>` | List contents of a remote directory. |
| `upload <local_file> <remote_path>` | Upload a file to the device. |
| `download <remote_file> <local_path>` | Download a file from the device. |
| `screenshot <local_path>` | Capture a screenshot and save it locally. |
| `openurl <url>` | Open a URL on the device. |
| `press <keycode>` | Send a key event by keycode. |
| `keyboard` | Type text on the device from your keyboard. |
| `sleep` | Put the device to sleep. |
| `wifi <on\|off>` | Enable or disable Wi-Fi. |
| `battery` | Show battery information. |
| `activity` | Show current activity information. |
| `network <flags>` | Show network info (ARP, IP config, routes, ports, services, and more). |

## Use cases

### 1. Remote shell and file exfiltration

Connect to a device, open a shell, and pull a file off it:

```
(ghost)> connect 192.168.1.42
(ghost)> interact 0

(ghost: 192.168.1.42)> shell id
(ghost: 192.168.1.42)> list /sdcard/Download
(ghost: 192.168.1.42)> download /sdcard/Download/report.pdf ./report.pdf
```

### 2. Live device inspection

Grab a screenshot and read device state during an assessment:

```
(ghost)> connect 10.0.0.15:5555
(ghost)> interact 0

(ghost: 10.0.0.15)> screenshot ./screen.png
(ghost: 10.0.0.15)> battery
(ghost: 10.0.0.15)> network --ports --services
```

## Disclaimer

This tool is intended for **legal, authorized security testing and educational purposes only**. You are responsible for complying with all applicable laws. The authors are not liable for any misuse or damage.

## License

Released under the **MIT License**. Developed by [EntySec](https://entysec.com/).
