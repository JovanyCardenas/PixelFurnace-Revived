@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   PixelFurnace Studio 1.3 - Windows Builder
echo ============================================
echo.

where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python 3 was not found.
  echo Install Python 3 for Windows first.
  pause
  exit /b 1
)

echo [1/3] Installing build dependencies...
py -m pip install --upgrade pyinstaller hidapi pillow
if errorlevel 1 goto :fail

echo.
echo [2/3] Building branded standalone EXE...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

py -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name PixelFurnaceStudio ^
  --icon "PixelFurnaceStudio.ico" ^
  --add-data "background.png;." ^
  --add-data "icon.png;." ^
  --add-data "PixelFurnaceStudio.ico;." ^
  --collect-binaries hid ^
  PixelFurnaceStudio.py

if errorlevel 1 goto :fail

echo.
echo [3/3] Creating release folder...
if exist "PixelFurnace Studio Windows" rmdir /s /q "PixelFurnace Studio Windows"
mkdir "PixelFurnace Studio Windows"
mkdir "PixelFurnace Studio Windows\gameband_backup"
copy /y "dist\PixelFurnaceStudio.exe" "PixelFurnace Studio Windows\PixelFurnaceStudio.exe" >nul
copy /y "README.txt" "PixelFurnace Studio Windows\README.txt" >nul
echo Automatic Gameband backups are stored here.>"PixelFurnace Studio Windows\gameband_backup\KEEP_BACKUPS_HERE.txt"

echo.
echo ============================================
echo BUILD COMPLETE
echo ============================================
echo.
echo EXE:
echo   %CD%\PixelFurnace Studio Windows\PixelFurnaceStudio.exe
echo.
pause
exit /b 0

:fail
echo.
echo BUILD FAILED. Review the error above.
pause
exit /b 1
