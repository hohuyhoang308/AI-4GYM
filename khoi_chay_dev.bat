@echo off
chcp 65001 >nul
echo ========================================================
echo        KHỞI CHẠY CHATBOT AI-4GYM (CHẾ ĐỘ DEV)
echo ========================================================
echo.

set "PATH=%LOCALAPPDATA%\Programs\NodeJS\node-v22.14.0-win-x64;%PATH%"

:: 1. Kiểm tra / Khởi động Ollama
echo [1/3] Đang kiểm tra Ollama...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="1" (
    echo Khởi động Ollama server ngầm...
    start "" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
    timeout /t 3 /nobreak >nul
) else (
    echo Ollama đã đang chạy.
)

:: 2. Khởi chạy Backend FastAPI (cổng 8000)
echo.
echo [2/3] Đang khởi chạy Backend (port 8000)...
cd /d "%~dp0BE"
start "AI-4GYM Backend" .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

:: 3. Khởi chạy Frontend Vite (cổng 5173)
echo.
echo [3/3] Đang khởi chạy Frontend Vite (port 5173)...
cd /d "%~dp0FE"
start "AI-4GYM Frontend" cmd /k "npm run dev"

timeout /t 3 /nobreak >nul
start http://127.0.0.1:5173

echo.
echo ========================================================
echo  Môi trường dev đã sẵn sàng tại: http://127.0.0.1:5173
echo ========================================================
pause

