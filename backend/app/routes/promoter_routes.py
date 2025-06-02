"""推广用户相关路由

这个模块包含所有与推广用户相关的API路由，包括：
1. 推广用户申请
2. 推广用户审核
3. 推广用户数据统计
4. 推广佣金查询和提现
"""

from flask import Blueprint, request, jsonify, current_app, redirect
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.enums import PromoterType, UserRole
from app.models.promotion import PromoterLink, ClickRecord, ConversionRecord, CommissionRecord, WithdrawalRecord
from app.extensions import db
from datetime import datetime
import uuid
import random
import string

# 创建蓝图
promoter_bp = Blueprint('promoter', __name__, url_prefix='/api/promoter')

# 推广链接追踪路由（无需认证）
@promoter_bp.route('/r/<code>', methods=['GET'])
def redirect_promoter_link(code):
    """推广链接重定向"""
    # 查找推广链接
    link = PromoterLink.query.filter_by(code=code, is_active=True).first()
    
    if not link:
        return jsonify({'success': False, 'message': '无效的推广链接'}), 404
    
    # 记录点击
    click = ClickRecord(
        link_id=link.id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        referer=request.referrer
    )
    
    # 增加点击次数
    link.clicks += 1
    
    db.session.add(click)
    db.session.commit()
    
    # 重定向到注册页面，带上推广码
    return redirect(f"/register?ref={code}")

@promoter_bp.route('/links', methods=['GET'])
@jwt_required()
def get_promoter_links():
    """获取推广用户的推广链接列表"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    if not user.is_promoter():
        return jsonify({'success': False, 'message': '您不是推广用户'}), 403
    
    # 获取用户的推广链接
    links = PromoterLink.query.filter_by(user_id=user_id).all()
    
    result = [link.to_dict() for link in links]
    
    # 如果用户没有推广链接，自动创建一个通用链接
    if not result:
        # 创建通用推广链接
        code = f"RC{user_id}{generate_random_string(6)}"
        link = PromoterLink(
            user_id=user_id,
            name="通用推广链接",
            code=code
        )
        db.session.add(link)
        db.session.commit()
        
        result = [link.to_dict()]
    
    return jsonify({'success': True, 'links': result}), 200

@promoter_bp.route('/links', methods=['POST'])
@jwt_required()
def create_promoter_link():
    """创建新的推广链接"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    if not user.is_promoter():
        return jsonify({'success': False, 'message': '您不是推广用户'}), 403
    
    data = request.get_json()
    name = data.get('name', '推广链接')
    
    # 生成唯一的推广码
    code = f"RC{user_id}{generate_random_string(6)}"
    
    # 创建推广链接
    link = PromoterLink(
        user_id=user_id,
        name=name,
        code=code
    )
    
    db.session.add(link)
    db.session.commit()
    
    return jsonify({'success': True, 'link': link.to_dict()}), 201

@promoter_bp.route('/links/<int:link_id>', methods=['PUT'])
@jwt_required()
def update_promoter_link(link_id):
    """更新推广链接"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    if not user.is_promoter():
        return jsonify({'success': False, 'message': '您不是推广用户'}), 403
    
    # 查找推广链接
    link = PromoterLink.query.filter_by(id=link_id, user_id=user_id).first()
    
    if not link:
        return jsonify({'success': False, 'message': '推广链接不存在或不属于您'}), 404
    
    data = request.get_json()
    name = data.get('name')
    is_active = data.get('is_active')
    
    if name is not None:
        link.name = name
    
    if is_active is not None:
        link.is_active = is_active
    
    db.session.commit()
    
    return jsonify({'success': True, 'link': link.to_dict()}), 200

@promoter_bp.route('/links/<int:link_id>', methods=['DELETE'])
@jwt_required()
def delete_promoter_link(link_id):
    """删除推广链接"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    if not user.is_promoter():
        return jsonify({'success': False, 'message': '您不是推广用户'}), 403
    
    # 查找推广链接
    link = PromoterLink.query.filter_by(id=link_id, user_id=user_id).first()
    
    if not link:
        return jsonify({'success': False, 'message': '推广链接不存在或不属于您'}), 404
    
    # 不真正删除，只是设置为非活动状态
    link.is_active = False
    db.session.commit()
    
    return jsonify({'success': True, 'message': '推广链接已删除'}), 200

