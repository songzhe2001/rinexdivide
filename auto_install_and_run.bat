@echo off
chcp 65001 >nul
echo ========================================
echo 文件自動分類工具 - 自動安裝和運行
echo ========================================
echo.

:: 檢查 Python 是否已安裝
echo [1/4] 檢查 Python 安裝狀態...
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Python 已安裝
    python --version
    goto :check_pip
) else (
    echo ✗ Python 未安裝
    goto :install_python
)

:install_python
echo.
echo [2/4] 準備安裝 Python...
echo 正在下載 Python 安裝程式...

:: 創建臨時目錄
if not exist "temp" mkdir temp

:: 下載 Python 3.11.7 (穩定版本)
echo 下載中，請稍候...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe' -OutFile 'temp\python-installer.exe'}"

if not exist "temp\python-installer.exe" (
    echo ✗ Python 下載失敗！
    echo 請手動安裝 Python: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✓ Python 下載完成
echo 正在安裝 Python（這可能需要幾分鐘）...
echo 安裝選項：添加到 PATH、安裝 pip、關聯 .py 文件

:: 靜默安裝 Python，添加到 PATH
temp\python-installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

:: 等待安裝完成
timeout /t 10 /nobreak >nul

:: 刷新環境變數
call refreshenv >nul 2>&1

:: 再次檢查 Python
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Python 安裝成功！
    python --version
) else (
    echo ✗ Python 安裝可能失敗，請重新啟動命令提示字元或重新開機後再試
    echo 或手動安裝 Python: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 清理臨時文件
if exist "temp\python-installer.exe" del "temp\python-installer.exe"
if exist "temp" rmdir "temp"

:check_pip
echo.
echo [3/4] 檢查並安裝 Python 套件...

:: 檢查 pip 是否可用
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ pip 不可用，嘗試修復...
    python -m ensurepip --upgrade
    python -m pip install --upgrade pip
)

:: 安裝必要套件
echo 正在安裝必要套件...
pip install PyYAML>=6.0

if %errorlevel% == 0 (
    echo ✓ 套件安裝成功！
) else (
    echo ✗ 套件安裝失敗，嘗試使用國內鏡像...
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple PyYAML>=6.0
    if %errorlevel% neq 0 (
        echo ✗ 套件安裝失敗，請檢查網路連接
        pause
        exit /b 1
    )
)

:run_program
echo.
echo [4/4] 啟動文件分類工具...
echo ========================================
echo.

:: 檢查配置文件
if exist "config.yaml" (
    echo 找到 config.yaml 配置文件
) else if exist "config.json" (
    echo 找到 config.json 配置文件
) else (
    echo ✗ 未找到配置文件！
    echo 請創建 config.yaml 或 config.json 配置文件
    echo 參考 config_example.json 或現有的 config.yaml 範例
    pause
    exit /b 1
)

:: 運行主程式
python file_organizer.py

echo.
echo 程式執行完畢！
pause