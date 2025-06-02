"""
通用文件处理模块 - 处理多种类型的文件上传和分析
"""

from dataclasses import dataclass
from typing import Optional, Union, Any, Dict, List
from pathlib import Path
import base64
import logging
import os
import mimetypes
import uuid

@dataclass
class BaseFileData:
    """基础文件数据类"""
    filepath: Optional[Union[Path, str]] = None
    content: Optional[bytes] = None
    url: Optional[str] = None
    format: Optional[str] = None
    mime_type: Optional[str] = None
    
    def __post_init__(self):
        """验证输入数据"""
        inputs = [self.filepath, self.content, self.url]
        non_none_count = sum(1 for x in inputs if x is not None)
        
        if non_none_count == 0:
            raise ValueError("必须提供filepath、content或url中的一个")
        elif non_none_count > 1:
            logging.warning("提供了多个输入源，将优先使用content，然后是filepath，最后是url")

@dataclass
class ImageFileData(BaseFileData):
    """图片文件数据类"""
    detail: Optional[str] = None  # low, medium, high, auto

@dataclass
class AudioFileData(BaseFileData):
    """音频文件数据类"""
    length: Optional[float] = None
    filename: Optional[str] = None

@dataclass
class VideoFileData(BaseFileData):
    """视频文件数据类"""
    length: Optional[float] = None
    filename: Optional[str] = None

@dataclass
class DocumentFileData(BaseFileData):
    """文档文件数据类"""
    filename: Optional[str] = None
    size: Optional[int] = None

