@echo off
cd /d "%~dp0"
py -m pip install hidapi pillow
py PixelFurnaceStudio.py
if errorlevel 1 pause
