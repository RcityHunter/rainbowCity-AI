"""推广系统相关模型

这个模块包含推广系统相关的数据模型，包括：
1. 推广链接
2. 推广点击记录
3. 推广转化记录
4. 佣金记录
"""

from app.extensions import db
from datetime import datetime
from app.models.enums import PromoterType

class PromoterLink(db.Model):
    """推广链接模型"""
    __tablename__ = 'promoter_links'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # 链接名称
    code = db.Column(db.String(20), unique=True, nullable=False)  # 推广码
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # 统计数据
    clicks = db.Column(db.Integer, default=0)  # 点击次数
    registrations = db.Column(db.Integer, default=0)  # 注册次数
    conversions = db.Column(db.Integer, default=0)  # 付费转化次数
    
    # 关联关系
    user = db.relationship('User', backref=db.backref('promoter_links', lazy=True))
    
    def __repr__(self):
        return f'<PromoterLink {self.code}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'code': self.code,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'clicks': self.clicks,
            'registrations': self.registrations,
            'conversions': self.conversions
        }
    
    def increment_clicks(self):
        """增加点击次数"""
        self.clicks += 1
        db.session.commit()
    
    def increment_registrations(self):
        """增加注册次数"""
        self.registrations += 1
        db.session.commit()
    
    def increment_conversions(self):
        """增加转化次数"""
        self.conversions += 1
        db.session.commit()


class ClickRecord(db.Model):
    """点击记录模型"""
    __tablename__ = 'click_records'
    
    id = db.Column(db.Integer, primary_key=True)
    link_id = db.Column(db.Integer, db.ForeignKey('promoter_links.id'), nullable=False)
    ip_address = db.Column(db.String(50))  # 访问者IP
    user_agent = db.Column(db.String(255))  # 浏览器信息
    referer = db.Column(db.String(255))  # 来源页面
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    link = db.relationship('PromoterLink', backref=db.backref('clicks_records', lazy=True))
    
    def __repr__(self):
        return f'<ClickRecord {self.id}>'


class ConversionRecord(db.Model):
    """转化记录模型"""
    __tablename__ = 'conversion_records'
    
    id = db.Column(db.Integer, primary_key=True)
    link_id = db.Column(db.Integer, db.ForeignKey('promoter_links.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 被推广用户
    conversion_type = db.Column(db.String(20))  # 转化类型：registration, vip_purchase
    amount = db.Column(db.Integer, default=0)  # 转化金额（如果是付费，以分为单位）
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    link = db.relationship('PromoterLink', backref=db.backref('conversion_records', lazy=True))
    user = db.relationship('User', backref=db.backref('conversion_records', lazy=True))
    
    def __repr__(self):
        return f'<ConversionRecord {self.id}>'


class CommissionRecord(db.Model):
    """佣金记录模型"""
    __tablename__ = 'commission_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 推广用户
    conversion_id = db.Column(db.Integer, db.ForeignKey('conversion_records.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # 佣金金额（以分为单位）
    rate = db.Column(db.Integer, nullable=False)  # 佣金比例（以百分比存储，如 15% 存储为 15）
    status = db.Column(db.String(20), default='pending')  # 状态：pending, paid, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)  # 支付时间
    
    # 关联关系
    user = db.relationship('User', backref=db.backref('commission_records', lazy=True))
    conversion = db.relationship('ConversionRecord', backref=db.backref('commission_record', uselist=False))
    
    def __repr__(self):
        return f'<CommissionRecord {self.id}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'conversion_id': self.conversion_id,
            'amount': self.amount,
            'rate': self.rate,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None
        }


class WithdrawalRecord(db.Model):
    """提现记录模型"""
    __tablename__ = 'withdrawal_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # 提现金额（以分为单位）
    status = db.Column(db.String(20), default='pending')  # 状态：pending, approved, rejected, paid
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)  # 处理时间
    processor_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 处理人（管理员）
    payment_method = db.Column(db.String(50))  # 支付方式
    payment_account = db.Column(db.String(100))  # 支付账号
    remark = db.Column(db.Text)  # 备注
    
    # 关联关系
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('withdrawal_records', lazy=True))
    processor = db.relationship('User', foreign_keys=[processor_id], backref=db.backref('processed_withdrawals', lazy=True))
    
    def __repr__(self):
        return f'<WithdrawalRecord {self.id}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'processor_id': self.processor_id,
            'payment_method': self.payment_method,
            'payment_account': self.payment_account,
            'remark': self.remark
        }
