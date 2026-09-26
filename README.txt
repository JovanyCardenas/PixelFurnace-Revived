PIXELFURNACE STUDIO 1.3 — BRANDED WINDOWS EDITION
==================================================

This release integrates the supplied Gameband visual resources.

BRANDING
- background.png is used as the actual application wallpaper.
- icon.icns is retained for a future macOS build.
- icon.png is used as the live Tk application/window icon.
- PixelFurnaceStudio.ico is generated from the supplied ICNS and is used for
  the Windows EXE icon.

FEATURES
- Read Gameband over HID
- Sync date/time + timezone/DST
- Built-in Time and Date screens
- Scrolling text generation
- Custom 20x7 pixel-scroll drawing
- Add / delete / reorder text-pixel screens
- Scroll preview
- Save candidate
- Automatic backups
- Restore backup
- Guarded verified hardware writes
- Simple mode by default
- Advanced mode for screen management / recovery
- Animation creation remains intentionally removed

RUN FROM SOURCE
Double-click:
  Launch from Source.bat

BUILD THE WINDOWS EXE
Double-click:
  Build Windows EXE.bat

The finished standalone application will be:
  PixelFurnace Studio Windows\PixelFurnaceStudio.exe

The EXE bundles the Python runtime, HID support, Pillow, background artwork,
and application icon, so the end user does not need Python installed.

MACOS LATER
The included icon.icns is already an Apple icon container. A macOS .app still
needs to be built on macOS and Gameband HID access should be tested there
before calling the Mac build supported.

WINDOWS SECURITY
A locally built unsigned EXE can trigger Windows reputation checks. For public
distribution, code signing is the proper long-term solution; do not globally
disable Windows security.


STUDIO 1.3 FIXES
- Restores the complete Advanced Mode layout and controls.
- Advanced Mode again exposes Open Backup, Save Candidate, Restore Backup,
  Add Text / Pixel Scroll, Delete Screen, Move Up, Move Down, timing controls,
  and the diagnostic log.
- Keeps all Simple Mode behavior and Gameband branding from 1.2.
- Uses the same Gameband icon for the EXE, application window, and Windows
  taskbar by combining the embedded ICO, Tk window icon, and a dedicated
  Windows AppUserModelID.
