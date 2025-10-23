from flask import Blueprint, request, jsonify
from models.db import db, Item
import logging

items_bp = Blueprint('items', __name__)
logger = logging.getLogger(__name__)

@items_bp.route('/', methods=['GET'])
def get_items():
    try:
        # 获取查询参数
        name = request.args.get('name')
        category = request.args.get('category')
        status = request.args.get('status')
        
        # 构建查询
        query = Item.query
        
        if name:
            query = query.filter(Item.name.like(f'%{name}%'))
        if category:
            query = query.filter(Item.category == category)
        if status:
            query = query.filter(Item.status == status)
        
        items = query.all()
        
        # 转换为JSON格式
        result = []
        for item in items:
            result.append({
                'id': item.id,
                'name': item.name,
                'category': item.category,
                'unit': item.unit,
                'total_count': item.total_count,
                'in_stock': item.in_stock,
                'on_loan': item.on_loan,
                'status': item.status,
                'user': item.user,
                'keeper': item.keeper,
                'entry_time': item.entry_time,
                'description': item.description
            })
        
        return jsonify({
            'code': 200,
            'message': '获取物品列表成功',
            'data': result
        })
    except Exception as e:
        logger.error(f'获取物品列表错误: {str(e)}')
        return jsonify({'code': 500, 'message': '获取物品列表失败'}), 500

@items_bp.route('/', methods=['POST'])
def add_item():
    try:
        data = request.json
        
        # 创建新物品
        new_item = Item(
            name=data.get('name'),
            category=data.get('category'),
            unit=data.get('unit'),
            total_count=data.get('total_count'),
            in_stock=data.get('total_count'),  # 初始时全部在库
            on_loan=0,
            status='in_stock',
            keeper=data.get('keeper'),
            description=data.get('description')
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        logger.info(f'添加物品成功: {new_item.name}')
        return jsonify({
            'code': 200,
            'message': '添加物品成功',
            'data': {
                'id': new_item.id,
                'name': new_item.name
            }
        })
    except Exception as e:
        logger.error(f'添加物品错误: {str(e)}')
        db.session.rollback()
        return jsonify({'code': 500, 'message': '添加物品失败'}), 500

@items_bp.route('/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    try:
        data = request.json
        item = Item.query.get_or_404(item_id)
        
        # 更新物品信息
        item.name = data.get('name', item.name)
        item.category = data.get('category', item.category)
        item.unit = data.get('unit', item.unit)
        item.keeper = data.get('keeper', item.keeper)
        item.description = data.get('description', item.description)
        
        db.session.commit()
        
        logger.info(f'更新物品成功: {item.name}')
        return jsonify({
            'code': 200,
            'message': '更新物品成功',
            'data': {
                'id': item.id,
                'name': item.name
            }
        })
    except Exception as e:
        logger.error(f'更新物品错误: {str(e)}')
        db.session.rollback()
        return jsonify({'code': 500, 'message': '更新物品失败'}), 500

@items_bp.route('/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    try:
        item = Item.query.get_or_404(item_id)
        item_name = item.name
        
        db.session.delete(item)
        db.session.commit()
        
        logger.info(f'删除物品成功: {item_name}')
        return jsonify({
            'code': 200,
            'message': '删除物品成功'
        })
    except Exception as e:
        logger.error(f'删除物品错误: {str(e)}')
        db.session.rollback()
        return jsonify({'code': 500, 'message': '删除物品失败'}), 500

@items_bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        # 获取所有不重复的类别
        categories = db.session.query(Item.category).distinct().all()
        category_list = [cat[0] for cat in categories if cat[0]]
        
        return jsonify({
            'code': 200,
            'message': '获取类别列表成功',
            'data': category_list
        })
    except Exception as e:
        logger.error(f'获取类别列表错误: {str(e)}')
        return jsonify({'code': 500, 'message': '获取类别列表失败'}), 500