from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union, Literal
from datetime import datetime, timedelta
import stripe
import logging
import os

from app.db import query, update as db_update, create
from app.models.enums import VIPLevel, UserRole
from app.routes.auth_routes import get_current_user

# 创建路由器
router = APIRouter(prefix="/vip", tags=["VIP会员"])

# 初始化Stripe
def init_stripe():
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

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

# 定义请求和响应模型
class VIPPlan(BaseModel):
    level: str
    name: str
    features: Dict[str, Any]
    prices: Dict[str, int]
    ai_companions_limit: int
    ai_awakener_limit: int
    daily_chat_limit: Union[int, float]
    daily_lio_limit: Union[int, float]
    weekly_invite_limit: Union[int, float]

class VIPPlansResponse(BaseModel):
    plans: List[VIPPlan]

class VIPStatusResponse(BaseModel):
    is_vip: bool
    vip_level: Optional[str] = None
    vip_expiry: Optional[str] = None
    daily_usage: Dict[str, Any]
    benefits: Dict[str, Any]

class CheckoutRequest(BaseModel):
    plan: str
    interval: Literal['monthly', 'yearly']

class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str

class AdminSetVIPRequest(BaseModel):
    user_id: str
    vip_level: str
    duration_days: Optional[int] = 30

class VIPStatusUpdateResponse(BaseModel):
    message: str
    user_id: str
    vip_level: str
    vip_expiry: str

# 获取所有VIP套餐信息
@router.get("/plans", response_model=VIPPlansResponse)
async def get_vip_plans():
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
    
    logging.info(f"Returning VIP plans: {plans_list}")
    return {"plans": plans_list}

# 获取当前用户的VIP状态
@router.get("/status", response_model=VIPStatusResponse)
async def get_vip_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    """获取当前用户的VIP状态"""
    # 检查用户是否为VIP
    is_vip = False
    vip_level = current_user.get('vip_level')
    vip_expiry = current_user.get('vip_expiry')
    
    if vip_level and vip_level != 'free':
        if vip_expiry:
            # 检查VIP是否过期
            expiry_date = datetime.fromisoformat(vip_expiry)
            is_vip = expiry_date > datetime.utcnow()
    
    # 获取用户每日使用限制
    daily_limit = VIP_BENEFITS.get(vip_level, VIP_BENEFITS['free']).get('daily_chat_limit', 10)
    
    return {
        'is_vip': is_vip,
        'vip_level': vip_level,
        'vip_expiry': vip_expiry,
        'daily_usage': {
            'current': current_user.get('daily_ai_usage', 0),
            'limit': daily_limit
        },
        'benefits': VIP_BENEFITS.get(vip_level, VIP_BENEFITS['free'])
    }

# 创建Stripe结账会话
@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    checkout_data: CheckoutRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """创建Stripe结账会话"""
    try:
        init_stripe()
        
        plan = checkout_data.plan
        interval = checkout_data.interval
        
        # 验证计划和间隔
        if plan not in VIP_PRICES or interval not in VIP_PRICES[plan]:
            raise HTTPException(status_code=400, detail="Invalid plan or interval")
        
        price_cents = VIP_PRICES[plan][interval]
        
        # 计算订阅时长（月）
        months = 1 if interval == 'monthly' else 12
        
        # 创建Stripe结账会话
        base_url = str(request.base_url).rstrip('/')
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
            success_url=f"{base_url}/vip/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/vip/cancel",
            metadata={
                'user_id': current_user.get('id'),
                'plan': plan,
                'interval': interval,
                'months': months
            }
        )
        
        return {
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        }
        
    except stripe.error.StripeError as e:
        logging.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        logging.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")

