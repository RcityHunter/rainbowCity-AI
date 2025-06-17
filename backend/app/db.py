import asyncio
import os
import time
import surrealdb
from dotenv import load_dotenv
import logging

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
_db_lock = asyncio.Lock()
_connection_attempts = 0
_max_connection_attempts = 3
_connection_retry_delay = 2  # 秒
_db_pool = {}
_db_pool_lock = asyncio.Lock()

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
    
    # 使用异步锁确保只有一个协程在初始化连接
    async with _db_lock:
        # 如果连接已存在且正常，直接返回
        if _db is not None and await is_connection_alive():
            logging.info("DB连接已存在且正常，直接返回")
            return _db
        
        # 检查连接尝试次数
        if _connection_attempts >= _max_connection_attempts:
            logging.error(f"Maximum connection attempts ({_max_connection_attempts}) reached. Using mock mode.")
            return None
        
        # 尝试连接
        _connection_attempts += 1
        try:
            # 如果已有连接，先关闭
            if _db is not None:
                try:
                    logging.info("关闭旧的数据库连接")
                    await _db.close()
                except Exception as e:
                    logging.error(f"关闭旧连接出错: {str(e)}")
            
            # 创建新连接
            logging.info(f"尝试创建新的数据库连接: {SURREAL_URL}")
            _db = surrealdb.Surreal()
            await _db.connect(SURREAL_URL)
            await _db.signin({"user": SURREAL_USER, "pass": SURREAL_PASS})
            await _db.use(SURREAL_NS, SURREAL_DB)
            logging.info(f"Connected to SurrealDB at {SURREAL_URL} (attempt {_connection_attempts})")
            
            # 重置连接尝试计数
            _connection_attempts = 0
            return _db
        except Exception as e:
            logging.error(f"Error connecting to SurrealDB (attempt {_connection_attempts}): {e}")
            
            # 如果还有尝试次数，等待一段时间后重试
            if _connection_attempts < _max_connection_attempts:
                logging.info(f"Retrying in {_connection_retry_delay} seconds...")
                await asyncio.sleep(_connection_retry_delay)  # 使用异步睡眠而不是阻塞睡眠
                return await init_db_connection()
            
            return None

# 异步获取数据库连接
async def get_db():
    """获取数据库连接"""
    global _db_pool
    
    # 获取当前任务 ID作为唯一标识符
    task_id = id(asyncio.current_task())
    
    # 使用异步锁确保并发安全
    async with _db_pool_lock:
        # 检查这个任务是否已有连接
        if task_id in _db_pool and _db_pool[task_id] is not None:
            # 检查连接是否正常
            try:
                await _db_pool[task_id].query('INFO FOR DB')
                logging.info(f"使用现有连接: task_id={task_id}")
                return _db_pool[task_id]
            except Exception as e:
                # 如果连接出错，删除并创建新连接
                logging.error(f"现有连接失效: task_id={task_id}, error={str(e)}")
                try:
                    await _db_pool[task_id].close()
                except Exception as e:
                    logging.error(f"关闭失效连接出错: {str(e)}")
                del _db_pool[task_id]
        
        # 创建新连接
        try:
            # 创建新连接
            logging.info(f"为任务 {task_id} 创建新连接")
            db = surrealdb.Surreal()
            await db.connect(SURREAL_URL)
            await db.signin({"user": SURREAL_USER, "pass": SURREAL_PASS})
            await db.use(SURREAL_NS, SURREAL_DB)
            logging.info(f"Created new connection for task {task_id}")
            
            # 将连接存入连接池
            _db_pool[task_id] = db
            return db
        except Exception as e:
            logging.error(f"Error creating database connection: {e}")
            return None

# 异步关闭数据库连接
async def close_db():
    """关闭数据库连接"""
    global _db, _db_pool
    
    # 关闭全局连接
    if _db is not None:
        try:
            await _db.close()
            logging.info("Closed global database connection")
        except Exception as e:
            logging.error(f"Error closing global database connection: {e}")
        finally:
            _db = None
    
    # 关闭连接池中的所有连接
    async with _db_pool_lock:
        for task_id, db in list(_db_pool.items()):
            try:
                await db.close()
                logging.info(f"Closed database connection for task {task_id}")
            except Exception as e:
                logging.error(f"Error closing database connection for task {task_id}: {e}")
            finally:
                del _db_pool[task_id]
        
        # 清空连接池
        _db_pool.clear()
    
    logging.info("All database connections closed")
    
    # 强制进行垃圾回收
    import gc
    gc.collect()
    logging.info("Garbage collection performed after closing DB connections")

