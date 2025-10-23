from flask import Blueprint, request, jsonify
from datetime import datetime
from ..app import db
from ..models import Item, ItemCategory

item_bp = Blueprint('items', __name__)

# 获取物品列表
@item_bp.route('/', methods=['GET'])
def get_items():
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '').strip()
        category = request.args.get('category', '').strip()
        status = request.args.get('status', '').strip()
        
        # 构建查询
        query = Item.query
        
        # 关键词搜索
        if keyword:
            query = query.filter(Item.name.like(f'%{keyword}%') | Item.description.like(f'%{keyword}%'))
        
        # 类别筛选
        if category:
            query = query.filter_by(category=category)
        
        # 状态筛选
        if status == 'in_stock':
            query = query.filter(Item.in_stock > 0)
        elif status == 'out_of_stock':
            query = query.filter(Item.in_stock == 0)
        elif status == 'partial_in_stock':
            query = query.filter(Item.in_stock < Item.total, Item.in_stock > 0)
        
        # 执行查询
        items = query.all()
        
        # 构建响应数据
        result = []
        for item in items:
            result.append({
                'id': item.id,
                'name': item.name,
                'category': item.category,
                'total': item.total,
                'in_stock': item.in_stock,
                'description': item.description,
                'created_at': item.created_at.isoformat() if item.created_at else None,
                'updated_at': item.updated_at.isoformat() if item.updated_at else None
            })
        
        return jsonify({
            'code': 200,
            'data': result,
            'message': '获取物品列表成功'
        })
    except Exception as e:
        print(f'获取物品列表失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '获取物品列表失败'
        })

# 获取单个物品
@item_bp.route('/<int:item_id>', methods=['GET'])
def get_item(item_id):
    try:
        item = Item.query.get(item_id)
        if not item:
            return jsonify({
                'code': 404,
                'message': '物品不存在'
            })
        
        return jsonify({
            'code': 200,
            'data': {
                'id': item.id,
                'name': item.name,
                'category': item.category,
                'total': item.total,
                'in_stock': item.in_stock,
                'description': item.description,
                'created_at': item.created_at.isoformat() if item.created_at else None,
                'updated_at': item.updated_at.isoformat() if item.updated_at else None
            },
            'message': '获取物品信息成功'
        })
    except Exception as e:
        print(f'获取物品信息失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '获取物品信息失败'
        })

# 添加物品
@item_bp.route('/', methods=['POST'])
def add_item():
    try:
        data = request.json
        
        # 验证必填字段
        if not data.get('name'):
            return jsonify({
                'code': 400,
                'message': '物品名称不能为空'
            })
        
        # 验证库存数量
        total = data.get('total', 0)
        in_stock = data.get('in_stock', 0)
        
        if total < 0 or in_stock < 0:
            return jsonify({
                'code': 400,
                'message': '库存数量不能为负数'
            })
        
        if in_stock > total:
            return jsonify({
                'code': 400,
                'message': '当前库存不能大于总库存'
            })
        
        # 检查分类是否存在
        category = data.get('category', '未分类')
        existing_category = ItemCategory.query.filter_by(name=category).first()
        if not existing_category:
            # 创建新分类
            new_category = ItemCategory(name=category, description='自动创建的分类')
            db.session.add(new_category)
        
        # 创建物品
        item = Item(
            name=data['name'],
            category=category,
            total=total,
            in_stock=in_stock,
            description=data.get('description', '')
        )
        
        db.session.add(item)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'data': {
                'id': item.id,
                'name': item.name,
                'category': item.category,
                'total': item.total,
                'in_stock': item.in_stock,
                'description': item.description
            },
            'message': '添加物品成功'
        })
    except Exception as e:
        db.session.rollback()
        print(f'添加物品失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '添加物品失败'
        })

