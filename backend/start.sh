#!/bin/bash

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "升级pip..."
pip install --upgrade pip

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 启动服务
echo "启动服务..."
echo "服务将运行在 http://localhost:5001"
echo "局域网内可通过 http://<本机IP>:5001 访问"
python app.py