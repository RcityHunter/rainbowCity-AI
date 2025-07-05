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
        logging.warning("数据库连接不存在")
        return False
    
    try:
        # 尝试执行一个简单的查询
        result = _db.query('INFO FOR DB')
        if result:
            logging.info("数据库连接测试成功")
            return True
        logging.warning("数据库连接测试返回空结果")
        return False
    except Exception as e:
        logging.warning(f"数据库连接测试失败: {str(e)}")
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
                    # SurrealDB的close方法不是异步的，不需要await
                    _db.close()
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

# 获取数据库连接
async def get_db():
    """获取数据库连接，并处理自动重连"""
    global _db, USE_MOCK_MODE
    
    # 如果使用模拟模式，直接返回None
    if USE_MOCK_MODE:
        return None
    
    # 使用锁确保只有一个协程在检查和初始化连接
    async with _db_lock:
        # 如果连接不存在，初始化连接
        if _db is None:
            logging.info("数据库连接不存在，初始化新连接")
            await init_db_connection()
            if _db is None:
                logging.error("无法初始化数据库连接，返回None")
                return None
        
        # 检查连接是否可用
        try:
            if not await is_connection_alive():
                logging.warning("DB连接已断开，尝试重新连接")
                # 关闭旧连接
                try:
                    if _db is not None:
                        _db.close()
                except Exception as close_error:
                    logging.error(f"关闭旧连接出错: {str(close_error)}")
                
                # 创建新连接
                await init_db_connection()
                
                # 再次检查连接是否成功
                if _db is None or not await is_connection_alive():
                    logging.error("重新连接失败，返回None")
                    return None
        except Exception as e:
            logging.error(f"DB连接检查失败: {str(e)}")
            # 尝试重新初始化连接
            await init_db_connection()
            # 如果连接仍然失败，返回None
            if _db is None:
                logging.error("重新连接失败，返回None")
                return None
    
    return _db

# 异步关闭数据库连接
async def close_db_connection():
    """关闭数据库连接"""
    global _db
    
    if _db is not None:
        try:
            logging.info("关闭数据库连接")
            # SurrealDB的close方法不是异步的，不需要await
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
def create(table, data, max_retries=2):
    """在指定表中创建数据
    
    Args:
        table (str): 表名
        data (dict): 要创建的数据
        max_retries (int): 最大重试次数
        
    Returns:
        dict: 创建的记录，包含ID
    """
    async def _create(retry_count=0):
        db = await get_db()
        if db is None:
            logging.warning(f"DB连接不可用，无法创建数据到表 {table}")
            # 在模拟模式下，生成一个唯一ID并返回带ID的数据
            if isinstance(data, dict):
                if 'id' not in data:
                    data['id'] = f"{table}:{str(uuid.uuid4())}"
                return data
            return None
        
        try:
            # 使用SurrealDB的create方法创建记录
            logging.info(f"Creating data in {table}: {data}")
            
            # 确保数据是字典
            if not isinstance(data, dict):
                logging.error(f"Cannot create non-dict data: {data}")
                return None
                
            # 创建记录
            result = db.create(table, data)
            logging.info(f"Create result: {result}")
            
            # 确保结果是字典类型
            if result is None:
                logging.warning(f"创建{table}记录返回None")
                return None
            elif isinstance(result, list):
                logging.warning(f"创建{table}记录返回列表而非字典，尝试提取第一个元素")
                if len(result) > 0:
                    result = result[0]  # 取第一个元素
                else:
                    logging.error(f"创建{table}记录返回空列表")
                    return None
            
            # 验证创建结果
            if result:
                # 验证创建是否成功
                verify_query = f"SELECT * FROM {table} WHERE id = '{result.get('id')}'"
                logging.info(f"Verifying creation with query: {verify_query}")
                verify_result = db.query(verify_query)
                
                if verify_result and isinstance(verify_result, list) and len(verify_result) > 0 and 'result' in verify_result[0]:
                    if len(verify_result[0]['result']) > 0:
                        logging.info(f"Successfully verified creation of {table} record with ID {result.get('id')}")
                    else:
                        logging.warning(f"Created {table} record but could not verify it exists")
                
                return result
            else:
                logging.error(f"Create operation returned no result for {table}")
                return None
                
        except Exception as e:
            logging.error(f"Error creating data in {table}: {str(e)}")
            
            # 如果创建失败且未超过最大重试次数，尝试重新连接并重试
            if retry_count < max_retries:
                logging.warning(f"创建数据失败，尝试重新连接并重试，重试次数: {retry_count + 1}/{max_retries}")
                # 强制重新初始化连接
                global _db
                try:
                    if _db is not None:
                        _db.close()
                except Exception:
                    pass
                _db = None
                
                # 等待短暂时间后重试
                await asyncio.sleep(0.5 * (retry_count + 1))
                return await _create(retry_count + 1)
            
            # 如果创建失败，尝试使用原始SQL查询
            try:
                # 构建INSERT查询
                fields = ", ".join(data.keys())
                values_list = []
                for v in data.values():
                    if v is None:
                        values_list.append("NULL")
                    elif isinstance(v, str):
                        # 处理字符串中的引号
                        escaped_v = v.replace("'", "\\'") 
                        values_list.append(f"'{escaped_v}'")
                    elif isinstance(v, (list, dict)):
                        # 将对象和数组转换为JSON字符串
                        import json
                        json_str = json.dumps(v).replace("'", "\\'") 
                        values_list.append(f"'{json_str}'")
                    else:
                        values_list.append(str(v))
                        
                values = ", ".join(values_list)
                query_str = f"INSERT INTO {table} ({fields}) VALUES ({values}) RETURN AFTER"
                logging.info(f"Executing insert query: {query_str}")
                result = db.query(query_str)
                
                if result and isinstance(result, list) and len(result) > 0 and 'result' in result[0]:
                    if len(result[0]['result']) > 0:
                        logging.info(f"Successfully inserted {table} record using SQL")
                        return result[0]['result'][0]
                    else:
                        logging.warning(f"Insert query returned empty result")
                        return None
                else:
                    logging.error(f"Insert query failed: {result}")
                    return None
            except Exception as insert_error:
                logging.error(f"Error executing insert query: {str(insert_error)}")
                return None
    
    return run_async(_create())

