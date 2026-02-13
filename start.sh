#!/bin/bash

# 激活虚拟环境
source venv/bin/activate

# 启动 Flask 应用
echo "正在启动 Claude 网页版..."
echo "访问地址: http://localhost:5000"
echo "登录用户名: junner"
echo "登录密码: xingfu@1984"
python app.py
