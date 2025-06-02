import enum

class VIPLevel(enum.Enum):
    free = "Free"
    pro = "Pro"
    premium = "Premium"
    ultimate = "Ultimate"
    team = "Team"

class UserRole(enum.Enum):
    normal = "normal"      # 普通用户
    promoter = "promoter"  # 推广用户
    admin = "admin"        # 管理用户

class PromoterType(enum.Enum):
    individual = "individual"  # 个人推广
    institution = "institution"  # 机构推广

class AdminPosition(enum.Enum):
    marketing = "marketing"    # 市场
    operations = "operations"  # 运营
    customer_service = "customer_service"  # 客服
    technical = "technical"    # 技术
    management = "management"  # 管理员

class AdminLevel(enum.Enum):
    super_admin = 1  # 超级管理员
    admin = 2        # 管理员
    moderator = 3    # 版主
    editor = 4       # 编辑
    viewer = 5       # 查看者
