from app.extensions import db
from datetime import datetime
import random
import string

class InviteCode(db.Model):
    """邀请码模型"""
    __tablename__ = 'invite_codes'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 创建者ID，可为空表示系统生成
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # 过期时间，可为空表示永不过期
    max_uses = db.Column(db.Integer, default=1)  # 最大使用次数，默认为1
    current_uses = db.Column(db.Integer, default=0)  # 当前已使用次数
    is_active = db.Column(db.Boolean, default=True)  # 是否激活
    
    # 邀请码类型：personal（个人）, system（系统）, promotional（推广）
    type = db.Column(db.String(20), default='personal')
    
    # 邀请码特权：可以为空，或包含特定权益，如直接获得VIP等
    benefits = db.Column(db.JSON, nullable=True)
    
    @classmethod
    def generate_code(cls, length=8):
        """生成随机邀请码"""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choice(chars) for _ in range(length))
            # 检查是否已存在
            if not cls.query.filter_by(code=code).first():
                return code
    
    @classmethod
    def create_personal_code(cls, user_id):
        """为用户创建个人邀请码"""
        code = cls.generate_code()
        invite = cls(
            code=code,
            creator_id=user_id,
            type='personal',
            max_uses=10  # 个人邀请码可使用10次
        )
        db.session.add(invite)
        return invite
    
    @classmethod
    def create_system_code(cls, max_uses=None, expires_at=None, benefits=None):
        """创建系统邀请码"""
        code = cls.generate_code()
        invite = cls(
            code=code,
            type='system',
            max_uses=max_uses,
            expires_at=expires_at,
            benefits=benefits
        )
        db.session.add(invite)
        return invite
    
    def is_valid(self):
        """检查邀请码是否有效"""
        if not self.is_active:
            return False
        
        # 检查是否过期
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        # 检查使用次数
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
            
        return True
    
    def use(self):
        """使用邀请码"""
        if not self.is_valid():
            return False
        
        self.current_uses += 1
        
        # 如果达到最大使用次数，自动停用
        if self.max_uses and self.current_uses >= self.max_uses:
            self.is_active = False
            
        return True
    
    def to_dict(self):
        """将邀请码对象转换为字典"""
        return {
            'id': self.id,
            'code': self.code,
            'creator_id': self.creator_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'max_uses': self.max_uses,
            'current_uses': self.current_uses,
            'is_active': self.is_active,
            'type': self.type,
            'is_valid': self.is_valid()
        }
