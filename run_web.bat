@echo off
title Haven and Home Decor Studio (Browser View)
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo Starting Haven and Home Decor Studio in Web Browser...
python main.py --web