# 同步包装器，将异步操作转换为同步操作
def run_async(async_func):
    """运行异步函数并返回结果"""
    try:
        # Check if we're already in an event loop
        loop = asyncio.get_running_loop()
        # If we're in an event loop, we can't create a new one
        # Instead, we should just return the coroutine directly
        # The caller is responsible for awaiting it
        return async_func
    except RuntimeError:
        # If we're not in an event loop, create a new one
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
        import logging
        
        # 记录创建前的数据
        logging.info(f"DB Create - Table: {table}")
        logging.info(f"DB Create - Data before: {data}")
        if 'password_hash' in data:
            logging.info(f"DB Create - Password hash before: {data['password_hash']}")
            logging.info(f"DB Create - Password hash type: {type(data['password_hash'])}")
            logging.info(f"DB Create - Password hash length: {len(data['password_hash'])}")
        
        db = await get_db()
        if db is None:
            print("Using mock mode for create operation")
            return data
        
        try:
            # 执行创建操作
            result = await db.create(table, data)
            
            # 记录创建后的结果
            logging.info(f"DB Create - Result type: {type(result)}")
            logging.info(f"DB Create - Result: {result}")
            if result and isinstance(result, dict) and 'password_hash' in result:
                logging.info(f"DB Create - Password hash after: {result['password_hash']}")
                logging.info(f"DB Create - Password hash type after: {type(result['password_hash'])}")
                logging.info(f"DB Create - Password hash length after: {len(result['password_hash'])}")
            
            return result
        except Exception as e:
            logging.error(f"Error creating data in {table}: {e}")
            return data
    
    return run_async(_create())

# 同步查询数据
def query(table, condition=None, sort=None, limit=None, offset=None):
    """查询指定表中的数据"""
    async def _query():
        import time
        start_time = time.time()
        db = await get_db()
        if db is None:
            print("Using mock mode for query operation")
            return []
        
        # 根据条件执行查询
        query_str = ""
        params = {}
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
                    # 如果直接选择失败，回退到查询 - 使用参数化查询
                    query_str = f"SELECT * FROM {table} WHERE id = $id"
                    params = {"id": record_id}
                    print(f"Fallback query: {query_str} with params: {params}")
                    result = await db.query(query_str, params)
            else:
                # 构建条件查询 - 使用参数化查询
                conditions = []
                for idx, (k, v) in enumerate(condition.items()):
                    param_name = f"p{idx}"
                    conditions.append(f"{k} = ${param_name}")
                    params[param_name] = v
                
                conditions_str = " AND ".join(conditions)
                query_str = f"SELECT * FROM {table} WHERE {conditions_str}"
                
                # 添加排序
                if sort:
                    sort_str = ", ".join([f"{field} {order}" for field, order in sort])
                    query_str += f" ORDER BY {sort_str}"
                
                # 添加分页
                if limit is not None:
                    query_str += f" LIMIT {limit}"
                    if offset is not None:
                        query_str += f" START {offset}"
                
                print(f"Executing query: {query_str} with params: {params}")
                result = await db.query(query_str, params)
            
            query_time = time.time() - start_time
            if query_time > 1.0:  # 记录执行时间超过1秒的查询
                print(f"SLOW QUERY WARNING: Query took {query_time:.2f} seconds: {query_str} with params: {params}")
            
            print(f"Query result type: {type(result)}")
            print(f"Query returned in {query_time:.2f} seconds")
        except Exception as e:
            import traceback
            print(f"Error executing query '{query_str}': {e}")
            print(f"Query error details: {traceback.format_exc()}")
            raise
        
        # 处理查询结果
        try:
            if result and isinstance(result, list) and len(result) > 0 and 'result' in result[0]:
                data = result[0]['result']
                print(f"Query returned {len(data)} results in {query_time:.2f} seconds")
                return data
            print(f"Query returned empty result in {query_time:.2f} seconds")
            return []
        except Exception as e:
            import traceback
            print(f"Error processing query result: {e}")
            print(f"Error details: {traceback.format_exc()}")
            return []
    
    result_or_coroutine = run_async(_query())
    
    # Check if the result is a coroutine (when called from an async context)
    if asyncio.iscoroutine(result_or_coroutine):
        # If it's a coroutine, we need to mark this function as async
        # This is a bit of a hack, but it works for FastAPI routes
        # The caller must await this result
        return result_or_coroutine
    else:
        # If it's not a coroutine, it's already been executed and we can return it directly
        return result_or_coroutine

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
        result = await db.query(query_str)
        
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
            conditions = " AND ".join([f"{k} = '{v}'" for k, v in condition.items()])
            query_str = f"DELETE FROM {table} WHERE {conditions}"
            print(f"Executing delete query: {query_str}")
            result = await db.query(query_str)
            
            print(f"Delete result: {result}")
            return True
        except Exception as e:
            print(f"Error deleting data from {table}: {e}")
            return False
    
    return run_async(_delete())

# 创建全局会话对象
db_session = DBSession()