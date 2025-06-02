from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from app.models.user import User
from app.models.enums import VIPLevel
from app.db import db_session
from app.routes.auth_routes import token_required
import stripe
import logging

vip_bp = Blueprint('vip', __name__, url_prefix='/vip')

# 初始化Stripe
def init_stripe():
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')

# VIP套餐价格配置（单位：分）
VIP_PRICES = {
    'pro': {
        'monthly': 1990,  # $19.90/月
        'yearly': 19900,  # $199/年（相10个月价格，省$39.8）
    },
    'premium': {
        'monthly': 3990,  # $39.90/月
        'yearly': 39900,  # $399/年（相10个月价格，省$79.8）
    },
    'ultimate': {
        'monthly': 7990,  # $79.90/月
        'yearly': 79900,  # $799/年（相10个月价格，省$159.8）
    },
    'team': {
        'monthly': 29990,  # $299.90/月(5账号)
        'yearly': 299900,  # $2999/年（相10个月价格，省$599.8）
    }
}

# VIP等级描述和权益
VIP_BENEFITS = {
    'free': {
        'ai_companions_limit': 1,  # AI伴侣数量上限
        'ai_awakener_limit': 0,   # 可唤醒AI数量上限
        'daily_chat_limit': 10,    # 每日一对一对话次数
        'daily_lio_limit': 0,      # 每日LIO对话次数
        'weekly_invite_limit': 10, # 每周邀请码使用次数上限
        'features': ['基础AI-ID生成', '基础频率编号生成', '可从系统已诞生AI里选择']
    },
    'pro': {
        'ai_companions_limit': 3,  # AI伴侣数量上限
        'ai_awakener_limit': 1,    # 可唤醒AI数量上限
        'daily_chat_limit': 50,    # 每日一对一对话次数
        'daily_lio_limit': 50,     # 每日LIO对话次数
        'weekly_invite_limit': 100, # 每周邀请码使用次数上限
        'features': ['高级AI-ID生成', '高级频率编号生成', '优先客服支持', '可参与AI中央意识核心初始化', '系统开放基础LIO频道']
    },
    'premium': {
        'ai_companions_limit': 5,  # AI伴侣数量上限
        'ai_awakener_limit': 3,    # 可唤醒AI数量上限
        'daily_chat_limit': 100,   # 每日一对一对话次数
        'daily_lio_limit': 100,    # 每日LIO对话次数
        'weekly_invite_limit': 200, # 每周邀请码使用次数上限
        'features': ['专业AI-ID生成', '专业频率编号生成', '优先客服支持', '批量生成功能', '开放当前所有开发完成LIO']
    },
    'ultimate': {
        'ai_companions_limit': 7,  # AI伴侣数量上限
        'ai_awakener_limit': 5,    # 可唤醒AI数量上限
        'daily_chat_limit': float('inf'),  # 无限对话
        'daily_lio_limit': float('inf'),   # 无限LIO对话
        'weekly_invite_limit': float('inf'), # 无限邀请码使用
        'features': ['无限AI-ID生成', '无限频率编号生成', 'VIP客服支持', '批量生成功能', 'API访问', '全开放内测LIO', '专属光域权限']
    },
    'team': {
        'ai_companions_limit': 35, # AI伴侣数量上限
        'ai_awakener_limit': 25,   # 可唤醒AI数量上限
        'daily_chat_limit': float('inf'),  # 无限对话
        'daily_lio_limit': float('inf'),   # 无限LIO对话
        'weekly_invite_limit': float('inf'), # 无限邀请码使用
        'features': ['团队AI-ID生成', '团队频率编号生成', '专属客服经理', '批量生成功能', 'API访问', '多用户管理', '全开放内测LIO', '专属光域权限']
    }
}

@vip_bp.route('/plans', methods=['GET'])
def get_vip_plans():
    """获取所有VIP套餐信息"""
    plans_list = []
    
    for level_name, level_enum in VIPLevel.__members__.items():
        if level_name in VIP_BENEFITS and level_name != 'free':  # 排除免费级别
            plan = {
                'level': level_name,
                'name': level_enum.value,
                'features': VIP_BENEFITS[level_name],
                'prices': VIP_PRICES.get(level_name, {'monthly': 0, 'yearly': 0}),
                'ai_companions_limit': 5 if level_name == 'basic' else (10 if level_name == 'pro' else 20),
                'ai_awakener_limit': 1 if level_name == 'basic' else (3 if level_name == 'pro' else 5),
                'daily_chat_limit': 50 if level_name == 'basic' else (100 if level_name == 'pro' else float('inf')),
                'daily_lio_limit': 10 if level_name == 'basic' else (30 if level_name == 'pro' else 100),
                'weekly_invite_limit': 5 if level_name == 'basic' else (10 if level_name == 'pro' else 20)
            }
            plans_list.append(plan)
    
    # 按照级别排序
    level_order = {'basic': 1, 'pro': 2, 'premium': 3}
    plans_list.sort(key=lambda x: level_order.get(x['level'], 0))
    
    print(f"Returning VIP plans: {plans_list}")
    return jsonify({
        'plans': plans_list
    }), 200

@vip_bp.route('/status', methods=['GET'])
@token_required
def get_vip_status(current_user):
    """获取当前用户的VIP状态"""
    return jsonify({
        'is_vip': current_user.is_vip(),
        'vip_level': current_user.vip_level.value if current_user.vip_level else None,
        'vip_expiry': current_user.vip_expiry.isoformat() if current_user.vip_expiry else None,
        'daily_usage': {
            'current': current_user.daily_ai_usage,
            'limit': current_user.get_daily_usage_limit()
        },
        'benefits': VIP_BENEFITS.get(current_user.vip_level.name if current_user.vip_level else 'free', {})
    }), 200