class FileProcessor:
    """通用文件处理器"""
    
    def __init__(self):
        # 文件类型映射
        self.mime_type_mapping = {
            # 图片
            "image/png": "image",
            "image/jpeg": "image",
            "image/jpg": "image",
            "image/webp": "image",
            "image/gif": "image",
            
            # 视频
            "video/mp4": "video",
            "video/webm": "video",
            "video/quicktime": "video",
            "video/x-flv": "video",
            "video/mpeg": "video",
            "video/wmv": "video",
            "video/3gpp": "video",
            
            # 音频
            "audio/wav": "audio",
            "audio/mp3": "audio",
            "audio/mpeg": "audio",
            "audio/m4a": "audio",
            "audio/flac": "audio",
            "audio/ogg": "audio",
            
            # 文档
            "application/pdf": "document",
            "text/plain": "document",
            "text/csv": "document",
            "application/json": "document",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "document"
        }
        
        # 支持的文件扩展名
        self.supported_extensions = {
            "image": [".png", ".jpg", ".jpeg", ".gif", ".webp"],
            "video": [".mp4", ".mov", ".avi", ".mkv", ".webm"],
            "audio": [".wav", ".mp3", ".m4a", ".flac", ".ogg"],
            "document": [".pdf", ".txt", ".csv", ".json", ".docx"]
        }
        
        # 最大文件大小 (50MB)
        self.max_file_size = 50 * 1024 * 1024
    
    def detect_file_type(self, mime_type: str) -> str:
        """根据MIME类型检测文件类型"""
        return self.mime_type_mapping.get(mime_type, "unknown")
    
    def detect_type_from_extension(self, filename: str) -> str:
        """从文件扩展名检测类型"""
        ext = os.path.splitext(filename)[1].lower()
        
        for file_type, extensions in self.supported_extensions.items():
            if ext in extensions:
                return file_type
        
        return "unknown"
    
    def validate_file(self, file_data: BaseFileData, file_type: str) -> bool:
        """验证文件是否符合要求"""
        # 检查文件大小
        if file_data.content and len(file_data.content) > self.max_file_size:
            logging.error(f"文件大小超过限制: {len(file_data.content)} bytes")
            return False
        
        # 检查文件扩展名
        if file_data.filepath:
            ext = os.path.splitext(str(file_data.filepath))[1].lower()
            if ext not in self.supported_extensions.get(file_type, []):
                logging.error(f"不支持的文件扩展名: {ext}")
                return False
        
        return True
    
    def process_file(self, file_content: bytes, filename: str, content_type: str) -> Optional[Dict[str, Any]]:
        """处理文件上传"""
        file_type = self.detect_file_type(content_type)
        
        if file_type == "unknown":
            file_type = self.detect_type_from_extension(filename)
        
        if file_type == "unknown":
            logging.error(f"无法识别的文件类型: {content_type}, {filename}")
            return None
        
        try:
            # 生成唯一文件名
            unique_filename = f"{uuid.uuid4()}_{filename}"
            
            # 确定上传目录 - 尝试多个可能的位置
            possible_upload_dirs = [
                # 项目根目录/uploads/file_type
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'uploads', file_type),
                # backend/uploads/file_type
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads', file_type),
                # 当前工作目录/uploads/file_type
                os.path.join(os.getcwd(), 'uploads', file_type),
                # backend/app/uploads/file_type
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', file_type)
            ]
            
            # 选择第一个存在的目录，或创建新目录
            upload_dir = None
            for folder in possible_upload_dirs:
                if os.path.exists(folder):
                    upload_dir = folder
                    logging.debug(f"Using existing upload folder: {upload_dir}")
                    break
            
            # 如果没有找到现有目录，则创建新目录
            if not upload_dir:
                # 默认使用项目根目录下的uploads/file_type
                upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'uploads', file_type)
                os.makedirs(upload_dir, exist_ok=True)
                logging.debug(f"Created new upload folder: {upload_dir}")
            
            # 保存文件
            filepath = os.path.join(upload_dir, unique_filename)
            with open(filepath, 'wb') as f:
                f.write(file_content)
            
            # 生成文件URL
            file_url = f"/uploads/{file_type}/{unique_filename}"
            
            # 创建文件数据对象
            if file_type == "image":
                file_data = ImageFileData(
                    filepath=filepath,
                    content=file_content,
                    format=content_type.split("/")[1],
                    mime_type=content_type
                )
            elif file_type == "audio":
                file_data = AudioFileData(
                    filepath=filepath,
                    content=file_content,
                    format=content_type.split("/")[1],
                    mime_type=content_type,
                    filename=filename
                )
            elif file_type == "video":
                file_data = VideoFileData(
                    filepath=filepath,
                    content=file_content,
                    format=content_type.split("/")[1],
                    mime_type=content_type,
                    filename=filename
                )
            elif file_type == "document":
                file_data = DocumentFileData(
                    filepath=filepath,
                    content=file_content,
                    mime_type=content_type,
                    filename=filename,
                    size=len(file_content)
                )
            else:
                return None
            
            # 验证文件
            if not self.validate_file(file_data, file_type):
                os.remove(filepath)  # 删除不符合要求的文件
                return None
            
            # 返回处理结果
            return {
                "success": True,
                "file_type": file_type,
                "filename": unique_filename,
                "original_filename": filename,
                "url": file_url,
                "mime_type": content_type,
                "size": len(file_content)
            }
            
        except Exception as e:
            logging.error(f"处理文件上传时出错 {filename}: {e}")
            return None
    
    def get_base64_data(self, file_data: BaseFileData) -> Optional[str]:
        """获取文件的Base64编码数据"""
        try:
            if file_data.content:
                content = file_data.content
            elif file_data.filepath:
                with open(file_data.filepath, 'rb') as f:
                    content = f.read()
            else:
                return None
            
            return base64.b64encode(content).decode('utf-8')
        except Exception as e:
            logging.error(f"获取Base64数据失败: {e}")
            return None

# 创建全局文件处理器实例
file_processor = FileProcessor()

def handle_file_upload(file_content: bytes, filename: str, content_type: str) -> Optional[Dict[str, Any]]:
    """处理文件上传的便捷函数"""
    return file_processor.process_file(file_content, filename, content_type)
