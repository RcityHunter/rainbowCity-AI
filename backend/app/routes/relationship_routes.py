# backend/app/routes/relationship_routes.py
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import logging

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.models.relationship import Relationship, RelationshipStatus
from app.utils.relationship_utils import (
    calculate_interaction_frequency,
    calculate_emotional_density,
    calculate_collaboration_depth,
    calculate_ris,
    update_relationship_status,
)
from app.db import create, query, update as db_update

# 创建路由器
router = APIRouter(prefix="/relationships", tags=["关系管理"])

# 定义请求和响应模型
class RelationshipCreate(BaseModel):
    ai_id: str = Field(..., description="AI ID")
    human_id: str = Field(..., description="人类用户 ID")
    relationship_id: Optional[str] = Field(None, description="关系 ID，如不提供将自动生成")
    init_timestamp: Optional[str] = Field(None, description="初始化时间戳")
    last_active_time: Optional[str] = Field(None, description="最后活跃时间")
    status: Optional[str] = Field(None, description="关系状态")
    
class RelationshipCreateResponse(BaseModel):
    message: str
    relationship_id: str
    
class RelationshipStatusUpdate(BaseModel):
    status: str = Field(..., description="新的关系状态")
    
class RelationshipStatusResponse(BaseModel):
    status: str
    
class RelationshipUpdateResponse(BaseModel):
    message: str
    
class RisComponent(BaseModel):
    interaction_frequency: float
    emotional_density: float
    collaboration_depth: float
    
class RisResponse(BaseModel):
    ris: float
    components: RisComponent

