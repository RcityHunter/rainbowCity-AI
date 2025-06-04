"""
图片处理路由 - 处理图片上传和分析请求 - FastAPI版本
"""

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
import base64
import os
import uuid
from werkzeug.utils import secure_filename
import logging

from app.agent.image_processor import ImageData, handle_file_upload
from app.agent.tool_invoker import analyze_image
from app.routes.auth_routes import get_current_user

# 创建路由器
router = APIRouter(prefix="/image", tags=["图片处理"])

# 配置上传文件夹
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 允许的文件类型
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# 定义请求和响应模型
class ImageAnalysisRequest(BaseModel):
    image_data: str
    analysis_type: Optional[str] = "general"

class Base64ImageRequest(BaseModel):
    base64_data: str

class ImageResponse(BaseModel):
    success: bool
    filename: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None

class AnalysisResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

def allowed_file(filename):
    """检查文件类型是否允许上传"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@router.post("/upload", response_model=ImageResponse)
async def upload_image(file: UploadFile = File(...)):
    """处理图片上传请求"""
    try:
        # 检查文件名
        if file.filename == '':
            raise HTTPException(status_code=400, detail="未选择文件")
        
        # 检查文件类型
        if not allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="不支持的文件类型")
        
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # 保存文件
        file_content = await file.read()
        with open(filepath, "wb") as f:
            f.write(file_content)
        
        # 生成文件URL (在实际部署中，这应该是一个可访问的URL)
        file_url = f"/uploads/{unique_filename}"
        
        return {
            "success": True,
            "filename": unique_filename,
            "url": file_url
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"上传图片失败: {str(e)}")
        return {
            "success": False,
            "error": f"上传失败: {str(e)}"
        }

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_image_route(analysis_data: ImageAnalysisRequest):
    """处理图片分析请求"""
    try:
        image_data = analysis_data.image_data
        analysis_type = analysis_data.analysis_type
        
        if not image_data:
            raise HTTPException(status_code=400, detail="未提供图片数据")
        
        # 调用图片分析工具
        result = analyze_image(image_data, analysis_type)
        
        return {
            "success": True,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"分析图片失败: {str(e)}")
        return {
            "success": False,
            "error": f"分析失败: {str(e)}"
        }

@router.post("/base64", response_model=ImageResponse)
async def handle_base64_image(base64_data: Base64ImageRequest):
    """处理Base64编码的图片"""
    try:
        if not base64_data.base64_data:
            raise HTTPException(status_code=400, detail="未提供Base64图片数据")
        
        # 解码Base64数据
        b64_data = base64_data.base64_data
        if ',' in b64_data:
            # 如果包含数据URL格式 (data:image/jpeg;base64,...)
            _, b64_data = b64_data.split(',', 1)
        
        try:
            image_data = base64.b64decode(b64_data)
        except Exception:
            raise HTTPException(status_code=400, detail="无效的Base64图片数据")
        
        # 生成唯一文件名
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # 保存文件
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        # 生成文件URL
        file_url = f"/uploads/{filename}"
        
        return {
            "success": True,
            "filename": filename,
            "url": file_url
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"处理Base64图片失败: {str(e)}")
        return {
            "success": False,
            "error": f"处理失败: {str(e)}"
        }
