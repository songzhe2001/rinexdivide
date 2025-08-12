@echo off
chcp 65001 >nul
echo 文件自動分類工具 - 服務管理
echo ==============================
echo.

REM 檢查管理員權限
net session >nul 2>&1
if errorlevel 1 (
    echo 錯誤：需要管理員權限來管理服務！
    echo 請右鍵點擊此文件，選擇「以管理員身分執行」
    pause
    exit /b 1
)

:menu
echo 請選擇操作：
echo 1. 啟動服務
echo 2. 停止服務
echo 3. 重啟服務
echo 4. 查看服務狀態
echo 5. 移除服務
echo 6. 查看服務日誌
echo 0. 退出
echo.
set /p choice=請輸入選項 (0-6): 

if "%choice%"=="1" goto start_service
if "%choice%"=="2" goto stop_service
if "%choice%"=="3" goto restart_service
if "%choice%"=="4" goto status_service
if "%choice%"=="5" goto remove_service
if "%choice%"=="6" goto view_logs
if "%choice%"=="0" goto exit
echo 無效選項，請重新選擇。
echo.
goto menu

:start_service
echo 啟動文件自動分類服務...
net start FileOrganizerService
if errorlevel 1 (
    echo 服務啟動失敗！
) else (
    echo 服務啟動成功！
)
echo.
pause
goto menu

:stop_service
echo 停止文件自動分類服務...
net stop FileOrganizerService
if errorlevel 1 (
    echo 服務停止失敗！
) else (
    echo 服務停止成功！
)
echo.
pause
goto menu

:restart_service
echo 重啟文件自動分類服務...
net stop FileOrganizerService
timeout /t 2 /nobreak >nul
net start FileOrganizerService
if errorlevel 1 (
    echo 服務重啟失敗！
) else (
    echo 服務重啟成功！
)
echo.
pause
goto menu

:status_service
echo 查看服務狀態...
sc query FileOrganizerService
echo.
pause
goto menu

:remove_service
echo 移除文件自動分類服務...
net stop FileOrganizerService >nul 2>&1
python file_organizer_service.py remove
if errorlevel 1 (
    echo 服務移除失敗！
) else (
    echo 服務移除成功！
)
echo.
pause
goto menu

:view_logs
echo 查看 Windows 事件日誌中的服務日誌...
echo 請在事件檢視器中查看：
echo Windows 日誌 ^> 應用程式
echo 來源：FileOrganizerService
echo.
echo 或使用 PowerShell 命令：
echo Get-EventLog -LogName Application -Source FileOrganizerService -Newest 10
echo.
pause
goto menu

:exit
echo 退出服務管理工具。