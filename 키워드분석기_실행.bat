@echo off
chcp 65001
cd /d "c:\Users\user\keword"
echo Starting Modern Keyword Analysis Backend...
start "" "http://localhost:5000"
python api.py
pause
