@echo off
chcp 65001 >nul
REM Windows 一键运行：双击本文件即可（自动建环境、装依赖、起服务、开浏览器）。
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo 未检测到 Python。请先安装：https://www.python.org/downloads/
  echo 安装时务必勾选 "Add Python to PATH"，装好后再双击本文件。
  pause & exit /b 1
)

if not exist .venv ( python -m venv .venv )
echo 正在安装/检查依赖...
call .venv\Scripts\python -m pip install -q -r requirements.txt

echo 启动中... 几秒后浏览器会自动打开 http://localhost:5001
start "" http://localhost:5001
call .venv\Scripts\python start.py
pause
