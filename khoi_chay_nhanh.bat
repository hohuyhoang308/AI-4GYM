@echo off
chcp 65001 >nul
echo ========================================================
echo        KHỞI CHẠY CHATBOT AI-4GYM (BẢN CHÍNH THỨC)
echo ========================================================
echo.

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

:: 2. Khởi chạy Backend FastAPI (phục vụ giao diện tại cổng 8000)
echo.
echo [2/3] Đang khởi chạy Chatbot Backend tại http://127.0.0.1:8000 ...
cd /d "%~dp0BE"
start "AI-4GYM Backend" .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

:: 3. Mở trình duyệt
echo.
echo [3/3] Đang mở giao diện Chatbot trên trình duyệt...
timeout /t 2 /nobreak >nul
start http://127.0.0.1:8000

echo.
echo ========================================================
echo  Chatbot đã sẵn sàng tại: http://127.0.0.1:8000
echo ========================================================
pause

