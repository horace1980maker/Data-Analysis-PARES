@echo off
echo Starting PARES App...
echo Activating virtual environment...
if exist .venv\Scripts\activate (
    call .venv\Scripts\activate
) else (
    echo .venv not found. Please run "python -m venv .venv" and "pip install -r requirements.txt" first.
    pause
    exit /b
)

echo Opening browser...
start http://localhost:8000

echo Starting Server...
python -m uvicorn pares_converter.app.main:app --reload --port 8000
pause
