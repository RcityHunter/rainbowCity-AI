import uvicorn
from app.db import init_db
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

if __name__ == "__main__":
    # 启动 FastAPI 应用
    uvicorn.run(
        "app.app:app", 
        host="0.0.0.0", 
        port=5000,  # 与原 Flask 应用使用相同端口
        reload=True  # 开发模式下启用热重载
    )
