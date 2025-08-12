# 文件自動分類工具 - 安裝為 Windows 服務 (PowerShell)
# 需要管理員權限

param(
    [switch]$Uninstall
)

Write-Host "文件自動分類工具 - Windows 服務安裝" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# 檢查管理員權限
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "錯誤：需要管理員權限來安裝服務！" -ForegroundColor Red
    Write-Host "請以管理員身分運行 PowerShell" -ForegroundColor Yellow
    Read-Host "按 Enter 鍵退出"
    exit 1
}

# 檢查 Python 是否安裝
try {
    $pythonVersion = python --version 2>&1
    Write-Host "找到 Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "錯誤：未找到 Python！" -ForegroundColor Red
    Write-Host "請先安裝 Python" -ForegroundColor Yellow
    Read-Host "按 Enter 鍵退出"
    exit 1
}

$currentDir = Get-Location

if ($Uninstall) {
    Write-Host "移除服務..." -ForegroundColor Yellow
    try {
        Stop-Service -Name "FileOrganizerService" -ErrorAction SilentlyContinue
        python file_organizer_service.py remove
        Write-Host "服務移除成功！" -ForegroundColor Green
    } catch {
        Write-Host "服務移除失敗：$($_.Exception.Message)" -ForegroundColor Red
    }
    Read-Host "按 Enter 鍵退出"
    exit
}

Write-Host "當前目錄: $currentDir" -ForegroundColor Cyan
Write-Host ""

# 安裝依賴
Write-Host "安裝必要的依賴套件..." -ForegroundColor Yellow
try {
    pip install pywin32 schedule PyYAML
    Write-Host "依賴套件安裝成功" -ForegroundColor Green
} catch {
    Write-Host "嘗試使用國內鏡像源..." -ForegroundColor Yellow
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pywin32 schedule PyYAML
}

# 創建服務腳本
Write-Host "創建服務腳本..." -ForegroundColor Yellow

$serviceScript = @"
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import time
import logging
from pathlib import Path

# 添加當前目錄到 Python 路徑
sys.path.insert(0, r'$currentDir')

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(r'$currentDir\service.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 導入主程序
try:
    from file_organizer import load_config, run_file_organization, parse_schedule_config
    import schedule
except ImportError as e:
    logging.error(f"導入模組失敗: {e}")
    raise

class FileOrganizerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FileOrganizerService"
    _svc_display_name_ = "文件自動分類服務"
    _svc_description_ = "定期執行文件自動分類任務"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_alive = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False
        logging.info("服務停止請求")

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        logging.info("服務開始運行")
        self.main()

    def main(self):
        # 切換到服務目錄
        os.chdir(r'$currentDir')
        
        try:
            # 載入配置
            config = load_config()
            if config is None:
                logging.error("無法載入配置文件")
                servicemanager.LogErrorMsg("無法載入配置文件")
                return
            
            # 檢查是否啟用調度
            schedule_config = config.get("schedule", {})
            if not schedule_config.get("enabled", False):
                logging.error("定期運行功能未啟用")
                servicemanager.LogErrorMsg("定期運行功能未啟用")
                return
            
            # 解析調度配置
            if not parse_schedule_config(schedule_config):
                logging.error("調度配置解析失敗")
                servicemanager.LogErrorMsg("調度配置解析失敗")
                return
            
            # 是否在啟動時立即執行一次
            if schedule_config.get("run_on_start", False):
                logging.info("啟動時立即執行一次...")
                run_file_organization(config)
            
            logging.info("調度器已啟動")
            
            # 運行調度器
            while self.is_alive:
                schedule.run_pending()
                # 檢查停止事件，等待1秒
                if win32event.WaitForSingleObject(self.hWaitStop, 1000) == win32event.WAIT_OBJECT_0:
                    break
                    
        except Exception as e:
            logging.error(f"服務執行錯誤: {e}")
            servicemanager.LogErrorMsg(f"服務執行錯誤: {e}")
        
        logging.info("服務結束運行")

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(FileOrganizerService)
"@

$serviceScript | Out-File -FilePath "file_organizer_service.py" -Encoding UTF8

Write-Host ""
Write-Host "安裝服務..." -ForegroundColor Yellow
try {
    python file_organizer_service.py install
    Write-Host "服務安裝成功！" -ForegroundColor Green
} catch {
    Write-Host "服務安裝失敗：$($_.Exception.Message)" -ForegroundColor Red
    Read-Host "按 Enter 鍵退出"
    exit 1
}

Write-Host ""
Write-Host "使用方法：" -ForegroundColor Cyan
Write-Host "  啟動服務: Start-Service FileOrganizerService" -ForegroundColor White
Write-Host "  停止服務: Stop-Service FileOrganizerService" -ForegroundColor White
Write-Host "  查看狀態: Get-Service FileOrganizerService" -ForegroundColor White
Write-Host "  移除服務: .\install_service.ps1 -Uninstall" -ForegroundColor White
Write-Host ""
Write-Host "注意：請確保 config.yaml 中的 schedule.enabled 設為 true" -ForegroundColor Yellow
Write-Host "服務日誌將保存在: $currentDir\service.log" -ForegroundColor Cyan
Write-Host ""

Read-Host "按 Enter 鍵退出"