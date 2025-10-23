from flask import Flask, request, jsonify, send_from_directory
import os
from datetime import datetime
import logging
from models.db import db, User, Item, Request
from routes.auth import auth_bp
from routes.items import items_bp
from routes.requests import requests_bp

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("warehouse.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__, instance_relative_config=True)

# 加载配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///../instance/warehouse.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

# 注册蓝图
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(items_bp, url_prefix='/api/items')
app.register_blueprint(requests_bp, url_prefix='/api/requests')

# 允许跨域
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# 提供静态文件访问
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

# 主页路由 - 重定向到登录页面
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({'code': 404, 'message': '页面不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f'内部错误: {str(error)}')
    return jsonify({'code': 500, 'message': '服务器内部错误'}), 500

# 创建数据库表和默认用户
with app.app_context():
    try:
        db.create_all()
        logger.info('数据库表创建成功')
        
        # 检查是否已有用户
        if User.query.count() == 0:
            # 创建默认用户
            admin = User(username='admin', password='admin123', role='admin')
            user = User(username='user', password='user123', role='user')
            db.session.add(admin)
            db.session.add(user)
            db.session.commit()
            logger.info('默认用户创建成功')
    except Exception as e:
        logger.error(f'数据库初始化错误: {str(e)}')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    host = os.environ.get('HOST', '0.0.0.0')
    app.run(host=host, port=port, debug=True)