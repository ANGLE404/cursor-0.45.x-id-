@echo off
chcp 65001 > nul
cls

:: 檢查是否以管理員權限運行
net session >nul 2>&1
if %errorLevel% == 0 (
    :: 如果是管理員權限，只創建虛擬環境後就降權運行
    if not exist venv (
        echo ℹ️ 正在創建虛擬環境...
        python -m venv venv
    )
    
    :: 降權運行剩餘的步驟
    echo ℹ️ 以普通用戶權限繼續...
    powershell -Command "Start-Process -FilePath '%comspec%' -ArgumentList '/c cd /d %cd% && %~f0 run' -Verb RunAs:NO"
    exit /b
) else (
    :: 檢查是否是第二階段運行
    if "%1"=="run" (
        goto RUN_BUILD
    ) else (
        :: 如果是普通權限且需要創建虛擬環境，請求管理員權限
        if not exist venv (
            echo ⚠️ 需要管理員權限來創建虛擬環境
            echo ℹ️ 正在請求管理員權限...
            powershell -Command "Start-Process -Verb RunAs -FilePath '%comspec%' -ArgumentList '/c cd /d %cd% && %~f0'"
            exit /b
        ) else (
            goto RUN_BUILD
        )
    )
)

:RUN_BUILD
echo ℹ️ 啟動虛擬環境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 啟動虛擬環境失敗
    pause
    exit /b 1
)

:: 檢查並安裝缺失的依賴
echo ℹ️ 檢查依賴...
for /f "tokens=1" %%i in (requirements.txt) do (
    pip show %%i >nul 2>&1 || (
        echo ℹ️ 安裝 %%i...
        pip install %%i
    )
)

echo ℹ️ 開始構建...
python build.py
if errorlevel 1 (
    echo ❌ 構建失敗
    pause
    exit /b 1
)

echo ✅ 完成！
pause 