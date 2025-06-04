"""
文件处理路由 - 处理各种类型文件的上传和分析请求 - FastAPI版本
"""

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union, Set
import os
import uuid
from werkzeug.utils import secure_filename
import logging

from app.agent.file_processor import handle_file_upload
from app.routes.auth_routes import get_current_user

# 创建路由器
router = APIRouter(prefix="/file", tags=["文件处理"])

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

# 定义响应模型
class FileUploadResponse(BaseModel):
    success: bool = True
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    error: Optional[str] = None

def allowed_file(filename: str, file_type: Optional[str] = None) -> bool:
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

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    file_type: Optional[str] = Form(None)
):
    """通用文件上传处理"""
    try:
        # 检查文件名
        if file.filename == '':
            raise HTTPException(status_code=400, detail="未选择文件")
        
        # 检查文件类型
        if not allowed_file(file.filename, file_type):
            raise HTTPException(status_code=400, detail="不支持的文件类型")
        
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        
        # 读取文件内容
        file_content = await file.read()
        
        # 处理文件上传
        result = handle_file_upload(
            file_content,
            filename,
            file.content_type
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="文件处理失败")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"上传文件失败: {str(e)}")
        return {
            "success": False,
            "error": f"上传失败: {str(e)}"
        }

@router.get("/uploads/{filename:path}")
async def serve_file(filename: str):
    """提供上传文件的访问"""
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(file_path)

@router.get("/uploads/{file_type}/{filename:path}")
async def serve_typed_file(file_type: str, filename: str):
    """提供特定类型上传文件的访问"""
    type_folder = os.path.join(UPLOAD_FOLDER, file_type)
    file_path = os.path.join(type_folder, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(file_path)
