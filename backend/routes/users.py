from flask import Blueprint, request, jsonify, session
from ..auth import login, logout, change_password, get_user_info, update_user_profile, get_all_users, create_user, update_user, delete_user, login_required, admin_required
from ..app import db
from ..models import User, Log
from datetime import datetime

user_bp = Blueprint('users', __name__)

# 用户登录
@user_bp.route('/login', methods=['POST'])
def user_login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'code': 400,
                'message': '请输入用户名和密码'
            })
        
        success, message = login(username, password)
        if not success:
            # 记录登录失败日志
            log = Log(
                username=username,
                action='登录失败',
                details=message,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({
                'code': 401,
                'message': message
            })
        
        # 记录登录成功日志
        log = Log(
            username=username,
            action='登录成功',
            details='用户登录成功',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(log)
        db.session.commit()
        
        # 获取用户角色，用于前端跳转
        user = User.query.filter_by(username=username).first()
        
        return jsonify({
            'code': 200,
            'data': {
                'username': username,
                'role': user.role if user else 'user',
                'redirect_url': '/static/admin.html' if user and user.role == 'admin' else '/static/user.html'
            },
            'message': message
        })
    except Exception as e:
        print(f'登录失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '登录失败，请稍后重试'
        })

# 用户登出
@user_bp.route('/logout', methods=['POST'])
def user_logout():
    try:
        username = session.get('username', '未知用户')
        success, message = logout()
        
        # 记录登出日志
        log = Log(
            username=username,
            action='登出',
            details='用户登出成功',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': message
        })
    except Exception as e:
        print(f'登出失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '登出失败，请稍后重试'
        })

# 获取当前用户信息
@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    try:
        username = session.get('username')
        user_info = get_user_info(username)
        
        if not user_info:
            return jsonify({
                'code': 404,
                'message': '用户不存在'
            })
        
        return jsonify({
            'code': 200,
            'data': user_info,
            'message': '获取用户信息成功'
        })
    except Exception as e:
        print(f'获取用户信息失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '获取用户信息失败'
        })

# 更新用户信息
@user_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    try:
        data = request.json
        user_id = session.get('user_id')
        
        success, message = update_user_profile(user_id, data)
        if not success:
            return jsonify({
                'code': 400,
                'message': message
            })
        
        # 记录更新日志
        log = Log(
            username=session.get('username'),
            action='更新个人信息',
            details=f'用户ID: {user_id}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': message
        })
    except Exception as e:
        print(f'更新用户信息失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '更新用户信息失败'
        })

# 修改密码
@user_bp.route('/change-password', methods=['POST'])
@login_required
def user_change_password():
    try:
        data = request.json
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not old_password or not new_password or not confirm_password:
            return jsonify({
                'code': 400,
                'message': '请填写所有密码字段'
            })
        
        if new_password != confirm_password:
            return jsonify({
                'code': 400,
                'message': '两次输入的新密码不一致'
            })
        
        if len(new_password) < 6:
            return jsonify({
                'code': 400,
                'message': '新密码长度至少为6位'
            })
        
        user_id = session.get('user_id')
        success, message = change_password(user_id, old_password, new_password)
        
        if not success:
            return jsonify({
                'code': 400,
                'message': message
            })
        
        # 记录密码修改日志
        log = Log(
            username=session.get('username'),
            action='修改密码',
            details=f'用户ID: {user_id}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': message
        })
    except Exception as e:
        print(f'修改密码失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '修改密码失败'
        })

# 管理员功能：获取所有用户列表
@user_bp.route('/all', methods=['GET'])
@admin_required
def get_users_list():
    try:
        users = get_all_users()
        
        return jsonify({
            'code': 200,
            'data': users,
            'message': '获取用户列表成功'
        })
    except Exception as e:
        print(f'获取用户列表失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '获取用户列表失败'
        })

# 管理员功能：创建用户
@user_bp.route('/create', methods=['POST'])
@admin_required
def create_new_user():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'user')
        department = data.get('department')
        phone = data.get('phone')
        email = data.get('email')
        
        # 验证必填字段
        if not username or not password:
            return jsonify({
                'code': 400,
                'message': '用户名和密码不能为空'
            })
        
        if len(password) < 6:
            return jsonify({
                'code': 400,
                'message': '密码长度至少为6位'
            })
        
        success, message = create_user(username, password, role, department, phone, email)
        
        if not success:
            return jsonify({
                'code': 400,
                'message': message
            })
        
        # 记录创建用户日志
        log = Log(
            username=session.get('username'),
            action='创建用户',
            details=f'用户名: {username}, 角色: {role}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': message
        })
    except Exception as e:
        print(f'创建用户失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '创建用户失败'
        })

# 管理员功能：更新用户信息
@user_bp.route('/<int:user_id>', methods=['PUT'])
@admin_required
def update_user_info(user_id):
    try:
        data = request.json
        success, message = update_user(user_id, data)
        
        if not success:
            return jsonify({
                'code': 400,
                'message': message
            })
        
        # 记录更新用户日志
        log = Log(
            username=session.get('username'),
            action='更新用户信息',
            details=f'用户ID: {user_id}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': message
        })
    except Exception as e:
        print(f'更新用户信息失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '更新用户信息失败'
        })

# 管理员功能：删除用户
@user_bp.route('/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user_account(user_id):
    try:
        success, message = delete_user(user_id)
        
        if not success:
            return jsonify({
                'code': 400,
                'message': message
            })
        
        # 记录删除用户日志
        log = Log(
            username=session.get('username'),
            action='删除用户',
            details=f'用户ID: {user_id}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': message
        })
    except Exception as e:
        print(f'删除用户失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '删除用户失败'
        })

# 获取用户统计信息
@user_bp.route('/statistics', methods=['GET'])
@admin_required
def get_user_statistics():
    try:
        # 统计用户数量
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        admin_users = User.query.filter_by(role='admin').count()
        normal_users = User.query.filter_by(role='user').count()
        
        # 统计最近登录的用户
        recent_login_users = User.query.filter(User.last_login.isnot(None))\
            .order_by(User.last_login.desc())\
            .limit(10)\
            .all()
        
        recent_logins = [
            {
                'username': user.username,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'role': user.role
            }
            for user in recent_login_users
        ]
        
        # 统计部门分布
        department_stats = db.session.query(
            User.department,
            db.func.count(User.id).label('count')
        ).filter(
            User.department.isnot(None)
        ).group_by(
            User.department
        ).all()
        
        departments = [
            {
                'name': dept[0],
                'count': dept[1]
            }
            for dept in department_stats
        ]
        
        return jsonify({
            'code': 200,
            'data': {
                'total_users': total_users,
                'active_users': active_users,
                'admin_users': admin_users,
                'normal_users': normal_users,
                'recent_logins': recent_logins,
                'department_distribution': departments
            },
            'message': '获取用户统计信息成功'
        })
    except Exception as e:
        print(f'获取用户统计信息失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '获取用户统计信息失败'
        })

# 检查登录状态
@user_bp.route('/check-login', methods=['GET'])
def check_login_status():
    try:
        if 'username' in session:
            user = User.query.filter_by(username=session['username']).first()
            return jsonify({
                'code': 200,
                'data': {
                    'is_logged_in': True,
                    'username': session['username'],
                    'role': user.role if user else 'user'
                },
                'message': '已登录'
            })
        else:
            return jsonify({
                'code': 200,
                'data': {
                    'is_logged_in': False
                },
                'message': '未登录'
            })
    except Exception as e:
        print(f'检查登录状态失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '检查登录状态失败'
        })