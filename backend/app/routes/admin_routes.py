"""管理用户相关路由

这个模块包含所有与管理用户相关的API路由，包括：
1. 管理用户设置
2. 管理用户权限控制
3. 系统管理功能
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.enums import AdminPosition, AdminLevel, UserRole
from app.extensions import db
from datetime import datetime

# 创建蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/assign/<int:user_id>', methods=['POST'])
@jwt_required()
def assign_admin_role(user_id):
    """设置用户为管理员（超级管理员用）"""
    admin_id = get_jwt_identity()
    admin = User.query.get(admin_id)
    
    # 检查权限，只有超级管理员可以分配管理员角色
    if not admin or not admin.is_admin() or admin.admin_level != AdminLevel.super_admin:
        return jsonify({'success': False, 'message': '权限不足，只有超级管理员可以分配管理员角色'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    data = request.get_json()
    position_str = data.get('position')
    level_str = data.get('level')
    
    try:
        position = AdminPosition[position_str]
        level = AdminLevel[level_str]
    except (KeyError, TypeError):
        return jsonify({'success': False, 'message': '无效的管理岗位或级别'}), 400
    
    # 设置管理员角色
    success, message = user.set_admin_position(position, level)
    
    if success:
        db.session.commit()
        return jsonify({'success': True, 'message': message}), 200
    else:
        return jsonify({'success': False, 'message': message}), 400

@admin_bp.route('/permissions/<int:user_id>', methods=['POST'])
@jwt_required()
def set_admin_permissions(user_id):
    """设置管理员权限（超级管理员用）"""
    admin_id = get_jwt_identity()
    admin = User.query.get(admin_id)
    
    # 检查权限
    if not admin or not admin.is_admin() or admin.admin_level != AdminLevel.super_admin:
        return jsonify({'success': False, 'message': '权限不足，只有超级管理员可以设置权限'}), 403
    
    user = User.query.get(user_id)
    if not user or not user.is_admin():
        return jsonify({'success': False, 'message': '用户不存在或不是管理员'}), 404
    
    data = request.get_json()
    permissions = data.get('permissions', {})
    
    # 设置权限
    user.admin_permissions = permissions
    db.session.commit()
    
    return jsonify({'success': True, 'message': '管理员权限设置成功'}), 200

@admin_bp.route('/revoke/<int:user_id>', methods=['POST'])
@jwt_required()
def revoke_admin_role(user_id):
    """撤销管理员角色（超级管理员用）"""
    admin_id = get_jwt_identity()
    admin = User.query.get(admin_id)
    
    # 检查权限
    if not admin or not admin.is_admin() or admin.admin_level != AdminLevel.super_admin:
        return jsonify({'success': False, 'message': '权限不足，只有超级管理员可以撤销管理员角色'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    if not user.is_admin():
        return jsonify({'success': False, 'message': '该用户不是管理员'}), 400
    
    # 撤销管理员角色
    user.remove_role(UserRole.admin)
    user.admin_position = None
    user.admin_level = None
    user.admin_permissions = {}
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': '已撤销管理员角色'}), 200

@admin_bp.route('/list', methods=['GET'])
@jwt_required()
def list_admins():
    """获取所有管理员列表（管理员用）"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.is_admin():
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 查询所有管理员
    admins = User.query.filter(
        User.roles.any(UserRole.admin)
    ).all()
    
    result = []
    for admin in admins:
        result.append({
            'user_id': admin.id,
            'username': admin.username,
            'email': admin.email,
            'display_name': admin.display_name,
            'position': admin.admin_position.value if admin.admin_position else None,
            'level': admin.admin_level.value if admin.admin_level else None,
            'permissions': admin.admin_permissions
        })
    
    return jsonify({'success': True, 'admins': result}), 200

@admin_bp.route('/status', methods=['GET'])
@jwt_required()
def get_admin_status():
    """获取当前用户的管理员状态"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    result = {
        'is_admin': user.is_admin(),
        'position': user.admin_position.value if user.admin_position else None,
        'level': user.admin_level.value if user.admin_level else None,
        'permissions': user.admin_permissions
    }
    
    return jsonify({'success': True, 'admin_status': result}), 200

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def admin_dashboard():
    """获取管理员仪表盘数据"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.is_admin():
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 获取系统统计数据
    total_users = User.query.count()
    vip_users = User.query.filter(User.vip_level != 'free').count()
    promoters = User.query.filter(
        User.roles.any(UserRole.promoter),
        User.promoter_approved == True
    ).count()
    
    # 根据管理员岗位提供不同的数据
    position_data = {}
    if user.admin_position == AdminPosition.marketing:
        # 市场部门数据
        position_data = {
            'new_users_today': 0,  # 示例数据
            'conversion_rate': 0.0,
            'marketing_campaigns': []
        }
    elif user.admin_position == AdminPosition.operations:
        # 运营部门数据
        position_data = {
            'active_users': 0,  # 示例数据
            'retention_rate': 0.0,
            'feature_usage': {}
        }
    elif user.admin_position == AdminPosition.customer_service:
        # 客服部门数据
        position_data = {
            'open_tickets': 0,  # 示例数据
            'avg_response_time': 0.0,
            'satisfaction_rate': 0.0
        }
    elif user.admin_position == AdminPosition.technical:
        # 技术部门数据
        position_data = {
            'system_status': 'normal',  # 示例数据
            'api_usage': {},
            'error_rates': {}
        }
    
    dashboard_data = {
        'total_users': total_users,
        'vip_users': vip_users,
        'promoters': promoters,
        'position_data': position_data
    }
    
    return jsonify({'success': True, 'dashboard': dashboard_data}), 200
