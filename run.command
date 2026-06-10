#!/usr/bin/env bash
# Mac 一键运行：在访达里双击本文件即可（自动建环境、装依赖、起服务、开浏览器）。
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "未检测到 Python 3。请先安装：https://www.python.org/downloads/"
  echo "（装好后再双击本文件）"; read -n 1 -s -r -p "按任意键退出…"; exit 1
fi

[ -d .venv ] || python3 -m venv .venv
echo "正在安装/检查依赖…"
.venv/bin/pip install -q -r requirements.txt

echo "启动中… 几秒后浏览器会自动打开 http://localhost:5001"
( sleep 3; open "http://localhost:5001" ) &
.venv/bin/python start.py