# 查询指定表中的数据
def query(table, condition=None, sort=None, limit=None, offset=None, max_retries=2):
    # 检查是否使用了None作为条件值，这会导致SQL语法错误
    if condition:
        # 确保condition是字典类型
        if not isinstance(condition, dict):
            logging.error(f"查询条件必须是字典类型，但收到了 {type(condition)}")
            return []
        condition = {k: v for k, v in condition.items() if v is not None}
        
    async def _query(retry_count=0):
        db = await get_db()
        if db is None:
            logging.warning(f"数据库连接不可用，无法查询表 {table}")
            # 在模拟模式下或连接不可用时，返回空列表
            return []
        
        try:
            # 构建查询
            query_str = f"SELECT * FROM {table}"
            
            # 添加条件
            if condition:
                conditions = []
                for k, v in condition.items():
                    if v is None:
                        # 跳过None值
                        continue
                    elif isinstance(v, str):
                        conditions.append(f"{k} = '{v}'")
                    else:
                        conditions.append(f"{k} = {v}")
                if conditions:
                    query_str += " WHERE " + " AND ".join(conditions)
            
            # 添加排序
            if sort:
                sort_clauses = []
                # 处理不同类型的排序参数
                if isinstance(sort, dict):
                    # 如果是字典类型
                    for field, direction in sort.items():
                        sort_clauses.append(f"{field} {direction}")
                elif isinstance(sort, list):
                    # 如果是列表类型
                    for item in sort:
                        if isinstance(item, tuple) and len(item) == 2:
                            field, direction = item
                            sort_clauses.append(f"{field} {direction}")
                        else:
                            logging.warning(f"排序参数格式不正确: {item}")
                if sort_clauses:
                    query_str += " ORDER BY " + ", ".join(sort_clauses)
            
            # 添加限制
            if limit:
                query_str += f" LIMIT {limit}"
            
            # 添加偏移
            if offset:
                query_str += f" START {offset}"
            
            logging.info(f"Executing query: {query_str}")
            
            # 执行查询
            # 注意：SurrealDB 的 query 方法是同步的，不需要 await
            result = db.query(query_str)
            logging.info(f"查询结果类型: {type(result)}, 内容: {result}")
            
            # 处理查询结果 - 兼容不同版本的SurrealDB SDK返回格式
            if result is None:
                logging.info("查询结果为None")
                return []
            
            # 如果是列表
            if isinstance(result, list):
                # 如果是旧格式，包含'result'键
                if len(result) > 0 and isinstance(result[0], dict) and 'result' in result[0]:
                    result_data = result[0]['result']
                    logging.info(f"旧格式结果，处理后类型: {type(result_data)}")
                    
                    # 确保返回的是列表
                    if result_data is None:
                        return []
                    elif not isinstance(result_data, list):
                        if isinstance(result_data, dict):
                            return [result_data]
                        else:
                            logging.warning(f"查询结果类型异常: {type(result_data)}")
                            return []
                    return result_data
                # 如果是新格式，直接返回列表
                else:
                    logging.info(f"新格式结果，返回 {len(result)} 条记录")
                    return result
            # 如果是字典类型，将其包装为列表
            elif isinstance(result, dict):
                logging.info(f"字典类型结果，包装为列表")
                return [result]
            # 如果是其他类型，返回空列表
            else:
                logging.warning(f"意外类型的查询结果: {type(result)}")
                return []
            
            logging.info("查询成功，但没有找到匹配的记录")
            return []
        except Exception as e:
            logging.error(f"查询表 {table} 时出错: {str(e)}")
            
            # 如果是连接错误且未超过最大重试次数，尝试重新连接并重试
            if retry_count < max_retries:
                logging.warning(f"尝试重新连接并重试查询，重试次数: {retry_count + 1}/{max_retries}")
                # 强制重新初始化连接
                global _db
                try:
                    if _db is not None:
                        _db.close()
                except Exception:
                    pass
                _db = None
                
                # 等待短暂时间后重试
                await asyncio.sleep(0.5 * (retry_count + 1))
                return await _query(retry_count + 1)
            
            return []
    
    # 使用修改后的 run_async 函数，它会正确处理同步和异步上下文
    return run_async(_query())

