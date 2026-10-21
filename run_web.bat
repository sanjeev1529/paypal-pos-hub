@echo off
title PayPal POS and Fintech Hub (Browser View)
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo Starting PayPal POS & Fintech Hub in Web Browser...
python main.py --web
