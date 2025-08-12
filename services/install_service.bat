@echo off
chcp 65001 >nul
echo 文件自動分類工具 - 安裝為 Windows 服務
echo ==========================================
echo.

REM 檢查管理員權限
net session >nul 2>&1
if errorlevel 1 (
    echo 錯誤：需要管理員權限來安裝服務！
    echo 請右鍵點擊此文件，選擇「以管理員身分執行」
    pause
    exit /b 1
)

REM 檢查 Python 是否安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo 錯誤：未找到 Python！
    echo 請先安裝 Python
    pause
    exit /b 1
)

REM 獲取當前目錄
set CURRENT_DIR=%~dp0
set CURRENT_DIR=%CURRENT_DIR:~0,-1%

echo 當前目錄: %CURRENT_DIR%
echo.

REM 安裝依賴
echo 安裝必要的依賴套件...
pip install pywin32 schedule PyYAML
if errorlevel 1 (
    echo 嘗試使用國內鏡像源...
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pywin32 schedule PyYAML
)

REM 創建服務腳本
echo 創建服務腳本...
(
echo import win32serviceutil
echo import win32service
echo import win32event
echo import servicemanager
echo import socket
echo import sys
echo import os
echo import time
echo from pathlib import Path
echo.
echo # 添加當前目錄到 Python 路徑
echo sys.path.insert^(0, r'%CURRENT_DIR%'^)
echo.
echo # 導入主程序
echo from file_organizer import load_config, run_scheduler
echo.
echo class FileOrganizerService^(win32serviceutil.ServiceFramework^):
echo     _svc_name_ = "FileOrganizerService"
echo     _svc_display_name_ = "文件自動分類服務"
echo     _svc_description_ = "定期執行文件自動分類任務"
echo.
echo     def __init__^(self, args^):
echo         win32serviceutil.ServiceFramework.__init__^(self, args^)
echo         self.hWaitStop = win32event.CreateEvent^(None, 0, 0, None^)
echo         socket.setdefaulttimeout^(60^)
echo         self.is_alive = True
echo.
echo     def SvcStop^(self^):
echo         self.ReportServiceStatus^(win32service.SERVICE_STOP_PENDING^)
echo         win32event.SetEvent^(self.hWaitStop^)
echo         self.is_alive = False
echo.
echo     def SvcDoRun^(self^):
echo         servicemanager.LogMsg^(servicemanager.EVENTLOG_INFORMATION_TYPE,
echo                               servicemanager.PYS_SERVICE_STARTED,
echo                               ^(self._svc_name_, ''^^)^)
echo         self.main^(^)
echo.
echo     def main^(self^):
echo         # 切換到服務目錄
echo         os.chdir^(r'%CURRENT_DIR%'^)
echo         
echo         # 載入配置
echo         config = load_config^(^)
echo         if config is None:
echo             servicemanager.LogErrorMsg^("無法載入配置文件"^)
echo             return
echo         
echo         # 檢查是否啟用調度
echo         schedule_config = config.get^("schedule", {}^)
echo         if not schedule_config.get^("enabled", False^):
echo             servicemanager.LogErrorMsg^("定期運行功能未啟用"^)
echo             return
echo         
echo         try:
echo             run_scheduler^(config^)
echo         except Exception as e:
echo             servicemanager.LogErrorMsg^(f"服務執行錯誤: {e}"^)
echo.
echo if __name__ == '__main__':
echo     win32serviceutil.HandleCommandLine^(FileOrganizerService^)
) > file_organizer_service.py

echo.
echo 安裝服務...
python file_organizer_service.py install

if errorlevel 1 (
    echo 服務安裝失敗！
    pause
    exit /b 1
)

echo.
echo 服務安裝成功！
echo.
echo 使用方法：
echo   啟動服務: net start FileOrganizerService
echo   停止服務: net stop FileOrganizerService
echo   移除服務: python file_organizer_service.py remove
echo.
echo 注意：請確保 config.yaml 中的 schedule.enabled 設為 true
echo.
pause