# 更新物品
@item_bp.route('/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    try:
        data = request.json
        item = Item.query.get(item_id)
        
        if not item:
            return jsonify({
                'code': 404,
                'message': '物品不存在'
            })
        
        # 更新物品信息
        if 'name' in data:
            item.name = data['name']
        
        if 'category' in data:
            category = data['category']
            # 检查分类是否存在
            existing_category = ItemCategory.query.filter_by(name=category).first()
            if not existing_category:
                # 创建新分类
                new_category = ItemCategory(name=category, description='自动创建的分类')
                db.session.add(new_category)
            item.category = category
        
        if 'total' in data:
            total = data['total']
            if total < 0:
                return jsonify({
                    'code': 400,
                    'message': '总库存不能为负数'
                })
            item.total = total
        
        if 'in_stock' in data:
            in_stock = data['in_stock']
            if in_stock < 0:
                return jsonify({
                    'code': 400,
                    'message': '当前库存不能为负数'
                })
            if in_stock > item.total:
                return jsonify({
                    'code': 400,
                    'message': '当前库存不能大于总库存'
                })
            item.in_stock = in_stock
        
        if 'description' in data:
            item.description = data['description']
        
        item.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'data': {
                'id': item.id,
                'name': item.name,
                'category': item.category,
                'total': item.total,
                'in_stock': item.in_stock,
                'description': item.description
            },
            'message': '更新物品成功'
        })
    except Exception as e:
        db.session.rollback()
        print(f'更新物品失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '更新物品失败'
        })

# 删除物品
@item_bp.route('/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    try:
        item = Item.query.get(item_id)
        if not item:
            return jsonify({
                'code': 404,
                'message': '物品不存在'
            })
        
        # 检查是否有相关的申请记录
        from ..models import Request
        active_requests = Request.query.filter_by(
            item_id=item_id,
            status='approved'
        ).count()
        
        if active_requests > 0:
            return jsonify({
                'code': 400,
                'message': '该物品还有未归还的申请记录，无法删除'
            })
        
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除物品成功'
        })
    except Exception as e:
        db.session.rollback()
        print(f'删除物品失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '删除物品失败'
        })

# 批量添加物品
@item_bp.route('/batch', methods=['POST'])
def batch_add_items():
    try:
        data = request.json
        items_data = data.get('items', [])
        
        if not items_data:
            return jsonify({
                'code': 400,
                'message': '请提供物品数据'
            })
        
        added_count = 0
        errors = []
        
        for idx, item_data in enumerate(items_data):
            try:
                # 验证必填字段
                if not item_data.get('name'):
                    errors.append(f'第{idx+1}项：物品名称不能为空')
                    continue
                
                # 验证库存数量
                total = item_data.get('total', 0)
                in_stock = item_data.get('in_stock', 0)
                
                if total < 0 or in_stock < 0:
                    errors.append(f'第{idx+1}项：库存数量不能为负数')
                    continue
                
                if in_stock > total:
                    errors.append(f'第{idx+1}项：当前库存不能大于总库存')
                    continue
                
                # 检查分类是否存在
                category = item_data.get('category', '未分类')
                existing_category = ItemCategory.query.filter_by(name=category).first()
                if not existing_category:
                    # 创建新分类
                    new_category = ItemCategory(name=category, description='自动创建的分类')
                    db.session.add(new_category)
                
                # 创建物品
                item = Item(
                    name=item_data['name'],
                    category=category,
                    total=total,
                    in_stock=in_stock,
                    description=item_data.get('description', '')
                )
                
                db.session.add(item)
                added_count += 1
                
            except Exception as e:
                errors.append(f'第{idx+1}项：添加失败 - {str(e)}')
        
        # 如果有成功添加的物品，提交事务
        if added_count > 0:
            db.session.commit()
        
        result = {
            'code': 200 if added_count > 0 else 400,
            'data': {
                'added_count': added_count,
                'total_items': len(items_data),
                'errors': errors if errors else []
            }
        }
        
        if added_count == len(items_data):
            result['message'] = f'成功添加全部 {added_count} 个物品'
        elif added_count > 0:
            result['message'] = f'部分添加成功，成功 {added_count} 个，失败 {len(errors)} 个'
        else:
            result['message'] = '全部添加失败'
        
        return jsonify(result)
    
    except Exception as e:
        db.session.rollback()
        print(f'批量添加物品失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '批量添加物品失败'
        })

