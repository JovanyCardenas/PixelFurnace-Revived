# PixelFurnace Studio

A modern, open-source recreation of **PixelFurnace**, the software originally used to customize the LED display on the Gameband Minecraft bracelet.

## Download

### Windows

The easiest way to use PixelFurnace Studio is to download the prebuilt Windows application from the [Releases](../../releases) page.

Download:

**`PixelFurnaceStudio.exe`**

No Python installation is required for the standalone Windows build.

> Windows may display a reputation warning because the application is currently unsigned. PixelFurnace Studio is open source, and the source used to build the executable is available in this repository.

### Run From Source

Developers can also clone the repository and run PixelFurnace Studio directly with Python.

Requirements:

- Python 3
- `hidapi`
- `Pillow`

```bash
pip install -r requirements.txt
python PixelFurnaceStudio.py

## About This Project

The original Gameband software and PixelFurnace editor are no longer reliably available or functional on modern systems. After trying to find a working copy that could still communicate with my Gameband, I decided to recreate the functionality myself.

PixelFurnace Studio was built by reverse engineering the original Gameband software, its USB HID communication protocol, configuration memory format, and the data format used by the bracelet's 20×7 LED display.

The goal isn't to emulate the Gameband or replace its firmware. PixelFurnace Studio communicates directly with the original hardware and recreates the useful local functionality of the old PixelFurnace application on modern computers.

With it, an original Gameband can once again:

- Display custom scrolling text
- Display hand-drawn 20×7 pixel artwork
- Store multiple custom screens
- Reorder and remove screens
- Display its built-in Time and Date screens
- Synchronize its clock and timezone
- Have its configuration backed up and restored

No original Gameband cloud service is required.

> [!NOTE]
> PixelFurnace Studio is a community-made reimplementation/recreation. It is not the original PixelFurnace software and is not affiliated with or endorsed by the original Gameband developers, Mojang, Minecraft, or Microsoft.

## Why I Made This

I still had an original Gameband, but the software ecosystem surrounding it had effectively disappeared.

I could not find a modern, working version of PixelFurnace that would let me customize the bracelet again. The Gameband itself still worked, including its LED display, Time and Date screens, but there was no practical way to change what was stored on it.

Rather than leave the hardware unusable, I began investigating the original software.

By examining the old Gameband application and testing against real Gameband hardware, I was able to recover enough of the protocol to communicate with the bracelet directly.

That included identifying:

- The Gameband USB HID device
- Commands used to read and write its configuration
- The configuration memory layout
- Screen records and screen types
- The 20×7 LED pixel encoding
- Configuration checksums
- Clock synchronization
- Timezone and daylight-saving-time configuration

From that work, I built a new editor from scratch: **PixelFurnace Studio**.

It is intended both as a usable replacement for the old editor and as a preservation project for hardware that would otherwise be increasingly difficult to use.

## Reverse Engineering

PixelFurnace Studio does not require the original PixelFurnace application to run.

The Gameband protocol was independently reconstructed by studying the behavior and code of the legacy Gameband software and validating the results against original hardware.

For example, the primary Gameband HID interface was identified as:

| Property | Value |
|---|---|
| Vendor ID | `0x2A90` |
| Product ID | `0x0021` |
| Configuration base | `0x1800` |
| Configuration size | 4096 bytes |
| Display | 20×7 monochrome pixels |

Several HID commands were also recovered:

| Command | Function |
|---|---|
| `0x02` | Set clock |
| `0x04` | Prepare configuration region |
| `0x06` | Write configuration |
| `0x08` | Read configuration |
| `0x0A` | Commit configuration |

PixelFurnace Studio uses these commands directly rather than depending on the discontinued Gameband cloud infrastructure.

More information is available in [`docs/protocol.md`](docs/protocol.md).
