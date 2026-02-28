@echo off
title AURA - Full Stack Launcher
echo ============================================
echo   AURA v2 - Starting Frontend + Backend
echo ============================================
echo.

:: Start Backend (FastAPI on port 8001)
echo [1/2] Starting Backend (python main.py)...
start "AURA Backend" cmd /k "cd /d %~dp0 && python main.py"

:: Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

:: Start Frontend (Vite on port 5173)
echo [2/2] Starting Frontend (npm run dev)...
start "AURA Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ============================================
echo   Both servers are starting!
echo   Backend:  http://localhost:8001
echo   Frontend: http://localhost:5173
echo ============================================
echo.
echo You can close this window. The servers run in separate terminals.
pause
