@echo off
chcp 65001 >nul
title 文件自动分类工具

echo ========================================
echo           文件自动分类工具
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到Python环境！
    echo 请先安装Python 3.6或更高版本
    echo 下载地址：https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM 检查必要文件是否存在
if not exist "file_organizer.py" (
    echo 错误：找不到 file_organizer.py 文件！
    echo 请确保所有文件都在同一目录下
    echo.
    pause
    exit /b 1
)

if not exist "config.json" (
    echo 错误：找不到 config.json 配置文件！
    echo 请确保配置文件存在
    echo.
    pause
    exit /b 1
)

echo 正在启动文件分类工具...
echo.

REM 运行Python脚本
python file_organizer.py

echo.
echo 程序执行完毕！
pause