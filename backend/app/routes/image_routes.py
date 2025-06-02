"""
图片处理路由 - 处理图片上传和分析请求
"""

from flask import Blueprint, request, jsonify
import base64
import os
import uuid
from werkzeug.utils import secure_filename
from app.agent.image_processor import ImageData, handle_file_upload
from app.agent.tool_invoker import analyze_image

# 创建蓝图
image_bp = Blueprint('image', __name__)

# 配置上传文件夹
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 允许的文件类型
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """检查文件类型是否允许上传"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@image_bp.route('/upload', methods=['POST'])
def upload_image():
    """处理图片上传请求"""
    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    
    # 检查文件名
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    # 检查文件类型
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型'}), 400
    
    try:
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # 保存文件
        file.save(filepath)
        
        # 生成文件URL (在实际部署中，这应该是一个可访问的URL)
        file_url = f"/uploads/{unique_filename}"
        
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'url': file_url
        })
    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@image_bp.route('/analyze', methods=['POST'])
def analyze_image_route():
    """处理图片分析请求"""
    data = request.json
    
    if not data:
        return jsonify({'error': '请求数据为空'}), 400
    
    image_data = data.get('image_data')
    analysis_type = data.get('analysis_type', 'general')
    
    if not image_data:
        return jsonify({'error': '未提供图片数据'}), 400
    
    try:
        # 调用图片分析工具
        result = analyze_image(image_data, analysis_type)
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({'error': f'分析失败: {str(e)}'}), 500

@image_bp.route('/base64', methods=['POST'])
def handle_base64_image():
    """处理Base64编码的图片"""
    data = request.json
    
    if not data:
        return jsonify({'error': '请求数据为空'}), 400
    
    base64_data = data.get('base64_data')
    
    if not base64_data:
        return jsonify({'error': '未提供Base64图片数据'}), 400
    
    try:
        # 解码Base64数据
        if ',' in base64_data:
            # 如果包含数据URL格式 (data:image/jpeg;base64,...)
            _, base64_data = base64_data.split(',', 1)
        
        image_data = base64.b64decode(base64_data)
        
        # 生成唯一文件名
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # 保存文件
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        # 生成文件URL
        file_url = f"/uploads/{filename}"
        
        return jsonify({
            'success': True,
            'filename': filename,
            'url': file_url
        })
    except Exception as e:
        return jsonify({'error': f'处理失败: {str(e)}'}), 500
