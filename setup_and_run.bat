@echo off
chcp 65001 >nul
title 文件自动分类工具 - 首次设置

echo ========================================
echo      文件自动分类工具 - 首次设置
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到Python环境！
    echo.
    echo 请按照以下步骤安装Python：
    echo 1. 访问 https://www.python.org/downloads/
    echo 2. 下载最新版本的Python
    echo 3. 安装时勾选 "Add Python to PATH"
    echo 4. 安装完成后重新运行此脚本
    echo.
    pause
    exit /b 1
)

echo 检测到Python环境，版本信息：
python --version
echo.

REM 检查配置文件
if not exist "config.json" (
    echo 错误：找不到配置文件 config.json
    echo 请确保配置文件存在
    pause
    exit /b 1
)

echo 当前配置文件内容：
echo ----------------------------------------
type config.json
echo ----------------------------------------
echo.

echo 请确认以上配置是否正确：
echo 1. source_directory - 源文件夹路径
echo 2. o_files_directory - o文件目标目录
echo 3. p_files_directory - p文件目标目录
echo.

set /p confirm="配置正确吗？(y/n): "
if /i "%confirm%" neq "y" (
    echo.
    echo 请编辑 config.json 文件修改配置，然后重新运行此脚本
    echo 你可以用记事本打开 config.json 进行编辑
    pause
    exit /b 0
)

echo.
echo 配置确认完成！正在启动文件分类工具...
echo.

REM 运行Python脚本
python file_organizer.py

echo.
echo 程序执行完毕！
echo.
echo 提示：下次可以直接双击 run_file_organizer.bat 快速运行
pause