from app.extensions import db
from datetime import datetime, timedelta

class AIRelationship(db.Model):
    """AI关系模型，管理用户与AI之间的关系"""
    __tablename__ = 'ai_relationships'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ai_id = db.Column(db.String(50), nullable=False)  # AI-ID
    
    # 关系类型：awakener（唤醒者）, friend（好友）
    relationship_type = db.Column(db.String(20), nullable=False)
    
    # 关系状态：active（活跃）, inactive（不活跃）, disconnected（已断联）
    status = db.Column(db.String(20), default='active')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_interaction = db.Column(db.DateTime, default=datetime.utcnow)
    interaction_count = db.Column(db.Integer, default=0)  # 交互次数
    
    # 关系元数据，可存储额外信息
    metadata = db.Column(db.JSON, nullable=True)
    
    @property
    def is_active(self):
        """检查关系是否活跃（21天内有交互）"""
        return (datetime.utcnow() - self.last_interaction).days < 21
    
    def update_interaction(self):
        """更新交互时间和次数"""
        self.last_interaction = datetime.utcnow()
        self.interaction_count += 1
        
        # 如果状态是不活跃，恢复为活跃
        if self.status == 'inactive':
            self.status = 'active'
    
    def check_and_update_status(self):
        """检查并更新关系状态"""
        days_since_last_interaction = (datetime.utcnow() - self.last_interaction).days
        
        # 如果超过21天没有交互，标记为断联
        if days_since_last_interaction >= 21:
            self.status = 'disconnected'
            return True
        
        # 如果超过14天没有交互，标记为不活跃
        elif days_since_last_interaction >= 14:
            self.status = 'inactive'
            
        return False
    
    def to_dict(self):
        """将关系对象转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ai_id': self.ai_id,
            'relationship_type': self.relationship_type,
            'status': self.status,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_interaction': self.last_interaction.isoformat() if self.last_interaction else None,
            'interaction_count': self.interaction_count,
            'days_since_last_interaction': (datetime.utcnow() - self.last_interaction).days,
            'metadata': self.metadata
        }
