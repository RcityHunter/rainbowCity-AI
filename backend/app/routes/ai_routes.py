from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.utils.ai_utils import generate_ai_id, generate_frequency_number, get_frequency_info, get_personality_info, get_ai_type_info
from app.models.frequency import FrequencyNumber
from app.db import create, query

# 创建路由器
router = APIRouter(prefix="/ai", tags=["AI服务"])

# 定义请求和响应模型
class AiIdRequest(BaseModel):
    visible_number: int = Field(..., description="可见编号")

class AiIdResponse(BaseModel):
    id: str = Field(..., description="AI-ID")
    visible_number: int = Field(..., description="可见编号")
    uuid: str = Field(..., description="UUID")
    created_at: str = Field(..., description="创建时间")

class AiValuesDict(BaseModel):
    # 这里可以根据实际需要定义更具体的字段
    pass

class FrequencyRequest(BaseModel):
    ai_id: str = Field(..., description="AI-ID")
    awakener_id: str = Field(..., description="唤醒者ID")
    ai_values: Dict[str, Any] = Field(..., description="AI价值观")
    ai_personality: str = Field(..., description="AI人格")
    ai_type: str = Field(..., description="AI类型")

class FrequencyResponse(BaseModel):
    frequency_number: str = Field(..., description="频率编号")
    ai_id: str = Field(..., description="AI-ID")
    created_at: str = Field(..., description="创建时间")
    components: Dict[str, Any] = Field(..., description="频率编号组成部分")

class ValueCodeInfo(BaseModel):
    code: str
    value: str
    symbol: str
    color: str

class PersonalityCodeInfo(BaseModel):
    code: str
    description: str

class AiTypeCodeInfo(BaseModel):
    code: str
    description: str

class FrequencyComponents(BaseModel):
    value_code: ValueCodeInfo
    sequence_number: str
    personality_code: PersonalityCodeInfo
    ai_type_code: AiTypeCodeInfo
    hash_signature: str

class FrequencyDetailResponse(BaseModel):
    frequency_number: str
    components: FrequencyComponents
    ai_id: Optional[str] = None
    created_at: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    service: str

