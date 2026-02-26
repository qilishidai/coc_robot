@echo off
:: 切换到当前bat文件所在目录
cd /d "%~dp0"

:: 激活虚拟环境
call .venv\Scripts\activate.bat

:: 启动 UI入口.py
python UI入口.py

:: 等待用户按键后关闭窗口（可选）
pause