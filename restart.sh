#!/bin/bash

# Claude Web 后台重启脚本

APP_DIR="/root/claude-web"
APP_FILE="app.py"
LOG_FILE="$APP_DIR/app.log"
PID_FILE="$APP_DIR/app.pid"

cd $APP_DIR

echo "正在停止应用..."

# 如果存在 PID 文件，尝试停止进程
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        kill $OLD_PID
        echo "已停止进程 $OLD_PID"
        sleep 2
    fi
    rm -f "$PID_FILE"
fi

# 查找并停止所有运行中的 app.py 进程
pkill -f "python.*$APP_FILE" && echo "已停止所有相关进程"
sleep 1

echo "正在启动应用..."

# 启动应用并记录 PID
nohup python3 $APP_FILE > $LOG_FILE 2>&1 &
NEW_PID=$!
echo $NEW_PID > $PID_FILE

echo "应用已启动，PID: $NEW_PID"
echo "日志文件: $LOG_FILE"
echo "查看日志: tail -f $LOG_FILE"

# 等待几秒检查进程是否正常运行
sleep 3
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo "✓ 应用运行正常"
else
    echo "✗ 应用启动失败，请查看日志"
    exit 1
fi
