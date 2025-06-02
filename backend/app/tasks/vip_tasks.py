from datetime import datetime
from app.db import db_session
from app.models.user import User
from app.models.enums import VIPLevel, UserRole, PromoterStatus
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_vip_expiry():
    """检查所有用户的VIP过期状态并处理"""
    logger.info("开始检查VIP过期状态...")
    
    # 查询所有VIP用户
    vip_users = User.query.filter(User.vip_level != VIPLevel.free).all()
    
    expired_count = 0
    for user in vip_users:
        if user.vip_expiry and datetime.utcnow() > user.vip_expiry:
            # 处理VIP过期
            old_level = user.vip_level
            
            # 降级为免费用户
            user.vip_level = VIPLevel.free
            
            # 更新用户限制
            user.update_limits_based_on_vip()
            
            # 如果是推广用户，暂停推广权限
            if user.has_role(UserRole.promoter) and user.promoter_status != PromoterStatus.suspended:
                user.promoter_status = PromoterStatus.suspended
                logger.info(f"用户 {user.id} ({user.username or user.email}) 的推广权限已暂停")
            
            expired_count += 1
            logger.info(f"用户 {user.id} ({user.username or user.email}) 的VIP已过期，从 {old_level.value} 降级为 {user.vip_level.value}")
    
    if expired_count > 0:
        # 提交数据库更改
        db_session.commit()
        logger.info(f"共处理 {expired_count} 个过期VIP用户")
    else:
        logger.info("没有发现过期VIP用户")
    
    return expired_count

def run_scheduled_tasks():
    """运行所有计划任务"""
    try:
        # 检查VIP过期
        check_vip_expiry()
        
        # 可以添加其他定时任务
        
        logger.info("所有计划任务已完成")
    except Exception as e:
        logger.error(f"计划任务执行出错: {str(e)}")
        # 出错时回滚数据库
        db_session.rollback()
