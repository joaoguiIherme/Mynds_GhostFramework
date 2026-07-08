<h3 align="center">
    <img src="https://user-images.githubusercontent.com/54115104/116760735-6da1e780-aa1e-11eb-8c6f-530386487671.png" alt="logo" height="250px">
</h3>

<p align="center">
    <b>GHOST FRAMEWORK</b>
    <br>
    <code>// Android post-exploitation over the Android Debug Bridge (ADB)</code>
</p>

<p align="center">
    <a href="https://github.com/joaoguiIherme/Mynds_GhostFramework/releases/tag/v8.1.0"><img src="https://img.shields.io/badge/version-8.1.0-00ffee?style=flat-square"></a>
    <img src="https://img.shields.io/badge/python-3.7+-ff2e97?style=flat-square">
    <img src="https://img.shields.io/badge/platform-linux-9d4edd?style=flat-square">
    <img src="https://img.shields.io/badge/license-MIT-00ffee?style=flat-square">
</p>

```
    ┌─[ ghost ]─────────────────────────────────────────────┐
    │  connect · shell · pull · push · screenshot · recon    │
    └────────────────────────────────────────────────────────┘
```

---

## `//` What is it

**Ghost Framework** is a command-line post-exploitation tool for Android. It speaks
**ADB over TCP/IP** (default port `5555`) and hands you an interactive console to drive
a target device remotely — run shell commands, move files, capture screenshots, read
device state, and flip settings.

