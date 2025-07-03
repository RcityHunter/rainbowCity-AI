import time
import surrealdb
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)

# SurrealDB 连接参数
SURREAL_URL = "ws://localhost:8080"
SURREAL_USER = "root"
SURREAL_PASS = "123"
SURREAL_NS = "rainbow"
SURREAL_DB = "test"

def test_connection():
    logging.info(f"测试连接到 SurrealDB: {SURREAL_URL}")
    logging.info(f"使用凭据: user={SURREAL_USER}, pass={SURREAL_PASS}")
    logging.info(f"命名空间: {SURREAL_NS}, 数据库: {SURREAL_DB}")
    
    try:
        # 创建客户端
        db = surrealdb.Surreal(SURREAL_URL)
        logging.info(f"已创建客户端对象: {type(db)}")
        
        # 等待连接建立
        logging.info("等待连接建立...")
        time.sleep(1)
        
        # 尝试登录 - 使用正确的 SurrealDB 2.x 根用户身份验证格式
        # 注意：signin 方法不是异步的，不需要 await
        logging.info("尝试使用根用户登录...")
        signin_result = db.signin({
            "username": SURREAL_USER,
            "password": SURREAL_PASS
        })
        logging.info(f"登录成功! 结果: {signin_result}")
        
        # 选择命名空间和数据库
        logging.info(f"选择命名空间和数据库: {SURREAL_NS}, {SURREAL_DB}")
        use_result = db.use(SURREAL_NS, SURREAL_DB)
        logging.info(f"选择成功! 结果: {use_result}")
        
        # 尝试执行简单查询
        logging.info("执行简单查询...")
        result = db.query("SELECT * FROM type::table($table)", {
            "table": "test"
        })
        logging.info(f"查询结果: {result}")
        
        # 关闭连接
        logging.info("关闭连接...")
        db.close()
        logging.info("连接已关闭")
        
    except Exception as e:
        logging.error(f"连接测试失败: {e}")
        raise e

if __name__ == "__main__":
    test_connection()
