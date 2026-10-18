@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3 ukrainizer.py --restore
if errorlevel 9009 python ukrainizer.py --restore
pause
