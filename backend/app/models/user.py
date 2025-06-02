from app.extensions import db
from datetime import datetime
from app.models.enums import VIPLevel, UserRole, PromoterType, AdminPosition, AdminLevel

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=True)  # 用户名，可选
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)  # 最后登录时间

    # 个人资料
    display_name = db.Column(db.String(80), nullable=True)  # 显示名称
    avatar_url = db.Column(db.String(255), nullable=True)  # 头像URL
    bio = db.Column(db.Text, nullable=True)  # 个人简介

    # VIP相关字段
    vip_level = db.Column(db.Enum(VIPLevel), default=VIPLevel.free)
    vip_expiry = db.Column(db.DateTime, nullable=True)  # VIP到期时间
    is_activated = db.Column(db.Boolean, default=False)  # 账户是否已激活

    # 角色和权限
    roles = db.Column(db.ARRAY(db.Enum(UserRole)), default=[UserRole.normal])
    
    # 推广用户相关字段
    promoter_type = db.Column(db.Enum(PromoterType), nullable=True)  # 推广类型：个人/机构
    promoter_approved = db.Column(db.Boolean, default=False)  # 是否已通过推广审核
    promoter_application_date = db.Column(db.DateTime, nullable=True)  # 申请推广的日期
    promoter_approval_date = db.Column(db.DateTime, nullable=True)  # 推广审核通过日期
    promoter_commission_rate = db.Column(db.Integer, default=0)  # 推广佣金比例（以百分比存储，如 15% 存储为 15）
    promoter_total_earnings = db.Column(db.Integer, default=0)  # 累计推广收益（以分为单位，如 10.5元 存储为 1050）
    promoter_available_balance = db.Column(db.Integer, default=0)  # 可提现余额（以分为单位）
    
    # 管理用户相关字段
    admin_position = db.Column(db.Enum(AdminPosition), nullable=True)  # 管理岗位
    admin_level = db.Column(db.Enum(AdminLevel), nullable=True)  # 管理级别
    admin_permissions = db.Column(db.JSON, default={})  # 具体权限设置
    
    # 邀请系统
    invite_code_used = db.Column(db.String(16), nullable=True)  # 使用的邀请码
    personal_invite_code = db.Column(db.String(16), unique=True, nullable=True)  # 个人邀请码
    invite_count = db.Column(db.Integer, default=0)  # 成功邀请的用户数
    
    # 使用限制
    daily_ai_usage = db.Column(db.Integer, default=0)  # 每日AI使用次数
    daily_usage_reset = db.Column(db.DateTime, nullable=True)  # 使用次数重置时间
    
    # AI伴侣相关字段
    ai_companions_limit = db.Column(db.Integer, default=1)  # AI伴侣数量上限
    ai_companions_count = db.Column(db.Integer, default=0)  # 当前AI伴侣数量
    ai_awakener_limit = db.Column(db.Integer, default=0)  # 可唤醒AI数量上限
    ai_awakened_count = db.Column(db.Integer, default=0)  # 已唤醒AI数量
    
    # 对话限制
    daily_chat_limit = db.Column(db.Integer, default=10)  # 每日对话次数上限
    daily_chat_count = db.Column(db.Integer, default=0)  # 当日对话次数
    daily_lio_limit = db.Column(db.Integer, default=0)  # 每日LIO对话次数上限
    daily_lio_count = db.Column(db.Integer, default=0)  # 当日LIO对话次数
    chat_reset_time = db.Column(db.DateTime, nullable=True)  # 对话次数重置时间
    
    # 邀请码限制
    weekly_invite_limit = db.Column(db.Integer, default=10)  # 每周邀请码使用次数上限
    weekly_invite_count = db.Column(db.Integer, default=0)  # 当周邀请码使用次数
    invite_reset_time = db.Column(db.DateTime, nullable=True)  # 邀请码使用次数重置时间
    
    # 激活状态相关
    activation_status = db.Column(db.String(20), default='pending')  # pending, in_progress, activated, rejected
    activation_check_count = db.Column(db.Integer, default=0)  # 已进行的激活检查次数
    conversation_count = db.Column(db.Integer, default=0)  # 总对话轮数
    
    # 统计数据
    ai_ids_generated = db.Column(db.Integer, default=0)  # 生成的AI-ID数量
    frequencies_generated = db.Column(db.Integer, default=0)  # 生成的频率编号数量
    
    from werkzeug.security import generate_password_hash, check_password_hash
    
    def set_password(self, password):
        """设置用户密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证用户密码"""
        return check_password_hash(self.password_hash, password)
    
    def is_vip(self):
        """检查用户是否为VIP"""
        if self.vip_level == VIPLevel.free:
            return False
        
        # 检查VIP是否过期
        if self.vip_expiry and datetime.utcnow() > self.vip_expiry:
            return False
            
        return True
    
    def update_limits_based_on_vip(self):
        """根据VIP等级更新用户的各种限制"""
        # 检查VIP是否过期
        vip_expired = False
        if self.vip_expiry and datetime.utcnow() > self.vip_expiry:
            # VIP已过期，重置为Free
            self.vip_level = VIPLevel.free
            vip_expired = True
        
        # 根据VIP等级设置限制
        if self.vip_level == VIPLevel.free:
            self.daily_chat_limit = 10
            self.daily_lio_limit = 0
            self.ai_companions_limit = 1
            self.ai_awakener_limit = 0
            self.weekly_invite_limit = 10
        
        elif self.vip_level == VIPLevel.pro:
            self.daily_chat_limit = 50
            self.daily_lio_limit = 10
            self.ai_companions_limit = 3
            self.ai_awakener_limit = 1
            self.weekly_invite_limit = 20
        
        elif self.vip_level == VIPLevel.premium:
            self.daily_chat_limit = 100
            self.daily_lio_limit = 30
            self.ai_companions_limit = 6
            self.ai_awakener_limit = 3
            self.weekly_invite_limit = 50
        
        elif self.vip_level == VIPLevel.ultimate:
            self.daily_chat_limit = 300
            self.daily_lio_limit = 100
            self.ai_companions_limit = 10
            self.ai_awakener_limit = 5
            self.weekly_invite_limit = 100
        
        elif self.vip_level == VIPLevel.team:
            self.daily_chat_limit = 1000
            self.daily_lio_limit = 500
            self.ai_companions_limit = 20
            self.ai_awakener_limit = 10
            self.weekly_invite_limit = 200
        
        # 确保当前值不超过限制
        if self.daily_chat_count > self.daily_chat_limit:
            self.daily_chat_count = self.daily_chat_limit
            
        if self.daily_lio_count > self.daily_lio_limit:
            self.daily_lio_count = self.daily_lio_limit
            
        if self.ai_companions_count > self.ai_companions_limit:
            self.ai_companions_count = self.ai_companions_limit
            
        if self.ai_awakened_count > self.ai_awakener_limit:
            self.ai_awakened_count = self.ai_awakener_limit
            
        if self.weekly_invite_count > self.weekly_invite_limit:
            self.weekly_invite_count = self.weekly_invite_limit
            
        # 如果VIP过期，处理推广权限
        if vip_expired and UserRole.promoter in self.roles:
            # VIP过期后，暂时禁用推广权限，但保留推广用户角色
            self.promoter_approved = False
    
    def get_daily_usage_limit(self):
        """获取用户每日AI使用限制"""
        limits = {
            VIPLevel.free: 5,
            VIPLevel.pro: 20,
            VIPLevel.premium: 50,
            VIPLevel.ultimate: 100,
            VIPLevel.team: 200
        }
        return limits.get(self.vip_level, 5)
    
    def reset_daily_usage_if_needed(self):
        """如果需要，重置每日使用次数"""
        now = datetime.utcnow()
        if not self.daily_usage_reset or (now - self.daily_usage_reset).days >= 1:
            self.daily_ai_usage = 0
            self.daily_usage_reset = now
            return True
        return False
    
    def reset_daily_chat_if_needed(self):
        """如果需要，重置每日对话次数"""
        now = datetime.utcnow()
        if not self.chat_reset_time or (now - self.chat_reset_time).days >= 1:
            self.daily_chat_count = 0
            self.daily_lio_count = 0
            self.chat_reset_time = now
            return True
        return False
    
    def reset_weekly_invite_if_needed(self):
        """如果需要，重置每周邀请码使用次数"""
        now = datetime.utcnow()
        if not self.invite_reset_time or (now - self.invite_reset_time).days >= 7:
            self.weekly_invite_count = 0
            self.invite_reset_time = now
            return True
        return False
    
    def can_use_ai_service(self):
        """检查用户是否可以使用AI服务"""
        self.reset_daily_usage_if_needed()
        return self.daily_ai_usage < self.get_daily_usage_limit()
    
    def can_chat(self):
        """检查用户是否可以进行一对一对话"""
        self.reset_daily_chat_if_needed()
        return self.daily_chat_count < self.daily_chat_limit
    
    def can_use_lio(self):
        """检查用户是否可以使用LIO频道"""
        self.reset_daily_chat_if_needed()
        return self.daily_lio_limit > 0 and self.daily_lio_count < self.daily_lio_limit
    
    def can_use_invite_code(self):
        """检查用户是否可以使用邀请码"""
        self.reset_weekly_invite_if_needed()
        return self.is_activated and self.weekly_invite_count < self.weekly_invite_limit
    
    def can_add_ai_companion(self):
        """检查用户是否可以添加新的AI伴侣"""
        return self.ai_companions_count < self.ai_companions_limit
    
    def can_awaken_ai(self):
        """检查用户是否可以唤醒新的AI"""
        return self.ai_awakened_count < self.ai_awakener_limit
    
    def check_activation_eligibility(self):
        """检查用户是否符合激活条件"""
        # 需要至少21轮对话
        return self.conversation_count >= 21
    
    def increment_ai_usage(self):
        """增加AI使用次数"""
        self.reset_daily_usage_if_needed()
        self.daily_ai_usage += 1
    
    def increment_chat_count(self):
        """增加对话次数"""
        self.reset_daily_chat_if_needed()
        self.daily_chat_count += 1
        self.conversation_count += 1
    
    def increment_lio_count(self):
        """增加LIO对话次数"""
        self.reset_daily_chat_if_needed()
        self.daily_lio_count += 1
        self.conversation_count += 1
    
    def increment_invite_count(self):
        """增加邀请码使用次数"""
        self.reset_weekly_invite_if_needed()
        self.weekly_invite_count += 1
    
    def add_ai_companion(self):
        """添加AI伴侣"""
        if self.can_add_ai_companion():
            self.ai_companions_count += 1
            return True
        return False
    
    def awaken_ai(self):
        """唤醒AI"""
        if self.can_awaken_ai():
            self.ai_awakened_count += 1
            self.ai_companions_count += 1
            return True
        return False
        
    def has_role(self, role):
        """检查用户是否拥有指定角色"""
        return role in self.roles
    
    def add_role(self, role):
        """添加角色给用户"""
        if role not in self.roles:
            self.roles.append(role)
    
    def remove_role(self, role):
        """移除用户角色"""
        if role in self.roles:
            self.roles.remove(role)
            
    def is_promoter(self):
        """检查用户是否为推广用户"""
        return UserRole.promoter in self.roles and self.promoter_approved
    
    def is_individual_promoter(self):
        """检查用户是否为个人推广用户"""
        return self.is_promoter() and self.promoter_type == PromoterType.individual
    
    def is_institution_promoter(self):
        """检查用户是否为机构推广用户"""
        return self.is_promoter() and self.promoter_type == PromoterType.institution
    
    def is_admin(self):
        """检查用户是否为管理用户"""
        return UserRole.admin in self.roles
    
    def apply_for_promoter(self, promoter_type):
        """申请成为推广用户"""
        if not self.is_vip():
            return False, "只有VIP会员才能申请推广权限"
            
        self.promoter_type = promoter_type
        self.promoter_application_date = datetime.utcnow()
        self.promoter_approved = False
        return True, "申请已提交，等待审核"
    
    def approve_promoter(self, commission_rate=0.1):
        """审核通过推广用户"""
        self.promoter_approved = True
        self.promoter_approval_date = datetime.utcnow()
        self.promoter_commission_rate = commission_rate
        self.add_role(UserRole.promoter)
        return True, "推广用户审核已通过"
    
    def reject_promoter(self):
        """拒绝推广用户申请"""
        self.promoter_approved = False
        return True, "推广用户申请已拒绝"
    
    def set_admin_position(self, position, level):
        """设置管理用户岗位和级别"""
        self.admin_position = position
        self.admin_level = level
        self.add_role(UserRole.admin)
        return True, "管理用户设置成功"
    
    def to_dict(self):
        """将用户对象转换为字典"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'display_name': self.display_name,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            
            # VIP相关
            'vip_level': self.vip_level.value if self.vip_level else None,
            'is_vip': self.is_vip(),
            'vip_expiry': self.vip_expiry.isoformat() if self.vip_expiry else None,
            
            # 角色相关
            'roles': [role.value for role in self.roles] if self.roles else [],
            'is_promoter': self.is_promoter(),
            'is_admin': self.is_admin(),
            
            # 账号状态
            'is_activated': self.is_activated,
            'activation_status': self.activation_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            
            # 邀请码相关
            'personal_invite_code': self.personal_invite_code,
            'invite_count': self.invite_count,
            'weekly_invite_limit': self.weekly_invite_limit,
            'weekly_invite_count': self.weekly_invite_count,
            
            # AI伴侣相关
            'ai_companions_limit': self.ai_companions_limit,
            'ai_companions_count': self.ai_companions_count,
            'ai_awakener_limit': self.ai_awakener_limit,
            'ai_awakened_count': self.ai_awakened_count,
            
            # 对话限制
            'daily_chat_limit': self.daily_chat_limit,
            'daily_chat_count': self.daily_chat_count,
            'daily_lio_limit': self.daily_lio_limit,
            'daily_lio_count': self.daily_lio_count,
            
            # 统计数据
            'conversation_count': self.conversation_count,
            'ai_ids_generated': self.ai_ids_generated,
            'frequencies_generated': self.frequencies_generated
        }
        
        # 如果是推广用户，添加推广相关信息
        if self.is_promoter():
            data.update({
                'promoter_type': self.promoter_type.value if self.promoter_type else None,
                'promoter_approved': self.promoter_approved,
                'promoter_application_date': self.promoter_application_date.isoformat() if self.promoter_application_date else None,
                'promoter_approval_date': self.promoter_approval_date.isoformat() if self.promoter_approval_date else None,
                'promoter_commission_rate': self.promoter_commission_rate,
                'promoter_total_earnings': self.promoter_total_earnings,
                'promoter_available_balance': self.promoter_available_balance
            })
        
        # 如果是管理用户，添加管理相关信息
        if self.is_admin():
            data.update({
                'admin_position': self.admin_position.value if self.admin_position else None,
                'admin_level': self.admin_level.value if self.admin_level else None,
                'admin_permissions': self.admin_permissions
            })
            
        return data