> **Authorized use only.** Operate exclusively on devices you own or have explicit
> written permission to test. See [Disclaimer](#-disclaimer).

---

## `//` Requirements

| Component | Requirement |
|-----------|-------------|
| OS (operator) | Linux |
| Python | **3.7+** |
| Tooling | `pip3`, `git`, `adb` (`android-tools-adb` / `platform-tools`) |
| Network | Operator + target on the **same reachable network** |
| Target | Android device with **ADB over TCP/IP** exposed on a fixed port (`5555`) |

Install `adb` on Debian/Kali:

```bash
sudo apt update && sudo apt install -y android-tools-adb
```

---

## `//` Installation

Install straight from this repository:

```bash
pip3 install git+https://github.com/joaoguiIherme/Mynds_GhostFramework
```

Or clone and install from source:

```bash
git clone https://github.com/joaoguiIherme/Mynds_GhostFramework
cd Mynds_GhostFramework
pip3 install .
```

Launch the console:

```bash
ghost
```

---

## `//` Connecting a device

> **Read this first.** Ghost's `connect` talks the **classic ADB daemon protocol on a
> fixed port** (`5555`) using an RSA key. It **cannot** perform the Android 11+ *Wireless
> Debugging* TLS pairing handshake (the screen with a random port like `38803` and a
> 6-digit code). The workflow is always: get a working `adb` device → open port `5555`
> with `adb tcpip 5555` → then `connect` from Ghost.

### On the phone (once)

1. **Settings → About phone** → tap **Build number** 7× to unlock **Developer options**.
2. **Developer options** → enable **USB debugging**.

---

### Path A — USB (most reliable)

Use this to bootstrap the connection. A USB cable is needed **only once** to open the
TCP port; you can unplug afterwards.

**1. Verify the kernel sees the phone.** Plug in with a **data-capable cable** (many
cables are charge-only), then pull down the notification and set USB mode to
**File Transfer (MTP)**.

```bash
lsusb
```

The phone should appear (e.g. `Samsung`, `Xiaomi`, `Google`...). If it does **not**,
the problem is the cable or port — swap and retry before doing anything else.

**2. Reset the ADB server and authorize.**

```bash
adb kill-server
adb start-server
adb devices
```

- `unauthorized` → the phone shows an **RSA prompt** → tap **Allow (always)** → rerun `adb devices` until it reads `device`.
- empty list → back to step 1 (cable / USB mode).

**3. (If it stays `unauthorized` / `offline` on Linux) fix udev permissions:**

```bash
sudo usermod -aG plugdev "$USER"
sudo apt install -y android-sdk-platform-tools-common
```

Log out and back in, then repeat step 2.

**4. Open the TCP port** (now that a device is present):

```bash
adb tcpip 5555
```

**5. Connect from Ghost** (unplug USB if you want — the TCP port stays open):

```bash
ghost
(ghost)> connect 192.168.1.42
```

Port defaults to `5555` — do **not** append the Wireless Debugging port.

---

### Path B — Wireless (Android 11+, no USB)

The *Wireless Debugging* screen shows an `IP:port` (e.g. `192.168.18.31:38803`) **plus a
separate "Pair device with pairing code" entry** with a **different port**. Ghost cannot
pair, so pair and connect with `adb` first, then downgrade to the classic fixed port.

**1. Phone:** Developer options → **Wireless debugging** → **ON** → tap
**Pair device with pairing code**. Note the **6-digit code** and the **pairing IP:port**
(e.g. `192.168.18.31:41234` — this is *not* the `38803` shown on the main screen).

**2. Pair** using the **pairing port**:

```bash
adb pair 192.168.18.31:41234
# enter the 6-digit code when prompted
```

**3. Connect** using the **main Wireless Debugging port** (`38803`):

```bash
adb connect 192.168.18.31:38803
adb devices          # should read: device
```

**4. Downgrade to the classic fixed port** so Ghost can talk to it:

```bash
adb tcpip 5555
adb connect 192.168.18.31:5555
```

**5. Connect from Ghost:**

```bash
ghost
(ghost)> connect 192.168.18.31
```

---

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `error: no devices/emulators found` on `adb tcpip` | No ADB device present yet | Complete **Path A** steps 1–3 (or Path B pair/connect) first |
| Phone missing from `lsusb` | Charge-only cable / bad port / MTP not set | Swap cable, change port, set USB mode to File Transfer |
| `adb devices` shows `unauthorized` | RSA prompt not accepted | Tap **Allow (always)** on the phone; on Linux fix udev (Path A step 3) |
| Ghost: `Failed to connect to <ip>` on port `38803` | Feeding Ghost the Wireless Debugging port | Use `adb tcpip 5555`, then `connect <ip>` (port `5555`) |
| Connection drops after reboot | `tcpip` mode is not persistent | Re-run Path A / Path B after each phone reboot |

---

## `//` Usage

Start Ghost to reach the main console:

```
(ghost)>
```

### Core commands

| Command | Description |
|---------|-------------|
| `connect <host>:[port]` | Connect to a device over ADB (port defaults to `5555`). |
| `devices` | List all connected devices with their IDs. |
| `interact <id>` | Open the interactive session for a connected device. |
| `disconnect <id>` | Disconnect a device. |
| `clear` | Clear the terminal window. |
| `help` | Show all available commands. |
| `exit` / `quit` | Disconnect all devices and quit. |

After `interact <id>`, the prompt changes and the **device modules** become available.

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

---

## `//` Use cases

### 1 · Remote shell and file exfiltration

```
(ghost)> connect 192.168.1.42
(ghost)> interact 0

(ghost: 192.168.1.42)> shell id
(ghost: 192.168.1.42)> list /sdcard/Download
(ghost: 192.168.1.42)> download /sdcard/Download/report.pdf ./report.pdf
```

### 2 · Live device inspection

```
(ghost)> connect 10.0.0.15:5555
(ghost)> interact 0

(ghost: 10.0.0.15)> screenshot ./screen.png
(ghost: 10.0.0.15)> battery
(ghost: 10.0.0.15)> network --ports --services
```

---

## `//` Disclaimer

This tool is intended for **legal, authorized security testing and educational purposes
only**. You are solely responsible for complying with all applicable laws and for
obtaining permission before testing any device. The authors and contributors accept **no
liability** for misuse or damage.

---

## `//` License

Released under the **MIT License**. Original framework developed by
[EntySec](https://entysec.com/).