# 获取分类列表
@item_bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = ItemCategory.query.all()
        
        # 计算每个分类下的物品数量
        result = []
        for category in categories:
            item_count = Item.query.filter_by(category=category.name).count()
            result.append({
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'item_count': item_count
            })
        
        return jsonify({
            'code': 200,
            'data': result,
            'message': '获取分类列表成功'
        })
    except Exception as e:
        print(f'获取分类列表失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '获取分类列表失败'
        })

# 添加分类
@item_bp.route('/categories', methods=['POST'])
def add_category():
    try:
        data = request.json
        
        # 验证必填字段
        if not data.get('name'):
            return jsonify({
                'code': 400,
                'message': '分类名称不能为空'
            })
        
        # 检查分类是否已存在
        existing_category = ItemCategory.query.filter_by(name=data['name']).first()
        if existing_category:
            return jsonify({
                'code': 400,
                'message': '分类已存在'
            })
        
        # 创建分类
        category = ItemCategory(
            name=data['name'],
            description=data.get('description', '')
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'data': {
                'id': category.id,
                'name': category.name,
                'description': category.description
            },
            'message': '添加分类成功'
        })
    except Exception as e:
        db.session.rollback()
        print(f'添加分类失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '添加分类失败'
        })

# 更新分类
@item_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    try:
        data = request.json
        category = ItemCategory.query.get(category_id)
        
        if not category:
            return jsonify({
                'code': 404,
                'message': '分类不存在'
            })
        
        # 检查新名称是否已被使用
        if 'name' in data and data['name'] != category.name:
            existing_category = ItemCategory.query.filter_by(name=data['name']).first()
            if existing_category:
                return jsonify({
                    'code': 400,
                    'message': '分类名称已存在'
                })
            
            # 更新所有相关物品的分类名称
            Item.query.filter_by(category=category.name).update({'category': data['name']})
            category.name = data['name']
        
        if 'description' in data:
            category.description = data['description']
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'data': {
                'id': category.id,
                'name': category.name,
                'description': category.description
            },
            'message': '更新分类成功'
        })
    except Exception as e:
        db.session.rollback()
        print(f'更新分类失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '更新分类失败'
        })

# 删除分类
@item_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    try:
        category = ItemCategory.query.get(category_id)
        
        if not category:
            return jsonify({
                'code': 404,
                'message': '分类不存在'
            })
        
        # 检查是否有物品使用该分类
        item_count = Item.query.filter_by(category=category.name).count()
        if item_count > 0:
            return jsonify({
                'code': 400,
                'message': f'该分类下还有 {item_count} 个物品，无法删除'
            })
        
        # 不能删除默认分类
        if category.name == '未分类':
            return jsonify({
                'code': 400,
                'message': '默认分类不能删除'
            })
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除分类成功'
        })
    except Exception as e:
        db.session.rollback()
        print(f'删除分类失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '删除分类失败'
        })

# 获取物品统计信息
@item_bp.route('/statistics', methods=['GET'])
def get_item_statistics():
    try:
        # 计算各种统计数据
        total_items = Item.query.count()
        total_quantity = db.session.query(db.func.sum(Item.total)).scalar() or 0
        available_quantity = db.session.query(db.func.sum(Item.in_stock)).scalar() or 0
        borrowed_quantity = total_quantity - available_quantity
        
        # 按分类统计
        category_stats = []
        categories = ItemCategory.query.all()
        for category in categories:
            items = Item.query.filter_by(category=category.name).all()
            category_total = sum(item.total for item in items)
            category_available = sum(item.in_stock for item in items)
            
            category_stats.append({
                'category': category.name,
                'item_count': len(items),
                'total_quantity': category_total,
                'available_quantity': category_available,
                'borrowed_quantity': category_total - category_available
            })
        
        return jsonify({
            'code': 200,
            'data': {
                'total_items': total_items,
                'total_quantity': total_quantity,
                'available_quantity': available_quantity,
                'borrowed_quantity': borrowed_quantity,
                'category_stats': category_stats
            },
            'message': '获取物品统计信息成功'
        })
    except Exception as e:
        print(f'获取物品统计信息失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '获取物品统计信息失败'
        })