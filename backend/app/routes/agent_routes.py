"""
彩虹城AI-Agent对话管理系统API路由
"""

from flask import Blueprint, request, jsonify, current_app
import json
import os
import uuid
import base64
import mimetypes
import logging
from datetime import datetime
from app.agent.ai_assistant import AIAssistant
from app.agent.image_processor import ImageData
from app.agent.file_processor import handle_file_upload

# 配置日志
logging.basicConfig(level=logging.DEBUG)

# 创建API蓝图
agent_bp = Blueprint('agent', __name__, url_prefix='/api/agent')

# 创建AI助手实例
assistant = AIAssistant(model_name="gpt-3.5-turbo")

@agent_bp.route('/chat', methods=['POST'])
def chat_agent():
    """AI-Agent聊天接口"""
    try:
        data = request.json
        
        # 获取请求数据
        user_message = data.get('user_input', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        user_id = data.get('user_id', 'anonymous')
        ai_id = data.get('ai_id', 'ai_rainbow_city')
        image_data = data.get('image_data')  # 获取图片数据（如果有）
        
        # 创建AI助手实例
        ai_assistant = AIAssistant()
        
        # 处理用户查询
        result = ai_assistant.process_query(
            user_input=user_message,
            session_id=session_id,
            user_id=user_id,
            ai_id=ai_id,
            image_data=image_data
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@agent_bp.route('/chat/with_file', methods=['POST'])
def chat_with_file():
    """带文件的AI-Agent聊天接口，支持图片、音频、视频和文档"""
    try:
        logging.debug("Received chat_with_file request")
        logging.debug(f"Request files: {request.files.keys() if request.files else 'None'}")
        logging.debug(f"Request form: {request.form.keys() if request.form else 'None'}")
        
        # 检查是否有文件部分
        if not request.files and 'user_input' not in request.form:
            logging.error("Missing required parameters")
            return jsonify({'error': '请求缺少必要参数'}), 400
        
        # 获取用户文本输入
        user_message = request.form.get('user_input', '')
        session_id = request.form.get('session_id', str(uuid.uuid4()))
        user_id = request.form.get('user_id', 'anonymous')
        ai_id = request.form.get('ai_id', 'ai_rainbow_city')
        
        logging.debug(f"User message: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")
        logging.debug(f"Session ID: {session_id}")
        
        # 处理文件
        file_data = None
        file_type = None
        file_info = None
        
        # 检查所有可能的文件字段
        for file_field in ['file', 'image', 'audio', 'video', 'document']:
            if file_field in request.files:
                file = request.files[file_field]
                if file and file.filename:
                    logging.debug(f"Processing {file_field} file: {file.filename}, content-type: {file.content_type}")
                    try:
                        # 读取文件内容
                        file_content = file.read()
                        logging.debug(f"File size: {len(file_content)} bytes")
                        
                        # 处理文件上传
                        file_info = handle_file_upload(
                            file_content,
                            file.filename,
                            file.content_type
                        )
                        
                        if file_info:
                            logging.debug(f"File upload successful: {file_info}")
                            # 确定文件类型
                            file_type = file_info['file_type']
                            logging.debug(f"Detected file type: {file_type}")
                            
                            # Base64编码
                            file_base64 = base64.b64encode(file_content).decode('utf-8')
                            # 添加数据URL前缀
                            mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
                            file_data = f"data:{mime_type};base64,{file_base64}"
                            logging.debug(f"Created data URL with mime-type: {mime_type}")
                            break
                        else:
                            logging.error(f"File upload returned no info for {file.filename}")
                    except Exception as e:
                        logging.exception(f"Error processing file {file.filename}: {str(e)}")
                        return jsonify({'error': f'文件处理失败: {str(e)}'}), 400
        
        logging.debug(f"File processing complete. File type: {file_type}, File data present: {file_data is not None}")
        
        # 创建AI助手实例
        ai_assistant = AIAssistant()
        logging.debug("Created AI Assistant instance")
        
        # 准备文件数据参数
        file_data_param = None
        if file_data:
            file_data_param = {
                'type': file_type,
                'data': file_data,
                'info': file_info
            }
            logging.debug(f"Prepared file data parameter with type: {file_type}")
        
        # 处理用户查询
        logging.debug("Calling AI Assistant process_query")
        result = ai_assistant.process_query(
            user_input=user_message,
            session_id=session_id,
            user_id=user_id,
            ai_id=ai_id,
            image_data=file_data if file_type == 'image' else None,
            file_data=file_data_param
        )
        logging.debug(f"AI Assistant process_query completed with result keys: {result.keys() if result else 'None'}")
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 保留原有的图片处理接口以保持兼容性
@agent_bp.route('/chat/with_image', methods=['POST'])
def chat_with_image():
    """带图片的AI-Agent聊天接口（兼容旧版本）"""
    return chat_with_file()

@agent_bp.route('/history/<session_id>', methods=['GET'])
def get_history(session_id):
    """获取会话历史"""
    try:
        history = assistant.get_conversation_history(session_id)
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "history": history
        })
        
    except Exception as e:
        current_app.logger.error(f"获取会话历史时出错: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@agent_bp.route('/logs/<session_id>', methods=['GET'])
def get_logs(session_id):
    """获取会话日志"""
    try:
        logs = assistant.get_session_logs(session_id)
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "logs": logs
        })
        
    except Exception as e:
        current_app.logger.error(f"获取会话日志时出错: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@agent_bp.route('/session/clear/<session_id>', methods=['POST'])
def clear_session(session_id):
    """清除会话数据"""
    try:
        success = assistant.clear_session(session_id)
        
        return jsonify({
            "success": success,
            "session_id": session_id,
            "message": "会话数据已清除" if success else "未找到指定会话"
        })
        
    except Exception as e:
        current_app.logger.error(f"清除会话数据时出错: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
