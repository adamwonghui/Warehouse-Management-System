from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # admin 或 user
    created_at = db.Column(db.DateTime, default=datetime.now)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    total_count = db.Column(db.Integer, nullable=False)
    in_stock = db.Column(db.Integer, nullable=False)
    on_loan = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False)  # in_stock, out_of_stock, partial_in_stock
    user = db.Column(db.String(50))  # 当前使用人
    keeper = db.Column(db.String(50))  # 保管人
    entry_time = db.Column(db.DateTime, default=datetime.now)
    description = db.Column(db.Text)

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    item = db.relationship('Item', backref=db.backref('requests', lazy=True))
    quantity = db.Column(db.Integer, nullable=False)
    purpose = db.Column(db.String(200))
    status = db.Column(db.String(20), nullable=False)  # pending, approved, rejected, returned, partially_returned
    created_at = db.Column(db.DateTime, default=datetime.now)
    approved_at = db.Column(db.DateTime)
    approver = db.Column(db.String(50))
    comment = db.Column(db.Text)