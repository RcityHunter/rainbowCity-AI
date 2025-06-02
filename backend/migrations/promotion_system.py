"""推广系统数据库迁移脚本

此脚本创建推广系统相关的表：
1. promoter_links - 推广链接表
2. click_records - 点击记录表
3. conversion_records - 转化记录表
4. commission_records - 佣金记录表
5. withdrawal_records - 提现记录表

Revision ID: promotion_system
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # 创建推广链接表
    op.create_table(
        'promoter_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('clicks', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('registrations', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('conversions', sa.Integer(), nullable=True, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    
    # 创建点击记录表
    op.create_table(
        'click_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('link_id', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('referer', sa.String(255), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['link_id'], ['promoter_links.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建转化记录表
    op.create_table(
        'conversion_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('link_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('conversion_type', sa.String(20), nullable=True),
        sa.Column('amount', sa.Float(), nullable=True, server_default='0'),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['link_id'], ['promoter_links.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建佣金记录表
    op.create_table(
        'commission_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('conversion_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('rate', sa.Float(), nullable=False),
        sa.Column('status', sa.String(20), nullable=True, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conversion_id'], ['conversion_records.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建提现记录表
    op.create_table(
        'withdrawal_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('status', sa.String(20), nullable=True, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('processor_id', sa.Integer(), nullable=True),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('payment_account', sa.String(100), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['processor_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_promoter_links_user_id', 'promoter_links', ['user_id'], unique=False)
    op.create_index('ix_click_records_link_id', 'click_records', ['link_id'], unique=False)
    op.create_index('ix_conversion_records_link_id', 'conversion_records', ['link_id'], unique=False)
    op.create_index('ix_conversion_records_user_id', 'conversion_records', ['user_id'], unique=False)
    op.create_index('ix_commission_records_user_id', 'commission_records', ['user_id'], unique=False)
    op.create_index('ix_commission_records_conversion_id', 'commission_records', ['conversion_id'], unique=False)
    op.create_index('ix_withdrawal_records_user_id', 'withdrawal_records', ['user_id'], unique=False)

def downgrade():
    # 删除表
    op.drop_table('withdrawal_records')
    op.drop_table('commission_records')
    op.drop_table('conversion_records')
    op.drop_table('click_records')
    op.drop_table('promoter_links')