@promoter_bp.route('/commissions', methods=['GET'])
@jwt_required()
def get_commissions():
    """获取佣金记录"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    if not user.is_promoter():
        return jsonify({'success': False, 'message': '您不是推广用户'}), 403
    
    # 获取佣金记录
    commissions = CommissionRecord.query.filter_by(user_id=user_id).order_by(CommissionRecord.created_at.desc()).all()
    
    result = [comm.to_dict() for comm in commissions]
    
    return jsonify({'success': True, 'commissions': result}), 200

@promoter_bp.route('/withdrawals', methods=['GET'])
@jwt_required()
def get_withdrawals():
    """获取提现记录"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    if not user.is_promoter():
        return jsonify({'success': False, 'message': '您不是推广用户'}), 403
    
    # 获取提现记录
    withdrawals = WithdrawalRecord.query.filter_by(user_id=user_id).order_by(WithdrawalRecord.created_at.desc()).all()
    
    result = [withdrawal.to_dict() for withdrawal in withdrawals]
    
    return jsonify({'success': True, 'withdrawals': result}), 200

# 辅助函数
def generate_random_string(length):
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@promoter_bp.route('/apply', methods=['POST'])
@jwt_required()
def apply_for_promoter():
    """申请成为推广用户"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    # 检查是否已经是推广用户
    if user.is_promoter():
        return jsonify({'success': False, 'message': '您已经是推广用户'}), 400
    
    # 检查是否已经提交过申请
    if user.promoter_type is not None and not user.promoter_approved:
        return jsonify({'success': False, 'message': '您已提交申请，请等待审核'}), 400
    
    # 检查是否为VIP用户
    if not user.is_vip():
        return jsonify({'success': False, 'message': '只有VIP用户才能申请成为推广用户'}), 400
    
    # 获取申请类型
    data = request.get_json()
    promoter_type_str = data.get('promoter_type')
    
    try:
        promoter_type = PromoterType[promoter_type_str]
    except (KeyError, TypeError):
        return jsonify({'success': False, 'message': '无效的推广用户类型'}), 400
    
    # 提交申请
    success, message = user.apply_for_promoter(promoter_type)
    
    if success:
        db.session.commit()
        return jsonify({'success': True, 'message': message}), 200
    else:
        return jsonify({'success': False, 'message': message}), 400

@promoter_bp.route('/applications', methods=['GET'])
@jwt_required()
def get_promoter_applications():
    """获取推广用户申请列表（管理员用）"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.is_admin():
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 获取所有待审核的申请
    applications = User.query.filter(
        User.promoter_type.isnot(None),
        User.promoter_approved == False,
        User.promoter_application_date.isnot(None)
    ).all()
    
    result = []
    for app in applications:
        result.append({
            'user_id': app.id,
            'username': app.username,
            'email': app.email,
            'display_name': app.display_name,
            'vip_level': app.vip_level.value if app.vip_level else None,
            'promoter_type': app.promoter_type.value if app.promoter_type else None,
            'application_date': app.promoter_application_date.isoformat() if app.promoter_application_date else None
        })
    
    return jsonify({'success': True, 'applications': result}), 200

@promoter_bp.route('/approve/<int:user_id>', methods=['POST'])
@jwt_required()
def approve_promoter(user_id):
    """审核通过推广用户申请（管理员用）"""
    admin_id = get_jwt_identity()
    admin = User.query.get(admin_id)
    
    if not admin or not admin.is_admin():
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    # 检查是否有待审核的申请
    if user.promoter_type is None or user.promoter_approved:
        return jsonify({'success': False, 'message': '该用户没有待审核的推广申请'}), 400
    
    # 获取佣金比例
    data = request.get_json()
    commission_rate = data.get('commission_rate', 0.1)  # 默认10%
    
    # 审核通过
    success, message = user.approve_promoter(commission_rate)
    
    if success:
        db.session.commit()
        return jsonify({'success': True, 'message': message}), 200
    else:
        return jsonify({'success': False, 'message': message}), 400

