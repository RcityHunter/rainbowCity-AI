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
        port=5001,  # 使用端口 5001 避免与其他服务冲突
        reload=False,  # 暂时禁用热重载以查看完整日志
        log_level="debug"  # 增加日志级别
    )