# 生成 AI-ID 并存储到 SurrealDB
@router.post("/generate_id", response_model=AiIdResponse, status_code=201)
async def generate_ai_id_api(request: AiIdRequest):
    """生成 AI-ID 并存储到 SurrealDB"""
    try:
        visible_number = request.visible_number
        
        # 生成AI-ID
        ai_id = generate_ai_id(visible_number)
        logging.info(f"Generated AI-ID: {ai_id.ai_id}")
        
        # 准备数据并存储
        ai_id_data = ai_id.to_dict()
        
        # 使用同步包装的数据库操作
        result = create('ai_id', ai_id_data)
        
        # 如果成功存储，记录日志
        if result:
            logging.info(f"Successfully stored AI-ID: {ai_id.ai_id}")
        
        # 返回响应
        return {
            'id': ai_id.ai_id,
            'visible_number': visible_number,
            'uuid': ai_id.uuid,
            'created_at': result.get('created_at', datetime.now().isoformat()) if result else datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error generating AI-ID: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate AI-ID: {str(e)}")

# 根据 AI-ID 获取 AI-ID 信息
@router.get("/ai_ids/{ai_id_str}", response_model=Dict[str, Any])
async def get_ai_id(ai_id_str: str):
    """根据 AI-ID 获取 AI-ID 信息"""
    if not ai_id_str:
        raise HTTPException(status_code=400, detail="Missing AI-ID")
        
    try:
        # 使用同步包装的数据库查询
        results = query('ai_id', {'ai_id': ai_id_str})
        
        # 处理查询结果
        if not results:
            raise HTTPException(status_code=404, detail="AI-ID not found")
            
        # 返回找到的第一个匹配结果
        return results[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error retrieving AI-ID: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve AI-ID: {str(e)}")

# 生成AI频率编号
@router.post("/generate_frequency", response_model=FrequencyResponse)
async def generate_frequency_api(request: FrequencyRequest):
    """生成AI频率编号并存储到数据库"""
    try:
        # 生成频率编号
        frequency_number_str = generate_frequency_number(
            ai_values=request.ai_values,
            ai_personality=request.ai_personality,
            ai_type=request.ai_type,
            ai_id=request.ai_id,
            awakener_id=request.awakener_id
        )
        
        # 解析频率编号
        frequency_obj = FrequencyNumber.from_string(frequency_number_str, request.ai_id)
        if not frequency_obj:
            raise HTTPException(status_code=500, detail="Failed to parse frequency number")
            
        # 准备返回数据
        frequency_data = frequency_obj.to_dict()
        
        # 添加关联的AI-ID
        frequency_data['ai_id'] = request.ai_id
        
        # 添加创建时间
        frequency_data['created_at'] = datetime.now().isoformat()
        
        # 存储到数据库
        result = create('frequency', frequency_data)
        
        # 获取颜色、符号和价值观信息
        value_info = get_frequency_info(frequency_obj.value_code)
        personality_info = get_personality_info(frequency_obj.personality_code)
        type_info = get_ai_type_info(frequency_obj.ai_type_code)
        
        # 构建响应
        response_data = {
            'frequency_number': frequency_number_str,
            'ai_id': request.ai_id,
            'created_at': result.get('created_at', datetime.now().isoformat()) if result else datetime.now().isoformat(),
            'components': {
                'value_code': {
                    'code': frequency_obj.value_code,
                    'value': value_info['value'],
                    'symbol': value_info['symbol'],
                    'color': value_info['color']
                },
                'sequence_number': frequency_obj.sequence_number,
                'personality_code': {
                    'code': frequency_obj.personality_code,
                    'description': personality_info
                },
                'ai_type_code': {
                    'code': frequency_obj.ai_type_code,
                    'description': type_info
                },
                'hash_signature': frequency_obj.hash_signature
            }
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error generating frequency number: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate frequency number: {str(e)}")

# 获取频率编号详情
@router.get("/frequency/{frequency_number}", response_model=FrequencyDetailResponse)
async def get_frequency(frequency_number: str):
    """根据频率编号获取详细信息"""
    if not frequency_number:
        raise HTTPException(status_code=400, detail="Missing frequency number")
        
    try:
        # 查询数据库
        results = query('frequency', {'frequency_number': frequency_number})
        
        if not results:
            # 如果数据库中没有找到，尝试解析频率编号
            frequency_obj = FrequencyNumber.from_string(frequency_number)
            if not frequency_obj:
                raise HTTPException(status_code=400, detail="Invalid frequency number format")
                
            # 获取颜色、符号和价值观信息
            value_info = get_frequency_info(frequency_obj.value_code)
            personality_info = get_personality_info(frequency_obj.personality_code)
            type_info = get_ai_type_info(frequency_obj.ai_type_code)
            
            # 构建响应
            response_data = {
                'frequency_number': frequency_number,
                'components': {
                    'value_code': {
                        'code': frequency_obj.value_code,
                        'value': value_info['value'],
                        'symbol': value_info['symbol'],
                        'color': value_info['color']
                    },
                    'sequence_number': frequency_obj.sequence_number,
                    'personality_code': {
                        'code': frequency_obj.personality_code,
                        'description': personality_info
                    },
                    'ai_type_code': {
                        'code': frequency_obj.ai_type_code,
                        'description': type_info
                    },
                    'hash_signature': frequency_obj.hash_signature
                },
                'ai_id': None,
                'created_at': None
            }
            
            return response_data
        
        # 如果数据库中找到了记录
        stored_data = results[0]
        frequency_obj = FrequencyNumber.from_string(frequency_number, stored_data.get('ai_id'))
        
        # 获取颜色、符号和价值观信息
        value_info = get_frequency_info(frequency_obj.value_code)
        personality_info = get_personality_info(frequency_obj.personality_code)
        type_info = get_ai_type_info(frequency_obj.ai_type_code)
        
        # 构建响应
        response_data = {
            'frequency_number': frequency_number,
            'components': {
                'value_code': {
                    'code': frequency_obj.value_code,
                    'value': value_info['value'],
                    'symbol': value_info['symbol'],
                    'color': value_info['color']
                },
                'sequence_number': frequency_obj.sequence_number,
                'personality_code': {
                    'code': frequency_obj.personality_code,
                    'description': personality_info
                },
                'ai_type_code': {
                    'code': frequency_obj.ai_type_code,
                    'description': type_info
                },
                'hash_signature': frequency_obj.hash_signature
            },
            'ai_id': stored_data.get('ai_id'),
            'created_at': stored_data.get('created_at')
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error retrieving frequency: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve frequency: {str(e)}")

# 添加一个简单的健康检查端点
@router.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "ok", "service": "ai-service"}
