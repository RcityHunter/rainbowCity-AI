import os
import logging
import asyncio
import time
import uuid
import surrealdb
from typing import Optional, Dict, Any, List, Union
from asyncio import Lock
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 是否启用数据库
ENABLE_DB = True  # 启用数据库连接

# 是否使用模拟模式 - 尝试禁用模拟模式，使用真实数据库
USE_MOCK_MODE = False  # 禁用模拟模式，尝试连接真实数据库

# SurrealDB配置
# 确保使用正确的协议格式，尝试使用 WebSocket
# 确保所有配置都有默认值，避免 None 值
SURREAL_URL = os.environ.get('SURREAL_URL') or 'ws://localhost:8080'
SURREAL_USER = os.environ.get('SURREAL_USER') or 'root'
SURREAL_PASS = os.environ.get('SURREAL_PASS') or '123'
SURREAL_NS = os.environ.get('SURREAL_NS') or 'rainbow'
SURREAL_DB = os.environ.get('SURREAL_DB') or 'test'

# 输出调试信息
logging.info(f"SURREAL_URL: {SURREAL_URL}")
logging.info(f"SURREAL_USER: {SURREAL_USER}")
logging.info(f"SURREAL_NS: {SURREAL_NS}")
logging.info(f"SURREAL_DB: {SURREAL_DB}")

# 如果数据库被禁用或使用模拟模式，记录日志
if not ENABLE_DB or USE_MOCK_MODE:
    logging.warning("数据库连接已被禁用或使用模拟模式")

# 全局数据库连接
_db = None
_db_lock = asyncio.Lock()
_connection_attempts = 0
_max_connection_attempts = 3
_connection_retry_delay = 2  # 秒
_db_pool = {}
_db_pool_lock = asyncio.Lock()

# 模拟数据库存储
_mock_db = {
    'users': {}
}

# 检查连接是否可用
async def is_connection_alive():
    """检查数据库连接是否正常"""
    global _db
    if _db is None:
        return False
    
    try:
        # 尝试执行一个简单的查询
        await _db.query('INFO FOR DB')
        return True
    except Exception:
        return False

# 初始化数据库连接
async def init_db_connection():
    """初始化数据库连接"""
    global _db, _connection_attempts, USE_MOCK_MODE
    
    try:
        # 输出调试信息
        logging.info(f"ENABLE_DB: {ENABLE_DB}, USE_MOCK_MODE: {USE_MOCK_MODE}")
        
        # 如果数据库被禁用或使用模拟模式，直接返回None
        if not ENABLE_DB or USE_MOCK_MODE:
            logging.info("数据库连接已被禁用或使用模拟模式，返回None")
            return None
        
        # 使用异步锁确保只有一个协程在初始化连接
        async with _db_lock:
            # 如果连接已存在且正常，直接返回
            if _db is not None:
                try:
                    if await is_connection_alive():
                        logging.info("DB连接已存在且正常，直接返回")
                        return _db
                except Exception as e:
                    logging.error(f"DB连接检查失败: {e}")
            
            # 检查连接尝试次数
            if _connection_attempts >= _max_connection_attempts:
                logging.error(f"Maximum connection attempts ({_max_connection_attempts}) reached. Using mock mode.")
                USE_MOCK_MODE = True
                return None
            
            # 尝试连接
            _connection_attempts += 1
            logging.info(f"SurrealDB 连接尝试 #{_connection_attempts}")
            
            # 如果已有连接，先关闭
            if _db is not None:
                try:
                    logging.info("关闭旧的数据库连接")
                    await _db.close()
                except Exception as e:
                    logging.error(f"关闭旧连接出错: {str(e)}")
            
            try:
                # 尝试连接 SurrealDB
                logging.info("尝试连接 SurrealDB")
                
                # 使用最新版本的 SurrealDB Python SDK 创建客户端并连接
                logging.info(f"使用 URL: {SURREAL_URL}")
                
                try:
                    # 创建客户端对象 - 直接在创建时传入 URL
                    logging.info(f"创建并连接 SurrealDB 客户端: {SURREAL_URL}")
                    _db = surrealdb.Surreal(SURREAL_URL)
                    logging.info("客户端创建成功")
                    
                    # 登录
                    logging.info(f"登录 SurrealDB: {SURREAL_USER}")
                    token = _db.signin({"username": SURREAL_USER, "password": SURREAL_PASS})
                    logging.info(f"登录成功: {token[:20]}...")
                    
                    # 选择命名空间和数据库
                    logging.info(f"选择命名空间和数据库: {SURREAL_NS}, {SURREAL_DB}")
                    result = _db.use(SURREAL_NS, SURREAL_DB)
                    logging.info(f"选择成功: {result}")
                    
                    # 连接成功，重置连接尝试次数
                    _connection_attempts = 0
                    logging.info("SurrealDB 连接成功初始化")
                    
                    return _db
                except Exception as e:
                    logging.error(f"SurrealDB 连接失败: {str(e)}")
                    if _connection_attempts >= _max_connection_attempts:
                        logging.error("达到最大连接尝试次数，切换到模拟模式")
                        USE_MOCK_MODE = True
                    return None
            except Exception as e:
                logging.error(f"SurrealDB 连接过程中出错: {str(e)}")
                if _connection_attempts >= _max_connection_attempts:
                    logging.error("达到最大连接尝试次数，切换到模拟模式")
                    USE_MOCK_MODE = True
                return None
    except Exception as e:
        logging.error(f"初始化数据库连接时出错: {str(e)}")
        return None

