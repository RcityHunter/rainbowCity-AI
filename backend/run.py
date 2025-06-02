from app import app
from app.db import init_db
import os
import sys
import asyncio
import signal
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化数据库
init_db(app)

# 处理Windows上的asyncio事件循环清理
def handle_asyncio_cleanup():
    # 在Windows上特别处理IocpProactor问题
    if sys.platform.startswith('win'):
        # 获取当前事件循环
        loop = asyncio.get_event_loop()
        
        # 如果是IocpProactor类型，添加清理代码
        if isinstance(loop, asyncio.ProactorEventLoop):
            # 关闭所有未完成的任务
            def close_all_tasks(loop):
                pending = asyncio.all_tasks(loop)
                if pending:
                    print(f"Cancelling {len(pending)} pending tasks...")
                    for task in pending:
                        task.cancel()
                    loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
                    print("All pending tasks cancelled.")
            
            # 注册信号处理程序
            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    signal.signal(sig, lambda s, f: close_all_tasks(loop))
                except (ValueError, RuntimeError):
                    # 如果信号处理程序已经设置，忽略错误
                    pass

# 设置日志级别，减少不必要的调试输出
import logging
logging.getLogger('asyncio').setLevel(logging.ERROR)

if __name__ == '__main__':
    # 应用asyncio清理处理
    handle_asyncio_cleanup()
    
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)  # 允许从任何 IP 访问