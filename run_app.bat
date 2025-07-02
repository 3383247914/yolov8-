@echo off
setlocal

REM 设置项目目录
set PROJECT_DIR=C:\Users\pc\Desktop\基于yolov8的金属检测模型
cd /d "%PROJECT_DIR%"

REM 设置Python路径
set PYTHON_PATH=python

REM 安装依赖
echo 正在安装依赖...
%PYTHON_PATH% -m pip install -r requirements.txt

REM 运行UI应用
echo 启动金属缺陷检测系统...
%PYTHON_PATH% ui_app.py

endlocal
pause