# 彩虹城 AI 共生社区后端包初始化
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入数据库初始化函数
from .db import init_db

# 注意：FastAPI 应用现在在 fastapi_app.py 中定义
# 这个文件只用于包初始化和一些共享配置

# 定义一些全局配置
APP_CONFIG = {
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev_key_please_change_in_production'),
    'STRIPE_SECRET_KEY': os.environ.get('STRIPE_SECRET_KEY', ''),
    'STRIPE_WEBHOOK_SECRET': os.environ.get('STRIPE_WEBHOOK_SECRET', ''),
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB最大上传文件大小
}

# 设置日志级别，减少不必要的调试输出
import logging
logging.getLogger('asyncio').setLevel(logging.ERROR)