# 同步更新数据
def update(table, id, data):
    """更新指定表中的数据
    
    Args:
        table (str): 表名
        id (str): 记录ID，可能包含表名前缀
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
            # 处理ID格式，创建一个局部变量以避免作用域问题
            record_id = id
            
            # 处理RecordID类型
            from surrealdb.data.types.record_id import RecordID
            if isinstance(record_id, RecordID):
                print(f"检测到RecordID类型: {record_id}")
                # 使用RecordID的table_name和record_id属性
                if hasattr(record_id, 'table_name') and hasattr(record_id, 'record_id'):
                    if record_id.table_name == table:
                        # 如果表名匹配，直接使用record_id
                        print(f"使用RecordID的record_id属性: {record_id.record_id}")
                        record_id = record_id.record_id
                    else:
                        # 如果表名不匹配，转换为字符串并提取ID部分
                        record_id_str = str(record_id)
                        print(f"将RecordID转换为字符串: {record_id_str}")
                        if ':' in record_id_str:
                            table_prefix, pure_id = record_id_str.split(':', 1)
                            record_id = pure_id
                else:
                    # 如果RecordID没有预期的属性，尝试将其转换为字符串
                    try:
                        record_id_str = str(record_id)
                        print(f"将RecordID转换为字符串: {record_id_str}")
                        if ':' in record_id_str:
                            if record_id_str.startswith(f"{table}:"):
                                _, pure_id = record_id_str.split(':', 1)
                                record_id = pure_id
                            else:
                                # 处理特殊情况：当ID是类似 {'id': RecordID(table_name=memory, record_id=xxx)} 的字典
                                if isinstance(id, dict) and 'id' in id and isinstance(id['id'], RecordID):
                                    record_id = id['id'].record_id
                                    print(f"从字典中提取RecordID: {record_id}")
                    except Exception as e:
                        print(f"处理RecordID时出错: {e}")
            # 处理字典类型的ID，特别是内存记录
            elif isinstance(record_id, dict) and 'id' in record_id:
                print(f"检测到字典类型ID: {record_id}")
                if isinstance(record_id['id'], RecordID):
                    # 如果字典中的id是RecordID类型
                    inner_id = record_id['id']
                    if hasattr(inner_id, 'record_id'):
                        record_id = inner_id.record_id
                        print(f"从字典中提取RecordID: {record_id}")
                    else:
                        record_id = str(inner_id).split(':', 1)[1] if ':' in str(inner_id) else str(inner_id)
                        print(f"从字典中提取并处理ID: {record_id}")
                else:
                    # 如果字典中的id是字符串或其他类型
                    record_id = str(record_id['id'])
                    if ':' in record_id and record_id.startswith(f"{table}:"):
                        record_id = record_id.split(':', 1)[1]
                    print(f"从字典中提取ID: {record_id}")
            # 处理字符串类型的ID
            elif isinstance(record_id, str) and ':' in record_id:
                # 如果ID已经包含表名前缀，则提取纯准ID
                prefix, pure_id = record_id.split(':', 1)
                if prefix == table:
                    # 如果前缀就是表名，直接使用纯准ID
                    print(f"ID已包含表名前缀，提取纯准ID: {pure_id}")
                    record_id = pure_id
            
            # 使用SurrealDB的update方法更新记录
            full_record_id = f"{table}:{record_id}"
            print(f"更新记录: {full_record_id}")
            
            # 为了避免日志过大，不打印完整的数据（特别是嵌入向量）
            if 'embedding' in data and isinstance(data['embedding'], list) and len(data['embedding']) > 10:
                log_data = data.copy()
                log_data['embedding'] = f"[{data['embedding'][0]}, {data['embedding'][1]}, ... (共{len(data['embedding'])}个元素)]"
                print(f"数据(简化): {log_data}")
            else:
                print(f"数据: {data}")
                
            try:
                result = db.update(full_record_id, data)
                return result
            except ValueError as ve:
                # 处理"too many values to unpack"错误
                if "too many values to unpack" in str(ve):
                    print(f"处理值解包错误: {ve}")
                    # 尝试使用另一种方式更新
                    try:
                        # 对于嵌入向量，我们需要特殊处理
                        if 'embedding' in data and isinstance(data['embedding'], list):
                            # 创建不包含嵌入向量的数据副本
                            data_without_embedding = {k: v for k, v in data.items() if k != 'embedding'}
                            # 先更新其他字段
                            if data_without_embedding:
                                result = db.update(full_record_id, data_without_embedding)
                                print(f"成功更新非嵌入字段: {list(data_without_embedding.keys())}")
                            
                            # 然后单独处理嵌入向量 - 使用原始查询
                            try:
                                # 使用参数化查询避免SQL注入和格式问题
                                update_embedding_query = f"UPDATE {full_record_id} SET embedding = $embedding"
                                params = {"embedding": data['embedding']}
                                print(f"尝试使用参数化查询更新嵌入向量")
                                result = db.query(update_embedding_query, params)
                                print(f"嵌入向量更新成功")
                                return data  # 返回原始数据作为结果
                            except Exception as embed_error:
                                print(f"嵌入向量更新失败: {embed_error}")
                                # 如果嵌入向量更新失败，至少返回已更新的其他字段
                                return data_without_embedding
                        else:
                            # 对于非嵌入向量数据，使用常规SQL更新
                            update_query = f"UPDATE {full_record_id} SET "
                            updates = []
                            for key, value in data.items():
                                if key != 'id':  # 跳过ID字段
                                    if isinstance(value, str):
                                        # 转义字符串中的单引号
                                        escaped_value = value.replace("'", "\\'") 
                                        updates.append(f"{key} = '{escaped_value}'")
                                    elif value is None:
                                        updates.append(f"{key} = NULL")
                                    else:
                                        updates.append(f"{key} = {value}")
                            
                            if updates:
                                update_query += ", ".join(updates)
                                print(f"尝试使用SQL更新: {update_query}")
                                result = db.query(update_query)
                                return data  # 返回原始数据作为结果
                    except Exception as sql_error:
                        print(f"SQL更新失败: {sql_error}")
                raise  # 重新抛出原始错误
        except Exception as e:
            print(f"Error updating data in {table}: {e}")
            return None
    
    return run_async(_update())

# 执行原始SQL查询
async def execute_raw_query(query_str, max_retries=2):
    """执行原始SQL查询
    
    Args:
        query_str (str): SQL查询字符串
        max_retries (int): 最大重试次数
        
    Returns:
        Any: 查询结果
    """
    async def _execute_query(retry_count=0):
        db = await get_db()
        if db is None:
            logging.warning("DB连接不可用，无法执行原始SQL查询")
            return None
        
        try:
            logging.info(f"Executing raw query: {query_str}")
            # 注意：query 方法不是异步的，不需要 await
            result = db.query(query_str)
            logging.info(f"原始SQL查询执行成功，结果类型: {type(result)}, 结果: {result}")
            
            # 处理查询结果 - 兼容不同版本的SurrealDB SDK返回格式
            # 注意：不要对结果进行额外处理，直接返回原始结果
            # 调用者应该处理不同格式的结果
            return result
            
        except Exception as e:
            logging.error(f"Error executing raw query: {str(e)}")
            
            # 如果是连接错误且未超过最大重试次数，尝试重新连接并重试
            if retry_count < max_retries:
                logging.warning(f"原始SQL查询失败，尝试重新连接并重试，重试次数: {retry_count + 1}/{max_retries}")
                # 强制重新初始化连接
                global _db
                try:
                    if _db is not None:
                        _db.close()
                except Exception:
                    pass
                _db = None
                
                # 等待短暂时间后重试
                await asyncio.sleep(0.5 * (retry_count + 1))
                return await _execute_query(retry_count + 1)
            
            # 超过重试次数，返回空结果
            return None
    
    return await _execute_query()

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
