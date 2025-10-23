from flask import Blueprint, request, jsonify
from models.db import db, Request, Item
import logging
from datetime import datetime

requests_bp = Blueprint('requests', __name__)
logger = logging.getLogger(__name__)

@requests_bp.route('/', methods=['GET'])
def get_requests():
    try:
        # 获取查询参数
        username = request.args.get('username')
        status = request.args.get('status')
        
        # 构建查询
        query = Request.query
        
        if username:
            query = query.filter(Request.username == username)
        if status:
            query = query.filter(Request.status == status)
        
        # 按时间倒序排列
        requests = query.order_by(Request.created_at.desc()).all()
        
        # 转换为JSON格式
        result = []
        for req in requests:
            result.append({
                'id': req.id,
                'username': req.username,
                'item_id': req.item_id,
                'item_name': req.item.name if req.item else '',
                'item_category': req.item.category if req.item else '',
                'quantity': req.quantity,
                'purpose': req.purpose,
                'status': req.status,
                'created_at': req.created_at,
                'approved_at': req.approved_at,
                'approver': req.approver,
                'comment': req.comment
            })
        
        return jsonify({
            'code': 200,
            'message': '获取申请列表成功',
            'data': result
        })
    except Exception as e:
        logger.error(f'获取申请列表错误: {str(e)}')
        return jsonify({'code': 500, 'message': '获取申请列表失败'}), 500

@requests_bp.route('/', methods=['POST'])
def create_request():
    try:
        data = request.json
        
        # 检查物品是否存在
        item = Item.query.get_or_404(data.get('item_id'))
        
        # 检查库存是否足够
        if item.in_stock < data.get('quantity'):
            return jsonify({'code': 400, 'message': '库存不足'}), 400
        
        # 创建新申请
        new_request = Request(
            username=data.get('username'),
            item_id=data.get('item_id'),
            quantity=data.get('quantity'),
            purpose=data.get('purpose'),
            status='pending'
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        logger.info(f'创建申请成功: 用户 {new_request.username} 申请 {item.name}')
        return jsonify({
            'code': 200,
            'message': '申请创建成功',
            'data': {
                'id': new_request.id
            }
        })
    except Exception as e:
        logger.error(f'创建申请错误: {str(e)}')
        db.session.rollback()
        return jsonify({'code': 500, 'message': '申请创建失败'}), 500

@requests_bp.route('/<int:request_id>/approve', methods=['PUT'])
def approve_request(request_id):
    try:
        data = request.json
        req = Request.query.get_or_404(request_id)
        
        # 检查申请状态
        if req.status != 'pending':
            return jsonify({'code': 400, 'message': '该申请已处理'}), 400
        
        # 获取物品
        item = Item.query.get_or_404(req.item_id)
        
        # 检查库存是否足够
        if item.in_stock < req.quantity:
            return jsonify({'code': 400, 'message': '库存不足'}), 400
        
        # 更新申请状态
        req.status = 'approved'
        req.approved_at = datetime.now()
        req.approver = data.get('approver')
        req.comment = data.get('comment')
        
        # 更新物品库存
        item.in_stock -= req.quantity
        item.on_loan += req.quantity
        item.user = req.username
        
        if item.in_stock == 0:
            item.status = 'out_of_stock'
        else:
            item.status = 'partial_in_stock'
        
        db.session.commit()
        
        logger.info(f'审批通过申请: ID {req.id}')
        return jsonify({
            'code': 200,
            'message': '审批通过成功'
        })
    except Exception as e:
        logger.error(f'审批申请错误: {str(e)}')
        db.session.rollback()
        return jsonify({'code': 500, 'message': '审批失败'}), 500

@requests_bp.route('/<int:request_id>/reject', methods=['PUT'])
def reject_request(request_id):
    try:
        data = request.json
        req = Request.query.get_or_404(request_id)
        
        # 检查申请状态
        if req.status != 'pending':
            return jsonify({'code': 400, 'message': '该申请已处理'}), 400
        
        # 更新申请状态
        req.status = 'rejected'
        req.approved_at = datetime.now()
        req.approver = data.get('approver')
        req.comment = data.get('comment')
        
        db.session.commit()
        
        logger.info(f'拒绝申请: ID {req.id}')
        return jsonify({
            'code': 200,
            'message': '拒绝申请成功'
        })
    except Exception as e:
        logger.error(f'拒绝申请错误: {str(e)}')
        db.session.rollback()
        return jsonify({'code': 500, 'message': '拒绝申请失败'}), 500

@requests_bp.route('/<int:request_id>/return', methods=['PUT'])
def return_item(request_id):
    try:
        data = request.json
        req = Request.query.get_or_404(request_id)
        
        # 检查申请状态
        if req.status != 'approved':
            return jsonify({'code': 400, 'message': '只有已批准的申请才能归还'}), 400
        
        # 获取物品
        item = Item.query.get_or_404(req.item_id)
        
        # 计算归还数量
        return_quantity = data.get('quantity', req.quantity)
        if return_quantity > req.quantity:
            return jsonify({'code': 400, 'message': '归还数量不能大于申请数量'}), 400
        
        # 更新物品库存
        item.in_stock += return_quantity
        item.on_loan -= return_quantity
        
        # 更新物品状态
        if item.on_loan == 0:
            item.status = 'in_stock'
            item.user = None
        else:
            item.status = 'partial_in_stock'
        
        # 更新申请状态
        if return_quantity == req.quantity:
            req.status = 'returned'
        else:
            req.status = 'partially_returned'
            req.quantity -= return_quantity
        
        db.session.commit()
        
        logger.info(f'归还物品: ID {req.id}')
        return jsonify({
            'code': 200,
            'message': '归还成功'
        })
    except Exception as e:
        logger.error(f'归还物品错误: {str(e)}')
        db.session.rollback()
        return jsonify({'code': 500, 'message': '归还失败'}), 500