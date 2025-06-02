"""
图片处理模块 - 用于处理和格式化不同类型的图片输入
支持URL、本地文件路径和字节内容三种输入方式
"""

from dataclasses import dataclass
from typing import Optional, Union, Any, Dict, List
from pathlib import Path
import base64
import logging
import os

@dataclass
class ImageData:
    """图片数据类，支持多种输入格式"""
    url: Optional[str] = None
    filepath: Optional[Union[Path, str]] = None
    content: Optional[bytes] = None
    format: Optional[str] = None
    detail: Optional[str] = None  # low, medium, high, auto
    
    def __post_init__(self):
        """验证输入数据"""
        inputs = [self.url, self.filepath, self.content]
        non_none_count = sum(1 for x in inputs if x is not None)
        
        if non_none_count == 0:
            raise ValueError("必须提供url、filepath或content中的一个")
        elif non_none_count > 1:
            raise ValueError("只能提供url、filepath或content中的一个")
    
    @property
    def image_url_content(self) -> Optional[bytes]:
        """从URL获取图片内容"""
        if self.url:
            import requests
            return requests.get(self.url).content
        return None


class ImageProcessor:
    """图片处理器"""
    
    def __init__(self):
        self.supported_formats = {
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg", 
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp"
        }
    
    def process_image(self, image: ImageData) -> Optional[Dict[str, Any]]:
        """处理图片，根据输入格式选择相应的处理方法"""
        try:
            if image.url is not None:
                return self._process_image_url(image.url, image.detail)
            elif image.filepath is not None:
                return self._process_image_path(image.filepath, image.detail)
            elif image.content is not None:
                return self._process_image_bytes(image.content, image.detail)
            else:
                logging.warning(f"不支持的图片格式: {image}")
                return None
        except Exception as e:
            logging.error(f"处理图片时出错: {e}")
            return None
    
    def _process_image_url(self, url: str, detail: Optional[str] = None) -> Dict[str, Any]:
        """处理URL格式的图片"""
        if url.startswith("data:image") or url.startswith(("http://", "https://")):
            payload = {"type": "image_url", "image_url": {"url": url}}
            if detail:
                payload["image_url"]["detail"] = detail
            return payload
        else:
            raise ValueError("图片URL必须以'data:image'或'http(s)://'开头")
    
    def _process_image_path(self, filepath: Union[Path, str], detail: Optional[str] = None) -> Dict[str, Any]:
        """处理本地文件路径的图片"""
        import mimetypes
        
        path = Path(filepath) if isinstance(filepath, str) else filepath
        if not path.exists():
            raise FileNotFoundError(f"图片文件不存在: {filepath}")
        
        # 获取MIME类型
        mime_type = mimetypes.guess_type(str(filepath))[0] or "image/jpeg"
        
        # 读取文件并编码
        with open(path, "rb") as f:
            image_bytes = f.read()
        
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        image_url = f"data:{mime_type};base64,{base64_image}"
        
        payload = {"type": "image_url", "image_url": {"url": image_url}}
        if detail:
            payload["image_url"]["detail"] = detail
        return payload
    
    def _process_image_bytes(self, content: bytes, detail: Optional[str] = None) -> Dict[str, Any]:
        """处理字节数据的图片"""
        # 尝试检测图片类型
        img_type = self.detect_image_type(content)
        mime_type = self.supported_formats.get(img_type, "image/jpeg")
        
        base64_image = base64.b64encode(content).decode("utf-8")
        image_url = f"data:{mime_type};base64,{base64_image}"
        
        payload = {"type": "image_url", "image_url": {"url": image_url}}
        if detail:
            payload["image_url"]["detail"] = detail
        return payload
    
    def detect_image_type(self, content: bytes) -> Optional[str]:
        """检测图片类型"""
        try:
            import imghdr
            return imghdr.what(None, h=content)
        except ImportError:
            try:
                import filetype
                kind = filetype.guess(content)
                return kind.extension if kind else None
            except ImportError:
                logging.warning("无法检测图片类型，请安装imghdr或filetype库")
                return None


class ModelImageFormatter:
    """不同模型的图片格式化器"""
    
    def __init__(self, processor: ImageProcessor):
        self.processor = processor
    
    def format_for_openai(self, images: List[ImageData]) -> List[Dict[str, Any]]:
        """为OpenAI格式化图片"""
        formatted_images = []
        for image in images:
            processed = self.processor.process_image(image)
            if processed:
                formatted_images.append(processed)
        return formatted_images
    
    def format_for_claude(self, images: List[ImageData]) -> List[Dict[str, Any]]:
        """为Claude格式化图片"""
        formatted_images = []
        for image in images:
            if image.url:
                formatted_images.append({
                    "type": "image",
                    "source": {"type": "url", "url": image.url}
                })
            else:
                # 获取图片字节数据
                if image.filepath:
                    with open(image.filepath, "rb") as f:
                        content_bytes = f.read()
                elif image.content:
                    content_bytes = image.content
                else:
                    continue
                
                # 检测图片类型
                img_type = self.processor.detect_image_type(content_bytes)
                if not img_type:
                    continue
                
                media_type = self.processor.supported_formats.get(img_type)
                if not media_type:
                    continue
                
                formatted_images.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": base64.b64encode(content_bytes).decode("utf-8")
                    }
                })
        return formatted_images


def handle_file_upload(file):
    """处理文件上传"""
    if hasattr(file, 'content_type') and file.content_type in ["image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"]:
        try:
            # 读取文件内容
            content = file.file.read() if hasattr(file, 'file') else file.read()
            # 创建图片对象
            image = ImageData(content=content, format=file.content_type)
            return image
        except Exception as e:
            logging.error(f"处理图片 {getattr(file, 'filename', 'unknown')} 时出错: {e}")
            return None
    else:
        raise ValueError("不支持的文件类型")