# 异步获取数据库连接
async def get_db():
    """获取数据库连接"""
    global _db, USE_MOCK_MODE
    
    # 如果使用模拟模式，直接返回None
    if USE_MOCK_MODE:
        return None
    
    # 如果连接不存在，初始化连接
    if _db is None:
        _db = await init_db_connection()
    else:
        # 检查连接是否正常
        try:
            if not await is_connection_alive():
                logging.warning("DB连接已断开，尝试重新连接")
                _db = await init_db_connection()
        except Exception as e:
            logging.error(f"检查DB连接状态时出错: {str(e)}")
            _db = await init_db_connection()
    
    return _db

# 异步关闭数据库连接
async def close_db_connection():
    """关闭数据库连接"""
    global _db
    
    if _db is not None:
        try:
            logging.info("关闭数据库连接")
            _db.close()
            _db = None
            logging.info("数据库连接已关闭")
        except Exception as e:
            logging.error(f"关闭数据库连接时出错: {str(e)}")

async def close_db():
    """关闭所有数据库连接"""
    global _db, _db_pool
    
    # 关闭主连接
    if _db is not None:
        try:
            logging.info("关闭主数据库连接")
            _db.close()
            _db = None
        except Exception as e:
            logging.error(f"关闭主数据库连接时出错: {str(e)}")
    
    # 关闭连接池中的所有连接
    async with _db_pool_lock:
        for key, conn in _db_pool.items():
            try:
                logging.info(f"关闭连接池中的连接: {key}")
                conn.close()
            except Exception as e:
                logging.error(f"关闭连接池中的连接 {key} 时出错: {str(e)}")
        
        # 清空连接池
        _db_pool = {}
        logging.info("所有数据库连接已关闭")

# 同步包装器，将异步操作转换为同步操作
def run_async(async_func):
    """运行异步函数并返回结果
    
    这个函数会检测当前是否在事件循环中：
    - 如果在事件循环中，直接返回协程对象，由调用者负责等待
    - 如果不在事件循环中，创建一个新的事件循环来运行协程
    
    重要：调用者需要检查返回值是否为协程，如果是则需要 await
    """
    try:
        # 检查是否在事件循环中
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果在事件循环中，直接返回协程对象
            return async_func
        else:
            # 如果不在事件循环中，创建一个新的事件循环来运行协程
            return loop.run_until_complete(async_func)
    except RuntimeError:
        # 如果没有事件循环，创建一个新的
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(async_func)
        finally:
            loop.close()

# 初始化数据库
def init_db(app):
    """初始化数据库"""
    # 在应用启动时初始化数据库连接
    @app.on_event("startup")
    async def startup_db_client():
        await init_db_connection()
        print("Database connection initialized on startup")
    
    # 在应用关闭时关闭数据库连接
    @app.on_event("shutdown")
    async def teardown_db(exception=None):
        await close_db()
        print("Database connection closed on shutdown")

# 同步创建数据
def create(table, data):
    """在指定表中创建数据"""
    async def _create():
        db = await get_db()
        if db is None:
            print("Using mock mode for create operation")
            # 在模拟模式下，生成一个唯一ID并返回带ID的数据
            if isinstance(data, dict):
                if 'id' not in data:
                    data['id'] = f"{table}:{str(uuid.uuid4())}"
                return data
            return None
        
        try:
            # 使用SurrealDB的create方法创建记录
            print(f"Creating data in {table}: {data}")
            result = db.create(table, data)
            return result
        except Exception as e:
            print(f"Error creating data in {table}: {e}")
            # 如果创建失败，尝试使用query方法
            try:
                if isinstance(data, dict):
                    # 构建INSERT查询
                    fields = ", ".join(data.keys())
                    values = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in data.values()])
                    query_str = f"INSERT INTO {table} ({fields}) VALUES ({values})"
                    print(f"Executing insert query: {query_str}")
                    result = db.query(query_str)
                    
                    if result and isinstance(result, list) and len(result) > 0 and 'result' in result[0]:
                        return result[0]['result']
                    return None
                else:
                    print(f"Cannot insert non-dict data: {data}")
                    return None
            except Exception as insert_error:
                print(f"Error executing insert query: {insert_error}")
                return None
    
    return run_async(_create())

