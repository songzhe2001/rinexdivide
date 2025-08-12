# 文件自動分類工具 - PowerShell 自動安裝腳本
# 設置執行策略：Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "文件自動分類工具 - 自動安裝和運行" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 檢查 Python 是否已安裝
Write-Host "[1/4] 檢查 Python 安裝狀態..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Python 已安裝: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python 未安裝"
    }
} catch {
    Write-Host "✗ Python 未安裝" -ForegroundColor Red
    Write-Host ""
    Write-Host "[2/4] 準備安裝 Python..." -ForegroundColor Yellow
    
    # 檢查是否有 winget
    try {
        winget --version | Out-Null
        Write-Host "使用 winget 安裝 Python..." -ForegroundColor Green
        winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
        
        # 刷新 PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        # 再次檢查
        $pythonVersion = python --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Python 安裝成功: $pythonVersion" -ForegroundColor Green
        } else {
            throw "Python 安裝失敗"
        }
    } catch {
        Write-Host "✗ 無法使用 winget 安裝 Python" -ForegroundColor Red
        Write-Host "請手動安裝 Python: https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "安裝時請勾選 'Add Python to PATH'" -ForegroundColor Yellow
        Read-Host "按 Enter 鍵退出"
        exit 1
    }
}

Write-Host ""
Write-Host "[3/4] 檢查並安裝 Python 套件..." -ForegroundColor Yellow

# 檢查 pip
try {
    pip --version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "修復 pip..." -ForegroundColor Yellow
        python -m ensurepip --upgrade
        python -m pip install --upgrade pip
    }
} catch {
    Write-Host "✗ pip 不可用" -ForegroundColor Red
}

# 安裝套件
Write-Host "正在安裝 PyYAML..." -ForegroundColor Yellow
try {
    pip install PyYAML>=6.0 --quiet
    Write-Host "✓ 套件安裝成功！" -ForegroundColor Green
} catch {
    Write-Host "嘗試使用國內鏡像..." -ForegroundColor Yellow
    try {
        pip install -i https://pypi.tuna.tsinghua.edu.cn/simple PyYAML>=6.0 --quiet
        Write-Host "✓ 套件安裝成功！" -ForegroundColor Green
    } catch {
        Write-Host "✗ 套件安裝失敗，請檢查網路連接" -ForegroundColor Red
        Read-Host "按 Enter 鍵退出"
        exit 1
    }
}

Write-Host ""
Write-Host "[4/4] 啟動文件分類工具..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 檢查配置文件
if (Test-Path "config.yaml") {
    Write-Host "找到 config.yaml 配置文件" -ForegroundColor Green
} elseif (Test-Path "config.json") {
    Write-Host "找到 config.json 配置文件" -ForegroundColor Green
} else {
    Write-Host "✗ 未找到配置文件！" -ForegroundColor Red
    Write-Host "請創建 config.yaml 或 config.json 配置文件" -ForegroundColor Yellow
    Write-Host "參考 config_example.json 或現有的 config.yaml 範例" -ForegroundColor Yellow
    Read-Host "按 Enter 鍵退出"
    exit 1
}

# 運行主程式
python file_organizer.py

Write-Host ""
Write-Host "程式執行完畢！" -ForegroundColor Green
Read-Host "按 Enter 鍵退出"