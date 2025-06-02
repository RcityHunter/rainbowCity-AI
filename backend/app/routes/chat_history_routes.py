"""
聊天历史记录API路由
实现单用户与AI聊天的历史记录存储和检索功能
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import jwt
import time
from datetime import datetime
from app.db import create, query, update, run_async, get_db

# 创建API蓝图
chat_history_bp = Blueprint('chat_history', __name__, url_prefix='/api/chats')

# JWT 认证装饰器
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # 从请求头中获取token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]  # 移除'Bearer '前缀
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # 解码token
            secret_key = current_app.config.get('SECRET_KEY', 'dev_key')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# 获取用户的所有聊天会话
@chat_history_bp.route('', methods=['GET'])
@token_required
def get_user_chats(current_user):
    """获取当前用户的所有聊天会话"""
    user_id = current_user.get('id')
    
    try:
        async def _get_chats():
            db = await get_db()
            if db is None:
                return []
            
            # 查询用户的所有未归档聊天，按最后消息时间和置顶状态排序
            result = await db.query(f"""
                SELECT * FROM chat 
                WHERE user_id = '{user_id}' AND is_archived = false 
                ORDER BY is_pinned DESC, last_message_at DESC
            """)
            
            if result and isinstance(result, list) and len(result) > 0:
                return result
            return []
        
        chats = run_async(_get_chats())
        
        # 处理查询结果
        if chats:
            return jsonify({
                'chats': chats
            }), 200
        else:
            return jsonify({
                'chats': []
            }), 200
            
    except Exception as e:
        print(f"Error fetching chats: {str(e)}")
        return jsonify({'error': f'Failed to fetch chats: {str(e)}'}), 500

# 创建新的聊天会话
@chat_history_bp.route('', methods=['POST'])
@token_required
def create_chat(current_user):
    """创建新的聊天会话"""
    user_id = current_user.get('id')
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # 设置默认值
    title = data.get('title', '新聊天')
    model_used = data.get('model_used', 'gemini-pro')
    
    try:
        # 创建新的聊天会话
        chat_data = {
            'user_id': user_id,
            'title': title,
            'created_at': datetime.now().isoformat(),
            'last_message_at': datetime.now().isoformat(),
            'model_used': model_used,
            'is_archived': False,
            'is_pinned': False
        }
        
        # 如果提供了预览，则添加
        if 'last_message_preview' in data:
            chat_data['last_message_preview'] = data['last_message_preview']
        
        result = create('chat', chat_data)
        
        if result and len(result) > 0:
            chat_id = result[0].get('id')
            return jsonify({
                'message': 'Chat created successfully',
                'chat_id': chat_id,
                'chat': result[0]
            }), 201
        else:
            return jsonify({'error': 'Failed to create chat'}), 500
            
    except Exception as e:
        print(f"Error creating chat: {str(e)}")
        return jsonify({'error': f'Failed to create chat: {str(e)}'}), 500

# 获取特定聊天会话的详情
@chat_history_bp.route('/<chat_id>', methods=['GET'])
@token_required
def get_chat(current_user, chat_id):
    """获取特定聊天会话的详情"""
    user_id = current_user.get('id')
    
    try:
        # 查询聊天会话
        chats = query('chat', {'id': f'chat:{chat_id}'})
        
        if not chats or len(chats) == 0:
            return jsonify({'error': 'Chat not found'}), 404
        
        chat = chats[0]
        
        # 验证聊天会话属于当前用户
        if chat.get('user_id') != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify({
            'chat': chat
        }), 200
            
    except Exception as e:
        print(f"Error fetching chat: {str(e)}")
        return jsonify({'error': f'Failed to fetch chat: {str(e)}'}), 500

# 更新聊天会话
@chat_history_bp.route('/<chat_id>', methods=['PUT'])
@token_required
def update_chat(current_user, chat_id):
    """更新聊天会话信息"""
    user_id = current_user.get('id')
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # 查询聊天会话
        chats = query('chat', {'id': f'chat:{chat_id}'})
        
        if not chats or len(chats) == 0:
            return jsonify({'error': 'Chat not found'}), 404
        
        chat = chats[0]
        
        # 验证聊天会话属于当前用户
        if chat.get('user_id') != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # 准备更新数据
        update_data = {}
        
        # 只更新允许的字段
        allowed_fields = ['title', 'last_message_at', 'last_message_preview', 'is_archived', 'is_pinned', 'model_used']
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        # 如果没有要更新的数据，直接返回成功
        if not update_data:
            return jsonify({
                'message': 'No changes to update',
                'chat': chat
            }), 200
        
        # 更新聊天会话
        result = update(f'chat:{chat_id}', update_data)
        
        if result and len(result) > 0:
            return jsonify({
                'message': 'Chat updated successfully',
                'chat': result[0]
            }), 200
        else:
            return jsonify({'error': 'Failed to update chat'}), 500
            
    except Exception as e:
        print(f"Error updating chat: {str(e)}")
        return jsonify({'error': f'Failed to update chat: {str(e)}'}), 500

# 删除聊天会话
@chat_history_bp.route('/<chat_id>', methods=['DELETE'])
@token_required
def delete_chat(current_user, chat_id):
    """删除聊天会话"""
    user_id = current_user.get('id')
    
    try:
        # 查询聊天会话
        chats = query('chat', {'id': f'chat:{chat_id}'})
        
        if not chats or len(chats) == 0:
            return jsonify({'error': 'Chat not found'}), 404
        
        chat = chats[0]
        
        # 验证聊天会话属于当前用户
        if chat.get('user_id') != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # 删除聊天会话
        async def _delete_chat():
            db = await get_db()
            if db is None:
                return False
            
            # 先删除关联的消息
            await db.query(f"DELETE FROM message WHERE chat_id = 'chat:{chat_id}'")
            
            # 再删除聊天会话
            await db.delete(f"chat:{chat_id}")
            return True
        
        result = run_async(_delete_chat())
        
        if result:
            return jsonify({
                'message': 'Chat deleted successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to delete chat'}), 500
            
    except Exception as e:
        print(f"Error deleting chat: {str(e)}")
        return jsonify({'error': f'Failed to delete chat: {str(e)}'}), 500

# 获取聊天会话的消息
@chat_history_bp.route('/<chat_id>/messages', methods=['GET'])
@token_required
def get_chat_messages(current_user, chat_id):
    """获取特定聊天会话的消息"""
    user_id = current_user.get('id')
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    # 限制页面大小，防止请求过大
    if page_size > 50:
        page_size = 50
    
    try:
        # 先验证聊天会话存在且属于当前用户
        chats = query('chat', {'id': f'chat:{chat_id}'})
        
        if not chats or len(chats) == 0:
            return jsonify({'error': 'Chat not found'}), 404
        
        chat = chats[0]
        
        if chat.get('user_id') != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # 查询消息
        async def _get_messages():
            db = await get_db()
            if db is None:
                return []
            
            # 计算偏移量
            offset = (page - 1) * page_size
            
            # 查询消息，按时间升序排序
            result = await db.query(f"""
                SELECT * FROM message 
                WHERE chat_id = 'chat:{chat_id}' 
                ORDER BY timestamp ASC 
                LIMIT {page_size} 
                START {offset}
            """)
            
            # 查询消息总数
            count_result = await db.query(f"""
                SELECT count() as total FROM message 
                WHERE chat_id = 'chat:{chat_id}'
            """)
            
            total = 0
            if count_result and isinstance(count_result, list) and len(count_result) > 0:
                total = count_result[0].get('total', 0)
            
            return {
                'messages': result if result else [],
                'total': total
            }
        
        result = run_async(_get_messages())
        
        if result:
            messages = result.get('messages', [])
            total = result.get('total', 0)
            
            return jsonify({
                'messages': messages,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }), 200
        else:
            return jsonify({
                'messages': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            }), 200
            
    except Exception as e:
        print(f"Error fetching messages: {str(e)}")
        return jsonify({'error': f'Failed to fetch messages: {str(e)}'}), 500

# 添加消息到聊天会话
@chat_history_bp.route('/<chat_id>/messages', methods=['POST'])
@token_required
def add_chat_message(current_user, chat_id):
    """添加消息到聊天会话"""
    user_id = current_user.get('id')
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # 验证必要字段
    if 'role' not in data or 'content' not in data:
        return jsonify({'error': 'Missing required fields: role, content'}), 400
    
    role = data.get('role')
    content = data.get('content')
    
    # 验证角色
    if role not in ['user', 'assistant', 'system']:
        return jsonify({'error': 'Invalid role. Must be one of: user, assistant, system'}), 400
    
    try:
        # 先验证聊天会话存在且属于当前用户
        chats = query('chat', {'id': f'chat:{chat_id}'})
        
        if not chats or len(chats) == 0:
            return jsonify({'error': 'Chat not found'}), 404
        
        chat = chats[0]
        
        if chat.get('user_id') != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # 准备消息数据
        message_data = {
            'chat_id': f'chat:{chat_id}',
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        # 添加可选字段
        if 'token_count' in data:
            message_data['token_count'] = data['token_count']
        
        if 'metadata' in data:
            message_data['metadata'] = data['metadata']
        
        # 创建消息
        result = create('message', message_data)
        
        if result and len(result) > 0:
            message_id = result[0].get('id')
            
            # 更新聊天会话的最后消息时间和预览
            preview = content
            if len(preview) > 100:
                preview = preview[:97] + '...'
            
            update_data = {
                'last_message_at': datetime.now().isoformat(),
                'last_message_preview': preview
            }
            
            update(f'chat:{chat_id}', update_data)
            
            return jsonify({
                'message': 'Message added successfully',
                'message_id': message_id,
                'message': result[0]
            }), 201
        else:
            return jsonify({'error': 'Failed to add message'}), 500
            
    except Exception as e:
        print(f"Error adding message: {str(e)}")
        return jsonify({'error': f'Failed to add message: {str(e)}'}), 500

# 批量添加消息到聊天会话
@chat_history_bp.route('/<chat_id>/messages/batch', methods=['POST'])
@token_required
def add_chat_messages_batch(current_user, chat_id):
    """批量添加消息到聊天会话"""
    user_id = current_user.get('id')
    data = request.get_json()
    
    if not data or 'messages' not in data:
        return jsonify({'error': 'No messages provided'}), 400
    
    messages = data.get('messages', [])
    if not messages or not isinstance(messages, list):
        return jsonify({'error': 'Invalid messages format'}), 400
    
    try:
        # 先验证聊天会话存在且属于当前用户
        chats = query('chat', {'id': f'chat:{chat_id}'})
        
        if not chats or len(chats) == 0:
            return jsonify({'error': 'Chat not found'}), 404
        
        chat = chats[0]
        
        if chat.get('user_id') != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # 批量创建消息
        async def _create_messages_batch():
            db = await get_db()
            if db is None:
                return False
            
            created_messages = []
            last_message = None
            
            for msg in messages:
                # 验证必要字段
                if 'role' not in msg or 'content' not in msg:
                    continue
                
                role = msg.get('role')
                content = msg.get('content')
                
                # 验证角色
                if role not in ['user', 'assistant', 'system']:
                    continue
                
                # 准备消息数据
                message_data = {
                    'chat_id': f'chat:{chat_id}',
                    'role': role,
                    'content': content,
                    'timestamp': msg.get('timestamp', datetime.now().isoformat())
                }
                
                # 添加可选字段
                if 'token_count' in msg:
                    message_data['token_count'] = msg['token_count']
                
                if 'metadata' in msg:
                    message_data['metadata'] = msg['metadata']
                
                # 创建消息
                result = await db.create('message', message_data)
                
                if result and len(result) > 0:
                    created_messages.append(result[0])
                    last_message = result[0]
            
            # 如果有消息被创建，更新聊天会话的最后消息时间和预览
            if last_message:
                preview = last_message.get('content', '')
                if len(preview) > 100:
                    preview = preview[:97] + '...'
                
                update_data = {
                    'last_message_at': last_message.get('timestamp', datetime.now().isoformat()),
                    'last_message_preview': preview
                }
                
                await db.update(f"chat:{chat_id}", update_data)
            
            return created_messages
        
        created_messages = run_async(_create_messages_batch())
        
        if created_messages:
            return jsonify({
                'message': f'{len(created_messages)} messages added successfully',
                'messages': created_messages
            }), 201
        else:
            return jsonify({'error': 'Failed to add messages'}), 500
            
    except Exception as e:
        print(f"Error adding messages batch: {str(e)}")
        return jsonify({'error': f'Failed to add messages batch: {str(e)}'}), 500