@router.post("", response_model=RelationshipCreateResponse, status_code=201)
async def create_relationship(relationship: RelationshipCreate):
    """
    创建一个新的 AI 与人类之间的关系
    """
    try:
        # 转换为字典以便处理
        data = relationship.dict(exclude_unset=True)
        
        # 生成 relationship_id（如果未提供）
        if "relationship_id" not in data or not data["relationship_id"]:
            data["relationship_id"] = f"rel-{str(uuid.uuid4())}"
            
        # 设置时间戳（如果未提供）
        now = datetime.utcnow().isoformat()
        if "init_timestamp" not in data or not data["init_timestamp"]:
            data["init_timestamp"] = now
        if "last_active_time" not in data or not data["last_active_time"]:
            data["last_active_time"] = now
            
        # 设置默认状态（如果未提供）
        if "status" not in data or not data["status"]:
            data["status"] = RelationshipStatus.ACTIVE.value
            
        # 存储到 SurrealDB
        result = create('relationship', data)
        
        if result:
            logging.info(f"Successfully created relationship: {data['relationship_id']}")
            return {
                "message": "Relationship created", 
                "relationship_id": data["relationship_id"]
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create relationship")
            
    except Exception as e:
        logging.error(f"Error creating relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create relationship: {str(e)}")

@router.get("/{relationship_id}", response_model=Dict[str, Any])
async def get_relationship(relationship_id: str):
    """
    获取特定关系的详细信息
    
    Args:
        relationship_id: 关系 ID
    """
    try:
        # 查询 SurrealDB
        results = query('relationship', {'relationship_id': relationship_id})
        
        # 处理查询结果
        if not results:
            raise HTTPException(status_code=404, detail="Relationship not found")
            
        # 返回找到的第一个匹配结果
        return results[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error retrieving relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve relationship: {str(e)}")

@router.put("/{relationship_id}", response_model=RelationshipUpdateResponse)
async def update_relationship(relationship_id: str, data: Dict[str, Any]):
    """
    更新特定关系的详细信息
    
    Args:
        relationship_id: 关系 ID
    """
    try:
        # 首先查询关系是否存在
        results = query('relationship', {'relationship_id': relationship_id})
        if not results:
            raise HTTPException(status_code=404, detail="Relationship not found")
            
        # 使用 SurrealDB 的更新函数更新关系
        result = db_update('relationship', relationship_id, data)
        
        if result:
            logging.info(f"Successfully updated relationship: {relationship_id}")
            return {"message": "Relationship updated"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update relationship")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update relationship: {str(e)}")

@router.get("/ai/{ai_id}", response_model=List[Dict[str, Any]])
async def get_ai_relationships(ai_id: str):
    """
    获取特定 AI 的所有关系
    
    Args:
        ai_id: AI ID
    """
    try:
        # 查询 SurrealDB
        results = query('relationship', {'ai_id': ai_id})
        
        # 返回结果，可能是空列表
        return results
        
    except Exception as e:
        logging.error(f"Error retrieving AI relationships: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve AI relationships: {str(e)}")

@router.get("/human/{human_id}", response_model=List[Dict[str, Any]])
async def get_user_relationships(human_id: str):
    """
    获取特定用户的所有关系
    
    Args:
        human_id: 人类用户 ID
    """
    try:
        # 查询 SurrealDB
        results = query('relationship', {'human_id': human_id})
        
        # 返回结果，可能是空列表
        return results
        
    except Exception as e:
        logging.error(f"Error retrieving user relationships: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user relationships: {str(e)}")

@router.get("/{relationship_id}/status", response_model=RelationshipStatusResponse)
async def get_relationship_status(relationship_id: str):
    """
    获取关系的当前状态
    
    Args:
        relationship_id: 关系 ID
    """
    try:
        # 查询 SurrealDB
        results = query('relationship', {'relationship_id': relationship_id})
        
        # 处理查询结果
        if not results:
            raise HTTPException(status_code=404, detail="Relationship not found")
            
        # 返回状态信息
        relationship = results[0]
        if 'status' in relationship:
            return {"status": relationship['status']}
        else:
            # 如果没有状态字段，默认为活跃状态
            return {"status": RelationshipStatus.ACTIVE.value}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error retrieving relationship status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve relationship status: {str(e)}")

@router.put("/{relationship_id}/status", response_model=RelationshipUpdateResponse)
async def update_relationship_status_route(relationship_id: str, status_update: RelationshipStatusUpdate):
    """
    更新关系的状态
    
    Args:
        relationship_id: 关系 ID
    """
    try:
        # 验证状态是否有效
        try:
            new_status = RelationshipStatus(status_update.status)
            status_value = new_status.value
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_update.status}")

        # 首先查询关系是否存在
        results = query('relationship', {'relationship_id': relationship_id})
        if not results:
            raise HTTPException(status_code=404, detail="Relationship not found")
            
        # 使用 SurrealDB 的更新函数更新状态
        update_data = {"status": status_value}
        result = db_update('relationship', relationship_id, update_data)
        
        if result:
            logging.info(f"Successfully updated relationship status: {relationship_id} to {status_value}")
            return {"message": "Relationship status updated"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update relationship status")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating relationship status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update relationship status: {str(e)}")

@router.get("/{relationship_id}/ris", response_model=RisResponse)
async def get_relationship_ris(relationship_id: str):
    """
    获取关系的强度评分 (RIS)
    
    Args:
        relationship_id: 关系 ID
    """
    try:
        # 查询 SurrealDB
        results = query('relationship', {'relationship_id': relationship_id})
        
        # 处理查询结果
        if not results:
            raise HTTPException(status_code=404, detail="Relationship not found")
            
        # 获取关系数据
        relationship = results[0]
        
        # 计算 RIS 分数
        interaction_count = relationship.get('interaction_count', 0)
        emotional_resonance_count = relationship.get('emotional_resonance_count', 0)
        
        interaction_frequency = calculate_interaction_frequency(interaction_count)
        emotional_density = calculate_emotional_density(emotional_resonance_count)
        collaboration_depth = calculate_collaboration_depth(relationship)
        
        ris = calculate_ris(interaction_frequency, emotional_density, collaboration_depth)
        
        # 返回结果以及各个组成部分的分数
        return {
            "ris": ris,
            "components": {
                "interaction_frequency": interaction_frequency,
                "emotional_density": emotional_density,
                "collaboration_depth": collaboration_depth
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error calculating relationship RIS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate relationship RIS: {str(e)}")
