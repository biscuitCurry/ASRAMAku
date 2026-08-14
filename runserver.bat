@echo off
cd /d "%~dp0"
call .venv\Scripts\activate

:: Opens the browser to your dashboard automatically
start http://127.0.0.1:8000/

:: Starts the Django development server
python manage.py runserver
pause