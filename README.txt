PIXELFURNACE STUDIO v1.1 — CLOCK & DST BUG FIXES
================================================

PixelFurnace Studio is an independent, community-made recreation of the
original PixelFurnace editor for the Gameband Minecraft bracelet. It connects
to original Gameband hardware to customize its 20x7 LED display without
requiring the discontinued Gameband cloud service.

WHAT'S NEW IN v1.1
------------------
- Improved detection of upcoming daylight-saving-time (DST) changes using
  local timezone offsets evaluated at future timestamps.
- Fixed the display of negative fractional-hour UTC offsets (for example,
  UTC-3:30).
- Fixed clock synchronization dialogs that displayed literal \n characters
  instead of line breaks.
- Clock synchronization now preserves configuration header word 6 rather
  than overwriting it. Other Gameband implementations identify this field
  as display orientation; its exact behavior still needs hardware testing.
- Clears stored transition timestamp fields when no upcoming timezone
  transition is found.

These fixes are implemented in the v1.1 source branch but have not yet been
fully validated on physical Gameband hardware. Test clock and display
behavior carefully before relying on them.

FEATURES
--------
- Read Gameband configuration over USB HID
- Synchronize date, time, timezone, and DST information
- Support built-in Time and Date screens
- Generate scrolling text
- Draw custom 20x7 pixel-scroll artwork
- Add, delete, and reorder text/pixel screens
- Preview scrolling messages
- Save configuration candidates to a .bin file
- Create automatic configuration backups
- Restore valid backups
- Apply configuration changes with readback and verification safeguards
- Use Simple Mode by default
- Use Advanced Mode for screen management, timing controls, and diagnostics
- Animation creation remains intentionally unsupported

BRANDING AND INCLUDED RESOURCES
-------------------------------
- background.png provides the application's wallpaper.
- icon.png provides the Tk application/window icon.
- PixelFurnaceStudio.ico provides the Windows executable icon.
- icon.icns is retained for a possible future macOS build.

RUN FROM SOURCE
---------------
Double-click:
  Launch from Source.bat

Alternatively, install the Python dependencies listed in requirements.txt
and run:
  python PixelFurnaceStudio.py

BUILD THE WINDOWS EXE
---------------------
Double-click:
  Build Windows EXE.bat

The build script is intended to produce:
  PixelFurnace Studio Windows\PixelFurnaceStudio.exe

The standalone Windows executable bundles the Python runtime and required
application resources, so end users do not need Python installed.

If downloading a prebuilt executable from GitHub Releases, use the file
provided with the release instead of building from source.

BACKUPS AND HARDWARE SAFETY
---------------------------
The application creates backups when reading the Gameband and before
configuration writes. Keep copies of your original backups somewhere safe.

Hardware configuration changes should be tested cautiously. Do not unplug
the Gameband while a write is in progress. Readback verification reduces
risk but cannot guarantee compatibility with every device or firmware.

MACOS STATUS
------------
The included icon.icns is an Apple icon resource, but a macOS .app still
needs to be built on macOS and Gameband HID access tested before macOS can
be considered supported.

WINDOWS SECURITY
----------------
An unsigned Windows executable may trigger a Microsoft Defender SmartScreen
reputation warning. For public distribution, code signing is the proper
long-term solution. Do not globally disable Windows security.

PROJECT AND SUPPORT
-------------------
Source code and issue reports:
  https://github.com/JovanyCardenas/PixelFurnace-Revived

PixelFurnace Studio is not the original PixelFurnace application and is not
affiliated with or endorsed by the original Gameband developers, Mojang,
Minecraft, or Microsoft. Third-party Gameband branding and artwork are not
claimed as original PixelFurnace Studio assets.
