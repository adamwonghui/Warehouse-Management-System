from datetime import datetime
from .app import db

class ItemCategory(db.Model):
    """物品分类模型"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ItemCategory {self.name}>'

class Item(db.Model):
    """物品模型"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False, default='未分类', index=True)
    total = db.Column(db.Integer, nullable=False, default=0)
    in_stock = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Item {self.name}>'

class Request(db.Model):
    """物品申请模型"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), nullable=False, index=True)
    item_id = db.Column(db.Integer, nullable=False, index=True)
    item_name = db.Column(db.String(200), nullable=False)
    item_category = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    purpose = db.Column(db.Text, nullable=False)
    
    # 状态：pending(待审批), approved(已批准), rejected(已拒绝), returned(已归还), partially_returned(部分归还)
    status = db.Column(db.String(50), nullable=False, default='pending', index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    approver = db.Column(db.String(100), nullable=True)
    comment = db.Column(db.Text)
    
    # 归还相关
    returned_quantity = db.Column(db.Integer, default=0)
    returned_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Request {self.id} - {self.username} - {self.item_name}>'

class User(db.Model):
    """用户模型"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')  # user, admin
    department = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Log(db.Model):
    """系统日志模型"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=True)
    username = db.Column(db.String(100), nullable=True, index=True)
    action = db.Column(db.String(200), nullable=False)  # 操作类型
    target_type = db.Column(db.String(50), nullable=True)  # 目标类型：item, request, user等
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text)  # 操作详情
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Log {self.id} - {self.username} - {self.action}>'

class SystemConfig(db.Model):
    """系统配置模型"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemConfig {self.key}>'

class Notification(db.Model):
    """通知模型"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=True)
    username = db.Column(db.String(100), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # system, request, approval等
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Notification {self.id} - {self.username} - {self.title}>'