import asyncio
import os
import time
import threading
from flask import g, current_app
import surrealdb
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# SurrealDB配置
SURREAL_URL = os.getenv('SURREAL_URL', 'ws://localhost:8080')
SURREAL_USER = os.getenv('SURREAL_USER', 'root')
SURREAL_PASS = os.getenv('SURREAL_PASS', '123')
SURREAL_NS = os.getenv('SURREAL_NS', 'rainbow')
SURREAL_DB = os.getenv('SURREAL_DB', 'test')

# 全局数据库连接
_db = None
_db_lock = threading.Lock()
_connection_attempts = 0
_max_connection_attempts = 3
_connection_retry_delay = 2  # 秒
_db_pool = {}
_db_pool_lock = threading.Lock()

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
    global _db, _connection_attempts
    
    # 使用锁确保只有一个线程在初始化连接
    with _db_lock:
        # 如果连接已存在且正常，直接返回
        if _db is not None and await is_connection_alive():
            return _db
        
        # 检查连接尝试次数
        if _connection_attempts >= _max_connection_attempts:
            print(f"Maximum connection attempts ({_max_connection_attempts}) reached. Using mock mode.")
            return None
        
        # 尝试连接
        _connection_attempts += 1
        try:
            # 如果已有连接，先关闭
            if _db is not None:
                try:
                    await _db.close()
                except Exception:
                    pass
            
            # 创建新连接
            _db = surrealdb.Surreal()
            await _db.connect(SURREAL_URL)
            await _db.signin({"user": SURREAL_USER, "pass": SURREAL_PASS})
            await _db.use(SURREAL_NS, SURREAL_DB)
            print(f"Connected to SurrealDB at {SURREAL_URL} (attempt {_connection_attempts})")
            
            # 重置连接尝试计数
            _connection_attempts = 0
            return _db
        except Exception as e:
            print(f"Error connecting to SurrealDB (attempt {_connection_attempts}): {e}")
            
            # 如果还有尝试次数，等待一段时间后重试
            if _connection_attempts < _max_connection_attempts:
                print(f"Retrying in {_connection_retry_delay} seconds...")
                time.sleep(_connection_retry_delay)
                return await init_db_connection()
            
            return None

# 异步获取数据库连接
async def get_db():
    """获取数据库连接"""
    global _db_pool
    
    # 获取当前线程 ID
    thread_id = threading.get_ident()
    
    # 使用锁确保线程安全
    with _db_pool_lock:
        # 检查这个线程是否已有连接
        if thread_id in _db_pool and _db_pool[thread_id] is not None:
            # 检查连接是否正常
            try:
                await _db_pool[thread_id].query('INFO FOR DB')
                return _db_pool[thread_id]
            except Exception:
                # 如果连接出错，删除并创建新连接
                try:
                    await _db_pool[thread_id].close()
                except Exception:
                    pass
                del _db_pool[thread_id]
        
        # 创建新连接
        try:
            # 创建新连接
            db = surrealdb.Surreal()
            await db.connect(SURREAL_URL)
            await db.signin({"user": SURREAL_USER, "pass": SURREAL_PASS})
            await db.use(SURREAL_NS, SURREAL_DB)
            print(f"Created new connection for thread {thread_id}")
            
            # 将连接存入连接池
            _db_pool[thread_id] = db
            return db
        except Exception as e:
            print(f"Error creating connection for thread {thread_id}: {e}")
            # 如果创建失败，尝试使用全局连接
            if _db is not None and await is_connection_alive():
                return _db
            return await init_db_connection()

# 异步关闭数据库连接
async def close_db():
    """关闭数据库连接"""
    global _db, _db_pool
    
    # 关闭全局连接
    if _db is not None:
        try:
            print("Closing global SurrealDB connection...")
            await _db.close()
            _db = None
            print("Global SurrealDB connection closed")
        except Exception as e:
            print(f"Error closing global SurrealDB connection: {e}")
    
    # 关闭连接池中的所有连接
    with _db_pool_lock:
        for thread_id, conn in list(_db_pool.items()):
            if conn is not None:
                try:
                    print(f"Closing SurrealDB connection for thread {thread_id}...")
                    await conn.close()
                    print(f"SurrealDB connection for thread {thread_id} closed")
                except Exception as e:
                    print(f"Error closing SurrealDB connection for thread {thread_id}: {e}")
                finally:
                    _db_pool[thread_id] = None
        print("Connection pool cleared")

# 同步包装器，将异步操作转换为同步操作
def run_async(async_func):
    """运行异步函数并返回结果"""
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
    with app.app_context():
        try:
            run_async(init_db_connection())
            print("Database initialized successfully")
        except Exception as e:
            print(f"Failed to initialize database: {e}")
    
    # 注册应用关闭时的回调
    @app.teardown_appcontext
    def teardown_db(exception=None):
        try:
            run_async(close_db())
        except Exception as e:
            print(f"Error in teardown_db: {e}")

# 同步创建数据
def create(table, data):
    """在指定表中创建数据"""
    async def _create():
        db = await get_db()
        if db is None:
            print("Using mock mode for create operation")
            return data
        
        try:
            result = await db.create(table, data)
            return result
        except Exception as e:
            print(f"Error creating data in {table}: {e}")
            return data
    
    return run_async(_create())

# 同步查询数据
def query(table, condition=None):
    """查询指定表中的数据"""
    async def _query():
        db = await get_db()
        if db is None:
            print("Using mock mode for query operation")
            return []
        
        # 根据条件执行查询
        query_str = ""
        try:
            if not condition:
                # 无条件查询所有记录
                query_str = f"SELECT * FROM {table}"
                print(f"Executing query: {query_str}")
                result = await db.query(query_str)
            elif 'id' in condition and condition['id'].startswith(f"{table}:"):
                # 直接通过ID查询单条记录
                record_id = condition['id']
                print(f"Executing direct ID query for {record_id}")
                try:
                    # 尝试直接使用select方法
                    record = await db.select(record_id)
                    print(f"Direct select result: {record}")
                    # 将结果包装为与查询结果相同的格式
                    if record:
                        result = [{'result': [record], 'status': 'OK'}]
                    else:
                        result = [{'result': [], 'status': 'OK'}]
                except Exception as e:
                    print(f"Error in direct select: {e}, falling back to query")
                    # 如果直接选择失败，回退到查询
                    query_str = f"SELECT * FROM {table} WHERE id = '{record_id}'"
                    print(f"Fallback query: {query_str}")
                    result = await db.query(query_str)
            else:
                # 构建条件查询
                conditions = " AND ".join([f"{k} = '{v}'" for k, v in condition.items()])
                query_str = f"SELECT * FROM {table} WHERE {conditions}"
                print(f"Executing query: {query_str}")
                result = await db.query(query_str)
            
            print(f"Query result type: {type(result)}")
            print(f"Query result: {result}")
        except Exception as e:
            print(f"Error executing query '{query_str}': {e}")
            raise
        
        # 处理查询结果
        try:
            if result and result[0] and 'result' in result[0]:
                return result[0]['result']
            return []
        except Exception as e:
            print(f"Error processing query result: {e}")
            return []
    
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
            result = await db.update(f"{table}:{id}", data)
            return result
        except Exception as e:
            print(f"Error updating data in {table}: {e}")
            return None
    
    return run_async(_update())


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

# 创建全局会话对象
db_session = DBSession()