# 支付成功处理
@router.get("/success", response_model=Dict[str, Any])
async def payment_success(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """支付成功处理"""
    try:
        init_stripe()
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")
        
        # 获取会话信息
        session = stripe.checkout.Session.retrieve(session_id)
        
        # 验证用户ID
        if session.metadata.get('user_id') != current_user.get('id'):
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # 获取计划信息
        plan = session.metadata.get('plan')
        months = int(session.metadata.get('months', 1))
        
        # 更新用户VIP状态
        try:
            # 检查计划是否有效
            if plan not in [level.name for level in VIPLevel]:
                raise HTTPException(status_code=400, detail="Invalid plan")
            
            # 设置过期时间
            current_expiry = current_user.get('vip_expiry')
            new_expiry = None
            
            if current_expiry:
                expiry_date = datetime.fromisoformat(current_expiry)
                if expiry_date > datetime.utcnow():
                    # 如果当前VIP未过期，则延长时间
                    new_expiry = (expiry_date + timedelta(days=30*months)).isoformat()
                else:
                    # 否则从现在开始计算
                    new_expiry = (datetime.utcnow() + timedelta(days=30*months)).isoformat()
            else:
                # 没有过期时间，从现在开始计算
                new_expiry = (datetime.utcnow() + timedelta(days=30*months)).isoformat()
            
            # 更新用户信息
            update_data = {
                'vip_level': plan,
                'vip_expiry': new_expiry
            }
            
            result = db_update('users', current_user.get('id'), update_data)
            
            if not result:
                raise HTTPException(status_code=500, detail="Failed to update VIP status")
            
            return {
                'message': 'Payment successful',
                'vip_level': plan,
                'vip_expiry': new_expiry
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Error updating VIP status: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update VIP status: {str(e)}")
        
    except stripe.error.StripeError as e:
        logging.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        logging.error(f"Error processing payment success: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process payment: {str(e)}")

# 处理Stripe Webhook事件
@router.post("/webhook", status_code=200)
async def stripe_webhook(request: Request):
    """处理Stripe Webhook事件"""
    try:
        init_stripe()
        
        # 获取请求数据和签名
        payload = await request.body()
        sig_header = request.headers.get('Stripe-Signature')
        
        # 验证Webhook签名
        endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            # 无效的payload
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            # 无效的签名
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # 处理事件
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # 获取用户和计划信息
            user_id = session.metadata.get('user_id')
            plan = session.metadata.get('plan')
            months = int(session.metadata.get('months', 1))
            
            # 查找用户
            users = query('users', {'id': user_id})
            if not users or len(users) == 0:
                logging.error(f"User not found: {user_id}")
                return {"status": "error", "message": "User not found"}
            
            user = users[0]
            
            # 检查计划是否有效
            if plan not in [level.name for level in VIPLevel]:
                logging.error(f"Invalid plan: {plan}")
                return {"status": "error", "message": "Invalid plan"}
            
            # 设置过期时间
            current_expiry = user.get('vip_expiry')
            new_expiry = None
            
            if current_expiry:
                expiry_date = datetime.fromisoformat(current_expiry)
                if expiry_date > datetime.utcnow():
                    # 如果当前VIP未过期，则延长时间
                    new_expiry = (expiry_date + timedelta(days=30*months)).isoformat()
                else:
                    # 否则从现在开始计算
                    new_expiry = (datetime.utcnow() + timedelta(days=30*months)).isoformat()
            else:
                # 没有过期时间，从现在开始计算
                new_expiry = (datetime.utcnow() + timedelta(days=30*months)).isoformat()
            
            # 更新用户信息
            update_data = {
                'vip_level': plan,
                'vip_expiry': new_expiry
            }
            
            result = db_update('users', user_id, update_data)
            
            if not result:
                logging.error(f"Failed to update VIP status for user {user_id}")
                return {"status": "error", "message": "Failed to update VIP status"}
            
            logging.info(f"Updated VIP status for user {user_id}: {plan}, expires {new_expiry}")
        
        return {"status": "success"}
        
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        # 返回200状态码，避免Stripe重试
        return {"status": "error", "message": f"Failed to process webhook: {str(e)}"}

# 管理员设置用户VIP状态（仅限管理员）
@router.post("/admin/set-vip", response_model=VIPStatusUpdateResponse)
async def admin_set_vip(
    vip_data: AdminSetVIPRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """管理员设置用户VIP状态（仅限管理员）"""
    try:
        # 验证管理员权限
        if 'admin' not in current_user.get('roles', []):
            raise HTTPException(status_code=403, detail="Only administrators can update user VIP level")
        
        user_id = vip_data.user_id
        vip_level_name = vip_data.vip_level
        duration_days = vip_data.duration_days or 30
        
        # 查找用户
        users = query('users', {'id': user_id})
        if not users or len(users) == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 检查VIP等级是否有效
        if vip_level_name not in [level.name for level in VIPLevel]:
            raise HTTPException(status_code=400, detail=f"Invalid VIP level: {vip_level_name}")
        
        # 设置过期时间
        new_expiry = (datetime.utcnow() + timedelta(days=duration_days)).isoformat()
        
        # 更新用户VIP状态
        update_data = {
            'vip_level': vip_level_name,
            'vip_expiry': new_expiry
        }
        
        result = db_update('users', user_id, update_data)
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to update VIP status")
        
        return {
            'message': 'VIP status updated successfully',
            'user_id': user_id,
            'vip_level': vip_level_name,
            'vip_expiry': new_expiry
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating user VIP level: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update user VIP level: {str(e)}")
