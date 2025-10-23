from functools import wraps
from flask import request, jsonify, session
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .app import db
from .models import User

def login_required(f):
    """登录装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({
                'code': 401,
                'message': '请先登录'
            })
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({
                'code': 401,
                'message': '请先登录'
            })
        
        user = User.query.filter_by(username=session['username']).first()
        if not user or user.role != 'admin':
            return jsonify({
                'code': 403,
                'message': '没有管理员权限'
            })
        return f(*args, **kwargs)
    return decorated_function

def authenticate_user(username, password):
    """验证用户身份"""
    user = User.query.filter_by(username=username).first()
    if not user:
        return None, False, "用户不存在"
    
    if not user.is_active:
        return None, False, "账户已被禁用"
    
    if not check_password_hash(user.password, password):
        return None, False, "密码错误"
    
    return user, True, "验证成功"

def login(username, password):
    """用户登录"""
    user, success, message = authenticate_user(username, password)
    if not success:
        return False, message
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # 设置会话
    session['username'] = user.username
    session['user_id'] = user.id
    session['role'] = user.role
    
    return True, "登录成功"

def logout():
    """用户登出"""
    session.pop('username', None)
    session.pop('user_id', None)
    session.pop('role', None)
    return True, "登出成功"

def change_password(user_id, old_password, new_password):
    """修改密码"""
    user = User.query.get(user_id)
    if not user:
        return False, "用户不存在"
    
    # 验证旧密码
    if not check_password_hash(user.password, old_password):
        return False, "原密码错误"
    
    # 更新密码
    user.password = generate_password_hash(new_password)
    user.updated_at = datetime.utcnow()
    db.session.commit()
    
    return True, "密码修改成功"

def get_user_info(username):
    """获取用户信息"""
    user = User.query.filter_by(username=username).first()
    if not user:
        return None
    
    return {
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'department': user.department,
        'phone': user.phone,
        'email': user.email,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None
    }

def update_user_profile(user_id, data):
    """更新用户信息"""
    user = User.query.get(user_id)
    if not user:
        return False, "用户不存在"
    
    # 更新用户信息
    if 'department' in data:
        user.department = data['department']
    
    if 'phone' in data:
        user.phone = data['phone']
    
    if 'email' in data:
        user.email = data['email']
    
    user.updated_at = datetime.utcnow()
    db.session.commit()
    
    return True, "用户信息更新成功"

def create_user(username, password, role='user', department=None, phone=None, email=None):
    """创建用户"""
    # 检查用户名是否已存在
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return False, "用户名已存在"
    
    # 创建新用户
    new_user = User(
        username=username,
        password=generate_password_hash(password),
        role=role,
        department=department,
        phone=phone,
        email=email
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return True, "用户创建成功"

def update_user(user_id, data):
    """更新用户(管理员用)"""
    user = User.query.get(user_id)
    if not user:
        return False, "用户不存在"
    
    # 检查是否是更新自己的角色为非管理员
    if 'role' in data and session['username'] == user.username and data['role'] != 'admin':
        return False, "不能将自己的角色降级"
    
    # 更新用户信息
    if 'username' in data:
        # 检查新用户名是否已被使用
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user and existing_user.id != user_id:
            return False, "用户名已存在"
        user.username = data['username']
    
    if 'role' in data:
        user.role = data['role']
    
    if 'department' in data:
        user.department = data['department']
    
    if 'phone' in data:
        user.phone = data['phone']
    
    if 'email' in data:
        user.email = data['email']
    
    if 'is_active' in data:
        # 不能禁用自己
        if session['username'] == user.username and not data['is_active']:
            return False, "不能禁用自己的账户"
        user.is_active = data['is_active']
    
    if 'password' in data and data['password']:
        user.password = generate_password_hash(data['password'])
    
    user.updated_at = datetime.utcnow()
    db.session.commit()
    
    return True, "用户信息更新成功"

def delete_user(user_id):
    """删除用户(管理员用)"""
    user = User.query.get(user_id)
    if not user:
        return False, "用户不存在"
    
    # 不能删除自己
    if session['username'] == user.username:
        return False, "不能删除自己的账户"
    
    # 不能删除最后一个管理员
    if user.role == 'admin':
        admin_count = User.query.filter_by(role='admin').count()
        if admin_count <= 1:
            return False, "不能删除最后一个管理员账户"
    
    db.session.delete(user)
    db.session.commit()
    
    return True, "用户删除成功"

def get_all_users():
    """获取所有用户(管理员用)"""
    users = User.query.all()
    return [
        {
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'department': user.department,
            'phone': user.phone,
            'email': user.email,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'is_active': user.is_active
        }
        for user in users
    ]