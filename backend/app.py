from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建Flask应用
app = Flask(__name__, static_folder='../frontend', static_url_path='')

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///warehouse.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# 启用CORS
CORS(app)

# 创建数据库实例
db = SQLAlchemy(app)

# 数据库模型
class ItemCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    items = db.relationship('Item', backref='category_obj', lazy=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), db.ForeignKey('item_category.name'), nullable=False)
    total = db.Column(db.Integer, default=0)
    in_stock = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    item_category = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    purpose = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected, returned, partially_returned
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    approver = db.Column(db.String(100))
    comment = db.Column(db.Text)
    returned_quantity = db.Column(db.Integer, default=0)
    returned_at = db.Column(db.DateTime)
    item = db.relationship('Item', backref='requests')

# 初始化数据库
with app.app_context():
    db.create_all()
    # 确保默认分类存在
    if not ItemCategory.query.filter_by(name='未分类').first():
        default_category = ItemCategory(name='未分类', description='默认分类')
        db.session.add(default_category)
        db.session.commit()

# 导入路由
from routes.items import item_bp
from routes.requests import request_bp
from routes.admin import admin_bp

# 注册蓝图
app.register_blueprint(item_bp, url_prefix='/api/items')
app.register_blueprint(request_bp, url_prefix='/api/requests')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

# 静态文件路由
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

# 默认路由，返回前端页面
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

# 登录验证
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # 简单的用户验证（实际应用中应使用更安全的方式）
    if username == 'admin' and password == 'admin123':
        return jsonify({
            'code': 200,
            'data': {
                'username': username,
                'role': 'admin'
            },
            'message': '登录成功'
        })
    elif username == 'user' and password == 'user123':
        return jsonify({
            'code': 200,
            'data': {
                'username': username,
                'role': 'user'
            },
            'message': '登录成功'
        })
    else:
        return jsonify({
            'code': 401,
            'message': '用户名或密码错误'
        })

# 健康检查
@app.route('/api/health')
def health():
    return jsonify({
        'code': 200,
        'data': {
            'status': 'ok',
            'timestamp': datetime.utcnow().isoformat()
        }
    })

# 404错误处理
@app.errorhandler(404)
def not_found(error):
    # 尝试返回静态文件，如果不存在则返回404
    if request.path.startswith('/static/'):
        return send_from_directory('../frontend', request.path[8:]), 404
    return jsonify({
        'code': 404,
        'message': '接口不存在'
    }), 404

# 500错误处理
@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'code': 500,
        'message': '服务器内部错误'
    }), 500

if __name__ == '__main__':
    # 从环境变量获取配置
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # 启动应用
    app.run(host=host, port=port, debug=debug)