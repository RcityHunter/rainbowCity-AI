"""
工具调度器
负责注册、管理和调用各种工具函数
"""

from typing import Callable, Dict, Any, List, Optional
import json
import requests
import os
import base64
from datetime import datetime
from .image_processor import ImageData, ImageProcessor

class ToolInvoker:
    """工具调度和执行"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.tool_definitions: List[Dict[str, Any]] = []
        
        # 注册默认工具
        self.register_tool(
            name="get_weather",
            func=get_weather,
            description="获取指定城市的天气信息",
            parameters={
                "city": {"type": "string", "description": "城市名称，如北京、上海等"},
                "date": {"type": "string", "description": "日期，如今天、明天等，默认为今天"}
            }
        )
        
        self.register_tool(
            name="generate_ai_id",
            func=generate_ai_id,
            description="生成AI-ID",
            parameters={
                "name": {"type": "string", "description": "AI的名称，可选"}
            }
        )
        
        self.register_tool(
            name="generate_frequency",
            func=generate_frequency,
            description="生成频率编号",
            parameters={
                "ai_id": {"type": "string", "description": "AI-ID"},
                "personality_type": {"type": "string", "description": "人格类型，默认为P"},
                "ai_type": {"type": "string", "description": "AI类型，默认为A"}
            }
        )
        
        self.register_tool(
            name="analyze_image",
            func=analyze_image,
            description="分析图片内容",
            parameters={
                "image_data": {"type": "string", "description": "图片的Base64编码或URL"},
                "analysis_type": {"type": "string", "description": "分析类型，可以是'general'(一般描述), 'objects'(物体检测), 'text'(文字识别)"}
            }
        )
        
        self.register_tool(
            name="process_document",
            func=process_document,
            description="处理文档文件",
            parameters={
                "document_url": {"type": "string", "description": "文档的URL路径，如果不提供，将尝试使用最近上传的文档", "optional": True},
                "action": {"type": "string", "description": "要执行的操作，可以是'analyze'(分析内容), 'summarize'(生成摘要), 'extract'(提取信息)", "optional": True}
            }
        )
        
    def register_tool(self, name: str, func: Callable, description: str, parameters: Dict[str, Any]):
        """注册工具函数"""
        self.tools[name] = func
        
        # 添加工具定义（OpenAI格式）
        # 过滤出必需的参数（不包含optional=True的参数）
        required_params = []
        for k, v in parameters.items():
            if not isinstance(v, dict) or not v.get("optional", False):
                required_params.append(k)
        
        # 创建不包含optional字段的参数副本
        clean_parameters = {}
        for k, v in parameters.items():
            if isinstance(v, dict):
                param_copy = v.copy()
                if "optional" in param_copy:
                    del param_copy["optional"]
                clean_parameters[k] = param_copy
            else:
                clean_parameters[k] = v
        
        tool_def = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": clean_parameters,
                    "required": required_params
                }
            }
        }
        
        self.tool_definitions.append(tool_def)
        
    def invoke_tool(self, tool_name: str, **kwargs) -> str:
        """执行工具调用"""
        if tool_name not in self.tools:
            return f"工具 {tool_name} 不存在"
            
        try:
            result = self.tools[tool_name](**kwargs)
            return str(result)
        except Exception as e:
            return f"工具调用失败: {str(e)}"
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """获取所有工具定义"""
        return self.tool_definitions


# 默认工具函数实现

def get_weather(city: str, date: str = None) -> str:
    """获取天气信息的工具"""
    try:
        # 从环境变量获取API密钥
        api_key = os.getenv("WEATHER_API_KEY")
        
        # 检查API密钥是否存在
        if not api_key:
            return "WeatherAPI密钥未配置，请在.env文件中设置WEATHER_API_KEY"
        
        # 处理城市名称，确保它是有效的
        if not city:
            return "请提供城市名称"
        
        # 中国城市名称映射，将中文城市名映射为英文名称
        city_mapping = {
            # 直辖市
            "北京": "Beijing",
            "北京市": "Beijing",
            "上海": "Shanghai",
            "上海市": "Shanghai",
            "天津": "Tianjin",
            "天津市": "Tianjin",
            "重庆": "Chongqing",
            "重庆市": "Chongqing",
            
            # 主要城市
            "广州": "Guangzhou",
            "广州市": "Guangzhou",
            "深圳": "Shenzhen",
            "深圳市": "Shenzhen",
            "成都": "Chengdu",
            "成都市": "Chengdu",
            "杭州": "Hangzhou",
            "杭州市": "Hangzhou",
            "南京": "Nanjing",
            "南京市": "Nanjing",
            "武汉": "Wuhan",
            "武汉市": "Wuhan",
            "西安": "Xian",
            "西安市": "Xian",
            "郑州": "Zhengzhou",
            "郑州市": "Zhengzhou",
            "济南": "Jinan",
            "济南市": "Jinan",
            "青岛": "Qingdao",
            "青岛市": "Qingdao",
            "大连": "Dalian",
            "大连市": "Dalian",
            "沈阳": "Shenyang",
            "沈阳市": "Shenyang",
            "哈尔滨": "Harbin",
            "哈尔滨市": "Harbin",
            
            # 区县级城市
            "章丘": "Jinan",  # 章丘属于济南市
            "历城": "Jinan",  # 历城区属于济南市
            "历下": "Jinan",  # 历下区属于济南市
            "崂山": "Qingdao",  # 崂山区属于青岛市
            "黄埔": "Wuhan",  # 黄埔区属于武汉市
            "海淀": "Beijing",  # 海淀区属于北京市
            "浦东": "Shanghai"  # 浦东区属于上海市
        }
        
        # 检查是否需要映射
        if city in city_mapping:
            original_city = city
            city = city_mapping[city]
            print(f"[INFO] 将城市名称 '{original_city}' 映射为 '{city}'")
        
        print(f"\n[DEBUG] 尝试获取{city}的天气信息")
        
        # 构建API URL
        if date and date.lower() in ["tomorrow", "明天"]:
            # 如果是查询明天的天气，使用forecast API
            url = f"https://api.weatherapi.com/v1/forecast.json?key={api_key}&q={city}&days=2&lang=zh"
        else:
            # 默认查询当前天气
            url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={city}&lang=zh"
        
        print(f"[DEBUG] 请求URL: {url}")
        
        # 发送API请求
        response = requests.get(url, timeout=10)  # 添加超时时间
        
        print(f"[DEBUG] 响应状态码: {response.status_code}")
        
        # 检查状态码
        if response.status_code != 200:
            error_msg = f"请求失败，状态码: {response.status_code}"
            try:
                error_data = response.json()
                if 'error' in error_data and 'message' in error_data['error']:
                    error_msg += f", 错误信息: {error_data['error']['message']}"
            except:
                error_msg += ", 无法解析错误响应"
            
            print(f"[ERROR] {error_msg}")
            return f"无法获取{city}的天气信息: {error_msg}"
        
        # 解析JSON响应
        try:
            data = response.json()
        except Exception as e:
            print(f"[ERROR] JSON解析错误: {str(e)}")
            return f"无法解析天气数据: {str(e)}"
        
        # 检查数据结构
        if 'location' not in data:
            print(f"[ERROR] 响应中缺少location字段: {data}")
            return f"获取到的数据格式不正确，缺少必要字段"
        
        # 解析响应数据
        try:
            if date and date.lower() in ["tomorrow", "明天"]:
                # 获取明天的天气预报
                forecast = data["forecast"]["forecastday"][1]["day"]
                location = data["location"]
                weather_text = forecast["condition"]["text"]
                max_temp = forecast["maxtemp_c"]
                min_temp = forecast["mintemp_c"]
                rain_chance = forecast["daily_chance_of_rain"]
                
                result = f"明天{location['name']}天气: {weather_text}, 气温{min_temp}°C至{max_temp}°C, 降雨概率{rain_chance}%"
            else:
                # 获取当前天气
                current = data["current"]
                location = data["location"]
                weather_text = current["condition"]["text"]
                temp = current["temp_c"]
                feels_like = current["feelslike_c"]
                humidity = current["humidity"]
                
                result = f"{location['name']}当前天气: {weather_text}, 气温{temp}°C, 体感温度{feels_like}°C, 湿度{humidity}%"
            
            print(f"[DEBUG] 成功获取天气信息: {result}")
            return result
        except Exception as e:
            print(f"[ERROR] 数据解析错误: {str(e)}\n数据: {data}")
            return f"解析{city}的天气数据时出错: {str(e)}"
    except requests.exceptions.Timeout:
        return f"请求{city}天气信息超时，请稍后再试"
    except requests.exceptions.ConnectionError:
        return f"连接天气API服务器失败，请检查网络连接"
    except Exception as e:
        print(f"[ERROR] 未预期的错误: {str(e)}")
        return f"获取天气信息失败: {str(e)}"

def generate_ai_id(name: str = None) -> str:
    """生成AI-ID的工具"""
    try:
        # 生成唯一的AI-ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = f"AI-{timestamp}"
        
        if name:
            return f"为 {name} 生成的AI-ID: {unique_id}"
        else:
            return f"生成的AI-ID: {unique_id}"
    except Exception as e:
        return f"生成AI-ID失败: {str(e)}"

def generate_frequency(ai_id: str, personality_type: str = "P", ai_type: str = "A") -> str:
    """生成频率编号的工具"""
    try:
        # 生成频率编号
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        frequency = f"F-{personality_type}{ai_type}-{timestamp}"
        
        return f"为AI-ID {ai_id} 生成的频率编号: {frequency}"
    except Exception as e:
        return f"生成频率编号失败: {str(e)}"

def analyze_image(image_data: str, analysis_type: str = "general") -> str:
    """图片分析工具
    
    Args:
        image_data: 图片的Base64编码或URL
        analysis_type: 分析类型，可以是'general'(一般描述), 'objects'(物体检测), 'text'(文字识别)
    
    Returns:
        图片分析结果的描述
    """
    try:
        # 创建ImageProcessor实例
        processor = ImageProcessor()
        
        # 判断输入类型
        if image_data.startswith(('http://', 'https://', 'data:image')):
            # 处理URL或数据地址
            image = ImageData(url=image_data)
        else:
            # 尝试处理为Base64编码
            try:
                content = base64.b64decode(image_data)
                image = ImageData(content=content)
            except Exception as e:
                return f"无法解析图片数据: {str(e)}"
        
        # 使用OpenAI或其他服务分析图片
        # 这里我们模拟分析结果，实际实现中应调用相应的API
        if analysis_type == "general":
            return "这是一张图片的一般描述。在实际实现中，这里应调用图像分析API来获取图片的详细内容描述。"
        elif analysis_type == "objects":
            return "已检测到图片中的物体。在实际实现中，这里应调用物体检测 API 来识别图片中的物体。"
        elif analysis_type == "text":
            return "已提取图片中的文字。在实际实现中，这里应调用OCR API 来提取图片中的文字。"
        else:
            return f"不支持的分析类型: {analysis_type}"
    except Exception as e:
        return f"分析图片时出错: {str(e)}"

def process_document(document_url: str = None, action: str = "analyze") -> str:
    """文档处理工具
    
    Args:
        document_url: 文档的URL路径，如果不提供，将尝试使用最近上传的文档
        action: 要执行的操作，可以是'analyze'(分析内容), 'summarize'(生成摘要), 'extract'(提取信息)
    
    Returns:
        文档处理结果的描述
    """
    import logging
    import os
    
    logging.debug(f"Processing document: {document_url} with action: {action}")
    
    try:
        # 检查文档URL是否有效
        if not document_url:
            # 如果没有提供文档URL，尝试查找最近上传的文档
            logging.debug("No document URL provided, trying to find the most recent document")
            # 尝试在不同的上传目录中查找
            upload_dirs = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads', 'document'),
                os.path.join(os.getcwd(), 'uploads', 'document'),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'document')
            ]
            
            most_recent_file = None
            most_recent_time = 0
            
            for upload_dir in upload_dirs:
                if os.path.exists(upload_dir) and os.path.isdir(upload_dir):
                    logging.debug(f"Checking upload directory: {upload_dir}")
                    for file in os.listdir(upload_dir):
                        file_path = os.path.join(upload_dir, file)
                        if os.path.isfile(file_path):
                            file_time = os.path.getmtime(file_path)
                            if file_time > most_recent_time:
                                most_recent_time = file_time
                                most_recent_file = file_path
            
            if most_recent_file:
                document_url = most_recent_file
                logging.debug(f"Found most recent document: {document_url}")
            else:
                return "未找到最近上传的文档，请提供文档URL"
        
        # 获取文档路径
        # 如果URL是相对路径，则将其转换为绝对路径
        if isinstance(document_url, str) and document_url.startswith('/'):
            # 获取文件名部分
            filename = os.path.basename(document_url)
            # 尝试多种可能的基础路径
            base_dirs = [
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),  # backend/
                os.getcwd(),  # 当前工作目录
                os.path.join(os.getcwd(), 'backend')  # 当前工作目录/backend
            ]
            
            # 尝试多种可能的子目录
            subdirs = [
                '',  # 直接在基础目录下
                'uploads/document/',  # 在uploads/document子目录下
                'uploads/',  # 在uploads子目录下
                document_url.lstrip('/').rsplit('/', 1)[0] + '/' if '/' in document_url else ''  # 使用URL中的目录结构
            ]
            
            # 生成所有可能的路径组合
            possible_paths = []
            for base_dir in base_dirs:
                for subdir in subdirs:
                    path = os.path.join(base_dir, subdir, filename)
                    possible_paths.append(path)
                    # 同时尝试不带uploads前缀的路径
                    if 'uploads/' in subdir:
                        path2 = os.path.join(base_dir, subdir.replace('uploads/', ''), filename)
                        possible_paths.append(path2)
            
            # 添加原始路径转换
            for base_dir in base_dirs:
                possible_paths.append(os.path.join(base_dir, document_url.lstrip('/')))
            
            # 尝试所有可能的路径
            document_path = None
            for path in possible_paths:
                if os.path.exists(path) and os.path.isfile(path):
                    document_path = path
                    logging.debug(f"Found document at path: {document_path}")
                    break
                    
            if not document_path:
                document_path = document_url  # 如果找不到，使用原始URL作为备选
        else:
            document_path = document_url  # 如果不是以/开头的路径，直接使用
            
        # 如果文件不存在，尝试其他可能的路径
        if not os.path.exists(document_path):
            # 尝试在不同的目录下查找文件
            possible_paths = [
                # 原始路径
                document_path,
                # 尝试使用项目根目录下的uploads目录
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads', document_url.lstrip('/')),
                # 尝试使用当前工作目录
                os.path.join(os.getcwd(), document_url.lstrip('/')),
                # 尝试使用当前工作目录下的uploads目录
                os.path.join(os.getcwd(), 'uploads', document_url.lstrip('/')),
                # 尝试使用backend目录下的uploads目录
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', document_url.lstrip('/'))
            ]
            
            # 尝试所有可能的路径
            for path in possible_paths:
                logging.debug(f"Trying path: {path}")
                if os.path.exists(path):
                    document_path = path
                    logging.debug(f"Found document at: {document_path}")
                    break
        
        logging.debug(f"Document path: {document_path}")
        
        # 检查文件是否存在
        if not os.path.exists(document_path):
            # 尝试从项目根目录查找
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            logging.debug(f"Project root: {project_root}")
            
            # 如果文档URL是相对路径，尝试从项目根目录查找
            if isinstance(document_url, str) and document_url.startswith('/'):
                root_path = os.path.join(project_root, document_url.lstrip('/'))
                logging.debug(f"Trying root path: {root_path}")
                if os.path.exists(root_path):
                    document_path = root_path
                    logging.debug(f"Found document at root path: {document_path}")
                else:
                    # 如果还是找不到，尝试最后一次扫描所有uploads目录
                    logging.debug("Scanning all uploads directories for the file...")
                    filename = os.path.basename(document_url)
                    found = False
                    
                    for root, dirs, files in os.walk(project_root):
                        if 'uploads' in root and filename in files:
                            document_path = os.path.join(root, filename)
                            logging.debug(f"Found document during scan: {document_path}")
                            found = True
                            break
                    
                    if not found:
                        return f"文档不存在: {document_url}"
            else:
                return f"文档不存在: {document_url}"
        
        # 读取文档内容
        try:
            with open(document_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 如果使用UTF-8读取失败，尝试使用其他编码
            try:
                with open(document_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except UnicodeDecodeError:
                return f"无法解析文档编码: {document_url}"
        except Exception as e:
            return f"读取文档时出错: {str(e)}"
        
        # 根据操作类型处理文档
        if action == "analyze":
            # 分析文档内容
            if len(content) > 1000:
                preview = content[:1000] + "..."
            else:
                preview = content
            
            return f"文档内容分析\n\n文档路径: {document_url}\n文档大小: {os.path.getsize(document_path)} 字节\n内容预览:\n{preview}"
        
        elif action == "summarize":
            # 生成文档摘要
            return f"文档摘要\n\n文档路径: {document_url}\n文档大小: {os.path.getsize(document_path)} 字节\n摘要: 这是一个文本文档，包含约 {len(content)} 个字符。在实际实现中，这里应调用文本摘要API来生成文档的摘要。"
        
        elif action == "extract":
            # 提取文档信息
            return f"文档信息提取\n\n文档路径: {document_url}\n文档大小: {os.path.getsize(document_path)} 字节\n提取的信息: 在实际实现中，这里应调用信息提取API来从文档中提取结构化信息。"
        
        else:
            return f"不支持的操作类型: {action}"
    
    except Exception as e:
        logging.exception(f"Error processing document: {str(e)}")
        return f"处理文档时出错: {str(e)}"
