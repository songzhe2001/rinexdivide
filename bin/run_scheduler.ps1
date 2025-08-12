# 文件自動分類工具 - 定期運行模式 (PowerShell)
# 需要管理員權限來安裝套件

Write-Host "文件自動分類工具 - 定期運行模式" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

# 檢查 Python 是否安裝
try {
    $pythonVersion = python --version 2>&1
    Write-Host "找到 Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "錯誤：未找到 Python！" -ForegroundColor Red
    Write-Host "請先安裝 Python 或運行 auto_install_and_run.bat" -ForegroundColor Yellow
    Read-Host "按 Enter 鍵退出"
    exit 1
}

# 檢查並安裝依賴
Write-Host "檢查依賴套件..." -ForegroundColor Yellow

# 檢查 schedule 套件
try {
    python -c "import schedule" 2>$null
    Write-Host "schedule 套件已安裝" -ForegroundColor Green
} catch {
    Write-Host "安裝 schedule 套件..." -ForegroundColor Yellow
    try {
        pip install schedule
        Write-Host "schedule 套件安裝成功" -ForegroundColor Green
    } catch {
        Write-Host "嘗試使用國內鏡像源..." -ForegroundColor Yellow
        pip install -i https://pypi.tuna.tsinghua.edu.cn/simple schedule
    }
}

# 檢查 PyYAML 套件
try {
    python -c "import yaml" 2>$null
    Write-Host "PyYAML 套件已安裝" -ForegroundColor Green
} catch {
    Write-Host "安裝 PyYAML 套件..." -ForegroundColor Yellow
    try {
        pip install PyYAML
        Write-Host "PyYAML 套件安裝成功" -ForegroundColor Green
    } catch {
        Write-Host "嘗試使用國內鏡像源..." -ForegroundColor Yellow
        pip install -i https://pypi.tuna.tsinghua.edu.cn/simple PyYAML
    }
}

Write-Host ""
Write-Host "啟動定期運行模式..." -ForegroundColor Green
Write-Host "注意：程序將持續運行，按 Ctrl+C 可停止" -ForegroundColor Yellow
Write-Host ""

# 切換到根目錄
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootPath = Split-Path -Parent $scriptPath
Set-Location $rootPath

# 運行程序
python file_organizer.py

Write-Host ""
Write-Host "程序已結束。" -ForegroundColor Green
Read-Host "按 Enter 鍵退出"