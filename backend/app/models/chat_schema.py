"""
聊天和消息的数据模型定义
"""

# SurrealDB 聊天表定义
CHAT_SCHEMA = """
-- 聊天表定义
DEFINE TABLE chat SCHEMAFULL;

DEFINE FIELD user_id ON chat TYPE string ASSERT $value != NONE;
DEFINE FIELD title ON chat TYPE string ASSERT $value != NONE; -- 标题不能为空
DEFINE FIELD last_message_at ON chat TYPE datetime;
DEFINE FIELD last_message_preview ON chat TYPE string;
DEFINE FIELD created_at ON chat TYPE datetime DEFAULT time::now();
DEFINE FIELD model_used ON chat TYPE string; -- 例如 'gemini-pro'
DEFINE FIELD is_archived ON chat TYPE bool DEFAULT false;
DEFINE FIELD is_pinned ON chat TYPE bool DEFAULT false;

-- 为user_id和last_message_at创建索引，方便按用户查询和排序
DEFINE INDEX idx_user_last_message ON chat FIELDS user_id, last_message_at DESC;
"""

# SurrealDB 消息表定义
MESSAGE_SCHEMA = """
-- 消息表定义
DEFINE TABLE message SCHEMAFULL;

DEFINE FIELD chat_id ON message TYPE record<chat> ASSERT $value != NONE;
DEFINE FIELD role ON message TYPE string ASSERT $value IN ['user', 'assistant', 'system'];
DEFINE FIELD content ON message TYPE string ASSERT $value != NONE;
DEFINE FIELD timestamp ON message TYPE datetime DEFAULT time::now();
DEFINE FIELD token_count ON message TYPE int;
DEFINE FIELD metadata ON message TYPE object;

-- 为chat_id和timestamp创建索引，方便按会话查询和按时间排序
DEFINE INDEX idx_chat_messages ON message FIELDS chat_id, timestamp ASC;
"""

# 初始化数据库模式的函数
async def init_chat_schema(db):
    """初始化聊天和消息的数据库模式"""
    try:
        # 创建聊天表
        await db.query(CHAT_SCHEMA)
        print("聊天表模式创建成功")
        
        # 创建消息表
        await db.query(MESSAGE_SCHEMA)
        print("消息表模式创建成功")
        
        return True
    except Exception as e:
        print(f"初始化聊天模式失败: {str(e)}")
        return False
