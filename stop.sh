#!/bin/bash

# 查找并停止 Flask 应用
echo "正在停止 Claude 网页版..."

# 查找运行 app.py 的进程
PID=$(ps aux | grep "python app.py" | grep -v grep | awk '{print $2}')

if [ -z "$PID" ]; then
    echo "未找到运行中的应用"
else
    kill $PID
    echo "应用已停止 (PID: $PID)"
fi
