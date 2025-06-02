"""用户角色扩展迁移脚本

此脚本实现彩虹城用户三大分类架构：
1. 普通用户（Free、Pro、Premium、Ultimate、Team五大等级）
2. 推广用户（个人推广、机构推广）
3. 管理用户（市场、运营、客服、技术、管理员）

Revision ID: user_role_extension
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# 创建枚举类型
def upgrade():
    # 创建推广用户类型枚举
    op.execute("CREATE TYPE promoter_type AS ENUM ('individual', 'institution')")
    
    # 创建管理用户岗位枚举
    op.execute("CREATE TYPE admin_position AS ENUM ('marketing', 'operations', 'customer_service', 'technical', 'management')")
    
    # 创建管理用户级别枚举
    op.execute("CREATE TYPE admin_level AS ENUM ('super_admin', 'admin', 'moderator', 'editor', 'viewer')")
    
    # 添加推广用户相关字段
    op.add_column('users', sa.Column('promoter_type', sa.Enum('individual', 'institution', name='promoter_type'), nullable=True))
    op.add_column('users', sa.Column('promoter_approved', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('users', sa.Column('promoter_application_date', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('promoter_approval_date', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('promoter_commission_rate', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('users', sa.Column('promoter_total_earnings', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('users', sa.Column('promoter_available_balance', sa.Float(), nullable=True, server_default='0.0'))
    
    # 添加管理用户相关字段
    op.add_column('users', sa.Column('admin_position', sa.Enum('marketing', 'operations', 'customer_service', 'technical', 'management', name='admin_position'), nullable=True))
    op.add_column('users', sa.Column('admin_level', sa.Enum('super_admin', 'admin', 'moderator', 'editor', 'viewer', name='admin_level'), nullable=True))
    op.add_column('users', sa.Column('admin_permissions', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'))

def downgrade():
    # 删除管理用户相关字段
    op.drop_column('users', 'admin_permissions')
    op.drop_column('users', 'admin_level')
    op.drop_column('users', 'admin_position')
    
    # 删除推广用户相关字段
    op.drop_column('users', 'promoter_available_balance')
    op.drop_column('users', 'promoter_total_earnings')
    op.drop_column('users', 'promoter_commission_rate')
    op.drop_column('users', 'promoter_approval_date')
    op.drop_column('users', 'promoter_application_date')
    op.drop_column('users', 'promoter_approved')
    op.drop_column('users', 'promoter_type')
    
    # 删除枚举类型
    op.execute("DROP TYPE admin_position")
    op.execute("DROP TYPE admin_level")
    op.execute("DROP TYPE promoter_type")
