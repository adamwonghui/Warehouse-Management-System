from flask import Blueprint, request, jsonify
from datetime import datetime
from ..app import db
from ..models import Item, Request, ItemCategory

admin_bp = Blueprint('admin', __name__)

# 获取系统统计信息
@admin_bp.route('/statistics', methods=['GET'])
def get_statistics():
    try:
        # 统计物品数量
        total_items = Item.query.count()
        
        # 统计总库存和当前库存
        all_items = Item.query.all()
        total_stock = sum(item.total for item in all_items)
        current_stock = sum(item.in_stock for item in all_items)
        
        # 统计各类请求数量
        pending_requests = Request.query.filter_by(status='pending').count()
        approved_requests = Request.query.filter_by(status='approved').count()
        rejected_requests = Request.query.filter_by(status='rejected').count()
        returned_requests = Request.query.filter_by(status='returned').count()
        partial_requests = Request.query.filter_by(status='partially_returned').count()
        
        # 获取最近7天的请求趋势
        from datetime import datetime, timedelta
        today = datetime.utcnow()
        weekly_trend = []
        
        for i in range(7):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            count = Request.query.filter(Request.created_at >= day_start, Request.created_at <= day_end).count()
            weekly_trend.append({
                'date': date_str,
                'count': count
            })
        
        # 按类别统计物品数量
        category_stats = []
        categories = ItemCategory.query.all()
        for category in categories:
            item_count = Item.query.filter_by(category=category.name).count()
            category_stats.append({
                'name': category.name,
                'count': item_count
            })
        
        return jsonify({
            'code': 200,
            'data': {
                'total_items': total_items,
                'total_stock': total_stock,
                'current_stock': current_stock,
                'request_stats': {
                    'pending': pending_requests,
                    'approved': approved_requests,
                    'rejected': rejected_requests,
                    'returned': returned_requests,
                    'partially_returned': partial_requests
                },
                'weekly_trend': weekly_trend,
                'category_stats': category_stats
            },
            'message': '获取统计信息成功'
        })
    except Exception as e:
        print(f'获取统计信息失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '获取统计信息失败'
        })

# 批量更新物品信息
@admin_bp.route('/items/batch_update', methods=['POST'])
def batch_update_items():
    try:
        data = request.json
        items_to_update = data.get('items', [])
        
        if not items_to_update:
            return jsonify({
                'code': 400,
                'message': '请提供要更新的物品信息'
            })
        
        updated_count = 0
        for item_data in items_to_update:
            item_id = item_data.get('id')
            if not item_id:
                continue
            
            item = Item.query.get(item_id)
            if item:
                # 更新物品信息
                if 'name' in item_data:
                    item.name = item_data['name']
                if 'category' in item_data:
                    # 确保分类存在
                    category = ItemCategory.query.filter_by(name=item_data['category']).first()
                    if not category:
                        category = ItemCategory(name=item_data['category'], description='自动创建的分类')
                        db.session.add(category)
                    item.category = item_data['category']
                if 'total' in item_data:
                    item.total = int(item_data['total'])
                if 'in_stock' in item_data:
                    item.in_stock = int(item_data['in_stock'])
                if 'description' in item_data:
                    item.description = item_data['description']
                
                item.updated_at = datetime.utcnow()
                updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'data': {
                'updated_count': updated_count
            },
            'message': f'成功更新 {updated_count} 个物品'
        })
    except Exception as e:
        db.session.rollback()
        print(f'批量更新物品失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '批量更新物品失败'
        })

# 批量删除物品
@admin_bp.route('/items/batch_delete', methods=['POST'])
def batch_delete_items():
    try:
        data = request.json
        item_ids = data.get('ids', [])
        
        if not item_ids:
            return jsonify({
                'code': 400,
                'message': '请提供要删除的物品ID'
            })
        
        # 检查是否有未归还的物品
        for item_id in item_ids:
            pending_requests = Request.query.filter_by(
                item_id=item_id,
                status='approved'
            ).count()
            
            if pending_requests > 0:
                return jsonify({
                    'code': 400,
                    'message': f'ID为 {item_id} 的物品还有未归还的申请，无法删除'
                })
        
        # 执行删除
        deleted_count = Item.query.filter(Item.id.in_(item_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'data': {
                'deleted_count': deleted_count
            },
            'message': f'成功删除 {deleted_count} 个物品'
        })
    except Exception as e:
        db.session.rollback()
        print(f'批量删除物品失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '批量删除物品失败'
        })

