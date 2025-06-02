from app.extensions import db
from app.models.enums import VIPLevel
from datetime import datetime

class LIOChannel(db.Model):
    """LIO频道模型"""
    __tablename__ = 'lio_channels'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)  # 频道唯一代码
    description = db.Column(db.Text, nullable=True)
    
    # 频道类型：basic（基础）, premium（高级）, beta（内测）, exclusive（专属）
    channel_type = db.Column(db.String(20), default='basic')
    
    # 可见性：public（公开）, vip_only（仅VIP可见）, ultimate_only（仅Ultimate可见）
    visibility = db.Column(db.String(20), default='public')
    
    # 频道状态：active（活跃）, inactive（不活跃）, maintenance（维护中）
    status = db.Column(db.String(20), default='active')
    
    # 创建和更新时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 频道图标和背景图
    icon_url = db.Column(db.String(255), nullable=True)
    background_url = db.Column(db.String(255), nullable=True)
    
    # 频道元数据，可存储额外信息
    metadata = db.Column(db.JSON, nullable=True)
    
    # 不同VIP等级的每日使用限制
    free_daily_limit = db.Column(db.Integer, default=0)
    pro_daily_limit = db.Column(db.Integer, default=15)
    premium_daily_limit = db.Column(db.Integer, default=30)
    ultimate_daily_limit = db.Column(db.Integer, default=-1)  # -1表示无限
    
    def get_daily_limit_for_vip(self, vip_level):
        """获取指定VIP等级的每日使用限制"""
        limits = {
            VIPLevel.free: self.free_daily_limit,
            VIPLevel.pro: self.pro_daily_limit,
            VIPLevel.premium: self.premium_daily_limit,
            VIPLevel.ultimate: self.ultimate_daily_limit,
            VIPLevel.team: self.ultimate_daily_limit  # 团队版与Ultimate相同
        }
        return limits.get(vip_level, 0)
    
    def is_accessible_for_vip(self, vip_level):
        """检查指定VIP等级是否可以访问此频道"""
        # 如果频道不活跃，任何人都不能访问
        if self.status != 'active':
            return False
        
        # 根据可见性检查访问权限
        if self.visibility == 'public':
            return True
        elif self.visibility == 'vip_only':
            return vip_level != VIPLevel.free
        elif self.visibility == 'ultimate_only':
            return vip_level in [VIPLevel.ultimate, VIPLevel.team]
        
        return False
    
    def to_dict(self):
        """将频道对象转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'channel_type': self.channel_type,
            'visibility': self.visibility,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'icon_url': self.icon_url,
            'background_url': self.background_url,
            'limits': {
                'free': self.free_daily_limit,
                'pro': self.pro_daily_limit,
                'premium': self.premium_daily_limit,
                'ultimate': self.ultimate_daily_limit
            },
            'metadata': self.metadata
        }


class UserLIOUsage(db.Model):
    """用户LIO频道使用记录"""
    __tablename__ = 'user_lio_usages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey('lio_channels.id'), nullable=False)
    
    # 使用计数
    daily_usage_count = db.Column(db.Integer, default=0)
    total_usage_count = db.Column(db.Integer, default=0)
    
    # 最后使用和重置时间
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    last_reset = db.Column(db.DateTime, default=datetime.utcnow)
    
    def reset_daily_usage_if_needed(self):
        """如果需要，重置每日使用次数"""
        now = datetime.utcnow()
        if not self.last_reset or (now - self.last_reset).days >= 1:
            self.daily_usage_count = 0
            self.last_reset = now
            return True
        return False
    
    def increment_usage(self):
        """增加使用次数"""
        self.reset_daily_usage_if_needed()
        self.daily_usage_count += 1
        self.total_usage_count += 1
        self.last_used = datetime.utcnow()
    
    def to_dict(self):
        """将使用记录对象转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'channel_id': self.channel_id,
            'daily_usage_count': self.daily_usage_count,
            'total_usage_count': self.total_usage_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'last_reset': self.last_reset.isoformat() if self.last_reset else None
        }