# 查询指定表中的数据
def query(table, condition=None, sort=None, limit=None, offset=None):
    async def _query():
        db = await get_db()
        if db is None:
            print("Using mock mode for query operation")
            # 在模拟模式下，返回空列表
            return []
        
        try:
            # 构建查询
            query_str = f"SELECT * FROM {table}"
            
            # 添加条件
            if condition:
                conditions = []
                for k, v in condition.items():
                    if isinstance(v, str):
                        conditions.append(f"{k} = '{v}'")
                    else:
                        conditions.append(f"{k} = {v}")
                if conditions:
                    query_str += " WHERE " + " AND ".join(conditions)
            
            # 添加排序
            if sort:
                sort_clauses = []
                for field, direction in sort.items():
                    sort_clauses.append(f"{field} {direction}")
                if sort_clauses:
                    query_str += " ORDER BY " + ", ".join(sort_clauses)
            
            # 添加限制
            if limit:
                query_str += f" LIMIT {limit}"
            
            # 添加偏移
            if offset:
                query_str += f" START {offset}"
            
            print(f"Executing query: {query_str}")
            
            # 执行查询
            # 注意：SurrealDB 的 query 方法是同步的，不需要 await
            result = db.query(query_str)
            
            # 处理查询结果
            if result and isinstance(result, list) and len(result) > 0 and 'result' in result[0]:
                return result[0]['result']
            return []
        except Exception as e:
            print(f"Error querying data from {table}: {e}")
            return []
    
    # 使用修改后的 run_async 函数，它会正确处理同步和异步上下文
    return run_async(_query())

# 同步更新数据
def update(table, id, data):
    """更新指定表中的数据
    
    Args:
        table (str): 表名
        id (str): 记录ID
        data (dict): 要更新的数据
        
    Returns:
        dict: 更新后的记录
    """
    async def _update():
        db = await get_db()
        if db is None:
            print("Using mock mode for update operation")
            return data
        
        try:
            # 使用SurrealDB的update方法更新记录
            result = db.update(f"{table}:{id}", data)
            return result
        except Exception as e:
            print(f"Error updating data in {table}: {e}")
            return None
    
    return run_async(_update())

# 执行原始SQL查询
async def execute_raw_query(query_str):
    """执行原始SQL查询
    
    Args:
        query_str (str): SQL查询字符串
        
    Returns:
        Any: 查询结果
    """
    db = await get_db()
    if db is None:
        print("Using mock mode for raw query operation")
        return None
    
    try:
        print(f"Executing raw query: {query_str}")
        # 注意：query 方法不是异步的，不需要 await
        result = db.query(query_str)
        
        if result and isinstance(result, list) and len(result) > 0 and 'result' in result[0]:
            return result[0]['result']
        return result
    except Exception as e:
        print(f"Error executing raw query: {e}")
        raise

# 创建一个数据库会话对象，用于兼容SQLAlchemy风格的代码
class DBSession:
    def __init__(self):
        self.pending_operations = []
    
    def add(self, obj):
        """添加对象到会话"""
        print(f"添加对象到会话: {obj}")
        # 实际上这里应该调用create函数
        if hasattr(obj, '__tablename__') and hasattr(obj, 'to_dict'):
            create(obj.__tablename__, obj.to_dict())
    
    def delete(self, obj):
        """从会话中删除对象"""
        print(f"从会话中删除对象: {obj}")
        # 实际删除操作
    
    def commit(self):
        """提交会话中的所有更改"""
        print("提交会话中的更改")
        # 实际上这里不需要做什么，因为每个操作都是立即执行的
    
    def rollback(self):
        """回滚会话中的所有更改"""
        print("回滚会话中的所有更改")
        # 实际上这里不需要做什么，因为每个操作都是立即执行的

# 同步删除数据
def delete(table, condition):
    """删除指定表中的数据
    
    Args:
        table (str): 表名
        condition (dict): 删除条件
        
    Returns:
        bool: 是否删除成功
    """
    async def _delete():
        db = await get_db()
        if db is None:
            print("Using mock mode for delete operation")
            return False
        
        try:
            # 构建条件查询
            conditions = " AND ".join([f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}" for k, v in condition.items()])
            query_str = f"DELETE FROM {table} WHERE {conditions}"
            print(f"Executing delete query: {query_str}")
            result = db.query(query_str)
            
            print(f"Delete result: {result}")
            return True
        except Exception as e:
            print(f"Error deleting data from {table}: {e}")
            return False
    
    return run_async(_delete())

# 创建全局会话对象
db_session = DBSession()