# 批量处理请求
@admin_bp.route('/requests/batch_process', methods=['POST'])
def batch_process_requests():
    try:
        data = request.json
        request_ids = data.get('ids', [])
        action = data.get('action')  # approve 或 reject
        approver = data.get('approver', 'admin')
        comment = data.get('comment', '')
        
        if not request_ids or action not in ['approve', 'reject']:
            return jsonify({
                'code': 400,
                'message': '请提供有效的请求ID和操作类型'
            })
        
        processed_count = 0
        for request_id in request_ids:
            req = Request.query.get(request_id)
            if req and req.status == 'pending':
                if action == 'approve':
                    # 检查库存
                    item = Item.query.get(req.item_id)
                    if item and item.in_stock >= req.quantity:
                        # 批准请求
                        req.status = 'approved'
                        req.approver = approver
                        req.approved_at = datetime.utcnow()
                        req.comment = comment
                        
                        # 减少库存
                        item.in_stock -= req.quantity
                        item.updated_at = datetime.utcnow()
                        
                        processed_count += 1
                elif action == 'reject':
                    # 拒绝请求
                    req.status = 'rejected'
                    req.approver = approver
                    req.approved_at = datetime.utcnow()
                    req.comment = comment
                    
                    processed_count += 1
        
        db.session.commit()
        
        action_text = '批准' if action == 'approve' else '拒绝'
        return jsonify({
            'code': 200,
            'data': {
                'processed_count': processed_count
            },
            'message': f'成功{action_text} {processed_count} 个请求'
        })
    except Exception as e:
        db.session.rollback()
        print(f'批量处理请求失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '批量处理请求失败'
        })

# 获取系统日志
@admin_bp.route('/logs', methods=['GET'])
def get_logs():
    try:
        # 这里可以实现更复杂的日志记录和查询功能
        # 目前返回一个示例
        logs = [
            {
                'timestamp': datetime.utcnow().isoformat(),
                'level': 'INFO',
                'message': '系统启动成功',
                'user': 'system'
            }
        ]
        
        return jsonify({
            'code': 200,
            'data': {
                'logs': logs
            },
            'message': '获取日志成功'
        })
    except Exception as e:
        print(f'获取日志失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '获取日志失败'
        })

# 系统设置
@admin_bp.route('/settings', methods=['GET', 'PUT'])
def system_settings():
    try:
        if request.method == 'GET':
            # 返回当前设置
            settings = {
                'system_name': '仓库管理系统',
                'auto_approve': False,
                'max_borrow_days': 7,
                'notification_enabled': True
            }
            
            return jsonify({
                'code': 200,
                'data': settings,
                'message': '获取系统设置成功'
            })
        
        elif request.method == 'PUT':
            # 更新系统设置
            data = request.json
            # 这里可以实现设置的保存逻辑
            
            return jsonify({
                'code': 200,
                'message': '更新系统设置成功'
            })
    except Exception as e:
        print(f'系统设置操作失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '系统设置操作失败'
        })

# 导出系统数据
@admin_bp.route('/export_data', methods=['GET'])
def export_data():
    try:
        export_type = request.args.get('type', 'all')
        
        data = {
            'export_type': export_type,
            'export_time': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }
        
        if export_type in ['all', 'items']:
            items = Item.query.all()
            data['items'] = [
                {
                    'id': item.id,
                    'name': item.name,
                    'category': item.category,
                    'total': item.total,
                    'in_stock': item.in_stock,
                    'description': item.description,
                    'created_at': item.created_at.isoformat() if item.created_at else None,
                    'updated_at': item.updated_at.isoformat() if item.updated_at else None
                }
                for item in items
            ]
        
        if export_type in ['all', 'requests']:
            requests = Request.query.all()
            data['requests'] = [
                {
                    'id': req.id,
                    'username': req.username,
                    'item_id': req.item_id,
                    'item_name': req.item_name,
                    'item_category': req.item_category,
                    'quantity': req.quantity,
                    'purpose': req.purpose,
                    'status': req.status,
                    'created_at': req.created_at.isoformat() if req.created_at else None,
                    'approved_at': req.approved_at.isoformat() if req.approved_at else None,
                    'approver': req.approver,
                    'comment': req.comment,
                    'returned_quantity': req.returned_quantity,
                    'returned_at': req.returned_at.isoformat() if req.returned_at else None
                }
                for req in requests
            ]
        
        if export_type in ['all', 'categories']:
            categories = ItemCategory.query.all()
            data['categories'] = [
                {
                    'id': cat.id,
                    'name': cat.name,
                    'description': cat.description
                }
                for cat in categories
            ]
        
        return jsonify({
            'code': 200,
            'data': data,
            'message': '导出数据成功'
        })
    except Exception as e:
        print(f'导出数据失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': '导出数据失败'
        })