@promoter_bp.route('/reject/<int:user_id>', methods=['POST'])
@jwt_required()
def reject_promoter(user_id):
    """拒绝推广用户申请（管理员用）"""
    admin_id = get_jwt_identity()
    admin = User.query.get(admin_id)
    
    if not admin or not admin.is_admin():
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    # 检查是否有待审核的申请
    if user.promoter_type is None or user.promoter_approved:
        return jsonify({'success': False, 'message': '该用户没有待审核的推广申请'}), 400
    
    # 拒绝申请
    success, message = user.reject_promoter()
    
    if success:
        db.session.commit()
        return jsonify({'success': True, 'message': message}), 200
    else:
        return jsonify({'success': False, 'message': message}), 400

@promoter_bp.route('/status', methods=['GET'])
@jwt_required()
def get_promoter_status():
    """获取当前用户的推广状态"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    result = {
        'is_promoter': user.is_promoter(),
        'promoter_type': user.promoter_type.value if user.promoter_type else None,
        'promoter_approved': user.promoter_approved,
        'application_date': user.promoter_application_date.isoformat() if user.promoter_application_date else None,
        'approval_date': user.promoter_approval_date.isoformat() if user.promoter_approval_date else None,
        'commission_rate': user.promoter_commission_rate,
        'total_earnings': user.promoter_total_earnings,
        'available_balance': user.promoter_available_balance
    }
    
    return jsonify({'success': True, 'promoter_status': result}), 200

@promoter_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_promoter_stats():
    """获取推广数据统计"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    if not user.is_promoter():
        return jsonify({'success': False, 'message': '您不是推广用户'}), 403
    
    # 获取用户的推广链接
    links = PromoterLink.query.filter_by(user_id=user_id).all()
    
    # 计算总点击、注册和转化数
    total_clicks = sum(link.clicks for link in links)
    total_registrations = sum(link.registrations for link in links)
    total_conversions = sum(link.conversions for link in links)
    
    # 获取本月佣金
    current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_commissions = CommissionRecord.query.filter(
        CommissionRecord.user_id == user_id,
        CommissionRecord.created_at >= current_month,
        CommissionRecord.status != 'cancelled'
    ).all()
    earnings_this_month = sum(comm.amount for comm in month_commissions)
    
    stats = {
        'clicks': total_clicks,
        'registrations': total_registrations,
        'conversions': total_conversions,
        'earnings_this_month': earnings_this_month,
        'earnings_total': user.promoter_total_earnings
    }
    
    return jsonify({'success': True, 'stats': stats}), 200

@promoter_bp.route('/withdraw', methods=['POST'])
@jwt_required()
def withdraw_earnings():
    """申请提现佣金"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    if not user.is_promoter():
        return jsonify({'success': False, 'message': '您不是推广用户'}), 403
    
    data = request.get_json()
    amount = data.get('amount', 0)
    payment_method = data.get('payment_method', 'bank_transfer')
    payment_account = data.get('payment_account', '')
    
    if amount <= 0:
        return jsonify({'success': False, 'message': '提现金额必须大于0'}), 400
    
    if amount > user.promoter_available_balance:
        return jsonify({'success': False, 'message': '可提现余额不足'}), 400
    
    # 创建提现记录
    withdrawal = WithdrawalRecord(
        user_id=user_id,
        amount=amount,
        status='pending',
        payment_method=payment_method,
        payment_account=payment_account
    )
    
    # 减少可提现余额
    user.promoter_available_balance -= amount
    
    db.session.add(withdrawal)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': '提现申请已提交，请等待处理',
        'withdrawal_id': withdrawal.id,
        'remaining_balance': user.promoter_available_balance
    }), 200