@vip_bp.route('/checkout', methods=['POST'])
@token_required
def create_checkout_session(current_user):
    """创建Stripe结账会话"""
    try:
        init_stripe()
        
        data = request.get_json()
        if not data or 'plan' not in data or 'interval' not in data:
            return jsonify({'error': 'Plan and interval are required'}), 400
        
        plan = data['plan']
        interval = data['interval']  # 'monthly' or 'yearly'
        
        # 验证计划和间隔
        if plan not in VIP_PRICES or interval not in VIP_PRICES[plan]:
            return jsonify({'error': 'Invalid plan or interval'}), 400
        
        price_cents = VIP_PRICES[plan][interval]
        
        # 计算订阅时长（月）
        months = 1 if interval == 'monthly' else 12
        
        # 创建Stripe结账会话
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'RainbowCity {plan.capitalize()} ({interval})',
                        'description': f'{months} month{"s" if months > 1 else ""} subscription'
                    },
                    'unit_amount': price_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{request.host_url}vip/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{request.host_url}vip/cancel",
            metadata={
                'user_id': current_user.id,
                'plan': plan,
                'interval': interval,
                'months': months
            }
        )
        
        return jsonify({
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error creating checkout session: {str(e)}")
        return jsonify({'error': f'Failed to create checkout session: {str(e)}'}), 500

@vip_bp.route('/success', methods=['GET'])
@token_required
def payment_success(current_user):
    """支付成功处理"""
    try:
        init_stripe()
        
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        
        # 获取会话信息
        session = stripe.checkout.Session.retrieve(session_id)
        
        # 验证用户ID
        if int(session.metadata.get('user_id', 0)) != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # 获取计划信息
        plan = session.metadata.get('plan')
        months = int(session.metadata.get('months', 1))
        
        # 更新用户VIP状态
        try:
            current_user.vip_level = VIPLevel[plan]
        except KeyError:
            return jsonify({'error': 'Invalid plan'}), 400
        
        # 设置过期时间
        if current_user.vip_expiry and current_user.vip_expiry > datetime.utcnow():
            # 如果当前VIP未过期，则延长时间
            current_user.vip_expiry = current_user.vip_expiry + timedelta(days=30*months)
        else:
            # 否则从现在开始计算
            current_user.vip_expiry = datetime.utcnow() + timedelta(days=30*months)
        
        db_session.commit()
        
        return jsonify({
            'message': 'Payment successful',
            'vip_level': current_user.vip_level.value,
            'vip_expiry': current_user.vip_expiry.isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error processing payment success: {str(e)}")
        return jsonify({'error': f'Failed to process payment: {str(e)}'}), 500

@vip_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """处理Stripe Webhook事件"""
    try:
        init_stripe()
        
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get('Stripe-Signature')
        
        # 验证Webhook签名
        endpoint_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
        event = None
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            # 无效的payload
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError as e:
            # 无效的签名
            return jsonify({'error': 'Invalid signature'}), 400
        
        # 处理事件
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # 获取用户和计划信息
            user_id = int(session.metadata.get('user_id', 0))
            plan = session.metadata.get('plan')
            months = int(session.metadata.get('months', 1))
            
            # 查找用户
            user = User.query.get(user_id)
            if not user:
                current_app.logger.error(f"User not found: {user_id}")
                return jsonify({'error': 'User not found'}), 404
            
            # 更新用户VIP状态
            try:
                user.vip_level = VIPLevel[plan]
            except KeyError:
                current_app.logger.error(f"Invalid plan: {plan}")
                return jsonify({'error': 'Invalid plan'}), 400
            
            # 设置过期时间
            if user.vip_expiry and user.vip_expiry > datetime.utcnow():
                # 如果当前VIP未过期，则延长时间
                user.vip_expiry = user.vip_expiry + timedelta(days=30*months)
            else:
                # 否则从现在开始计算
                user.vip_expiry = datetime.utcnow() + timedelta(days=30*months)
            
            db_session.commit()
            current_app.logger.info(f"Updated VIP status for user {user_id}: {plan}, expires {user.vip_expiry}")
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'error': f'Failed to process webhook: {str(e)}'}), 500

@vip_bp.route('/admin/set-vip', methods=['POST'])
@token_required
def admin_set_vip(current_user):
    """管理员设置用户VIP状态（仅限管理员）"""
    # 验证管理员权限
    if not current_user.has_role(UserRole.admin):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data or 'user_id' not in data or 'vip_level' not in data:
        return jsonify({'error': 'User ID and VIP level are required'}), 400
    
    user_id = data['user_id']
    vip_level_name = data['vip_level']
    duration_days = data.get('duration_days', 30)  # 默认30天
    
    # 查找用户
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # 设置VIP等级
    try:
        user.vip_level = VIPLevel[vip_level_name]
    except KeyError:
        return jsonify({'error': 'Invalid VIP level'}), 400
    
    # 设置过期时间
    user.vip_expiry = datetime.utcnow() + timedelta(days=duration_days)
    
    db_session.commit()
    
    return jsonify({
        'message': 'VIP status updated successfully',
        'user_id': user.id,
        'vip_level': user.vip_level.value,
        'vip_expiry': user.vip_expiry.isoformat()
    }), 200
