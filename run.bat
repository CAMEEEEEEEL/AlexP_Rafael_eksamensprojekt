@echo off
echo Use run.vbs to launch without a console window.
echo Starting with console (debug mode)...
python -m pip install -r requirements.txt --quiet
python main.py
pause
