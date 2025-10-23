from flask import Blueprint, request, jsonify
from models.db import db, User
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400
        
        # 查询用户
        user = User.query.filter_by(username=username).first()
        
        if not user or user.password != password:
            logger.warning(f'登录失败: 用户 {username} 密码错误')
            return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401
        
        logger.info(f'用户 {username} 登录成功')
        return jsonify({
            'code': 200,
            'message': '登录成功',
            'data': {
                'username': user.username,
                'role': user.role
            }
        })
    except Exception as e:
        logger.error(f'登录错误: {str(e)}')
        return jsonify({'code': 500, 'message': '登录失败，请稍后重试'}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'user')
        
        if not username or not password:
            return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400
        
        # 检查用户是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({'code': 400, 'message': '用户名已存在'}), 400
        
        # 创建新用户
        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f'新用户注册成功: {username}')
        return jsonify({
            'code': 200,
            'message': '注册成功',
            'data': {
                'username': new_user.username,
                'role': new_user.role
            }
        })
    except Exception as e:
        logger.error(f'注册错误: {str(e)}')
        db.session.rollback()
        return jsonify({'code': 500, 'message': '注册失败，请稍后重试'}), 500