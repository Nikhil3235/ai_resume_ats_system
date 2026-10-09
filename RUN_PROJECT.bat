@echo off
title AI Resume ATS Runner
echo ====================================================
echo           AI RESUME ATS SYSTEM - LAUNCHER
echo ====================================================
echo.
echo 1. Starting FastAPI Backend on http://localhost:8000 ...
start "ATS Backend" cmd /k "cd /d C:\Users\Gayatri Mali\OneDrive\Desktop\AI_RESUME_ATS_SYSYTEM && python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

timeout /t 5 >nul

echo 2. Starting Streamlit Frontend on http://localhost:8501 ...
start "ATS Frontend" cmd /k "cd /d C:\Users\Gayatri Mali\OneDrive\Desktop\AI_RESUME_ATS_SYSYTEM && python -m streamlit run frontend/streamlit_app.py --server.port 8501"

echo.
echo Application started successfully!
echo Opening browser...
start http://localhost:8501
exit
