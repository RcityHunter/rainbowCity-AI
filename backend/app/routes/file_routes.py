"""
文件处理路由 - 处理各种类型文件的上传和分析请求
"""

from flask import Blueprint, request, jsonify, send_from_directory
import os
import uuid
from werkzeug.utils import secure_filename
from app.agent.file_processor import handle_file_upload

# 创建蓝图
file_bp = Blueprint('file', __name__, url_prefix='/api/file')

# 配置上传文件夹
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 允许的文件类型
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
    'audio': {'wav', 'mp3', 'mpeg', 'm4a', 'flac', 'ogg'},
    'video': {'mp4', 'mov', 'avi', 'mkv', 'webm', 'flv', 'mpeg'},
    'document': {'pdf', 'txt', 'csv', 'json', 'docx'}
}

def allowed_file(filename, file_type=None):
    """检查文件类型是否允许上传"""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if file_type:
        return ext in ALLOWED_EXTENSIONS.get(file_type, set())
    else:
        # 检查所有允许的扩展名
        for extensions in ALLOWED_EXTENSIONS.values():
            if ext in extensions:
                return True
        return False

@file_bp.route('/upload', methods=['POST'])
def upload_file():
    """通用文件上传处理"""
    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    file_type = request.form.get('file_type', None)  # 可选参数，指定文件类型
    
    # 检查文件名
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    # 检查文件类型
    if not allowed_file(file.filename, file_type):
        return jsonify({'error': '不支持的文件类型'}), 400
    
    try:
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        
        # 处理文件上传
        result = handle_file_upload(
            file.read(),
            filename,
            file.content_type
        )
        
        if not result:
            return jsonify({'error': '文件处理失败'}), 500
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@file_bp.route('/uploads/<path:filename>', methods=['GET'])
def serve_file(filename):
    """提供上传文件的访问"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@file_bp.route('/uploads/<file_type>/<path:filename>', methods=['GET'])
def serve_typed_file(file_type, filename):
    """提供特定类型上传文件的访问"""
    type_folder = os.path.join(UPLOAD_FOLDER, file_type)
    return send_from_directory(type_folder, filename)
