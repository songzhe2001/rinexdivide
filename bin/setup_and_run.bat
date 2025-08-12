@echo off
chcp 65001 >nul
echo ========================================
echo 文件自動分類工具 - 安裝依賴並運行
echo ========================================
echo.

:: 檢查 Python 是否已安裝
echo [1/3] 檢查 Python...
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Python 已安裝
    python --version
) else (
    echo ✗ Python 未安裝！
    echo 請先安裝 Python: https://www.python.org/downloads/
    echo 或運行 auto_install_and_run.bat 進行自動安裝
    pause
    exit /b 1
)

echo.
echo [2/3] 安裝 Python 套件...

:: 檢查 pip
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 修復 pip...
    python -m ensurepip --upgrade
    python -m pip install --upgrade pip
)

:: 安裝套件
echo 正在安裝必要套件...
if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    pip install PyYAML>=6.0
)

if %errorlevel% == 0 (
    echo ✓ 套件安裝成功！
) else (
    echo 嘗試使用國內鏡像...
    if exist "requirements.txt" (
        pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
    ) else (
        pip install -i https://pypi.tuna.tsinghua.edu.cn/simple PyYAML>=6.0
    )
)

echo.
echo [3/3] 啟動文件分類工具...
echo ========================================
echo.

:: 切換到根目錄
cd /d "%~dp0\.."

:: 檢查配置文件
if exist "config\config.yaml" (
    echo 使用 config\config.yaml 配置文件
) else if exist "config\config.json" (
    echo 使用 config\config.json 配置文件
) else if exist "config\config.ini" (
    echo 使用 config\config.ini 配置文件
) else if exist "config.yaml" (
    echo 使用 config.yaml 配置文件
) else if exist "config.json" (
    echo 使用 config.json 配置文件
) else (
    echo ✗ 未找到配置文件！
    echo 請在 config\ 目錄下創建配置文件：
    echo   - config\config.yaml (推薦)
    echo   - config\config.json
    echo   - config\config.ini
    pause
    exit /b 1
)

python file_organizer.py
echo.
echo 程式執行完畢！
pause
