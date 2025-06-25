import os
import json
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from tavily import TavilyClient

router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={404: {"description": "Not found"}},
)

# 定义请求模型
class SearchRequest(BaseModel):
    query: str
    search_depth: Optional[str] = "basic"  # basic 或 advanced
    max_results: Optional[int] = 10
    include_domains: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None
    include_answer: Optional[bool] = True
    include_raw_content: Optional[bool] = False
    include_images: Optional[bool] = False

# 定义响应模型
class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    answer: Optional[str] = None
    query: str

@router.post("", response_model=SearchResponse)
async def search(
    request: SearchRequest
):
    """
    使用 Tavily 搜索引擎执行搜索
    """
    try:
        # 从环境变量获取 API 密钥
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Tavily API key not configured")
        
        # 创建 Tavily 客户端
        client = TavilyClient(api_key=api_key)
        
        # 准备搜索参数
        search_params = {
            "query": request.query,
            "search_depth": request.search_depth,
            "max_results": request.max_results,
            "include_answer": request.include_answer,
            "include_raw_content": request.include_raw_content,
            "include_images": request.include_images,
        }
        
        # 添加可选参数
        if request.include_domains:
            search_params["include_domains"] = request.include_domains
        if request.exclude_domains:
            search_params["exclude_domains"] = request.exclude_domains
            
        # 执行搜索
        response = client.search(**search_params)
        
        # 构建响应
        return SearchResponse(
            results=response.get("results", []),
            answer=response.get("answer"),
            query=request.query
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@router.get("/quick", response_model=SearchResponse)
async def quick_search(
    query: str = Query(..., description="搜索查询")
):
    """
    快速搜索端点，使用默认参数
    """
    try:
        # 从环境变量获取 API 密钥
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Tavily API key not configured")
        
        # 创建 Tavily 客户端
        client = TavilyClient(api_key=api_key)
        
        # 执行搜索
        response = client.search(query=query)
        
        # 构建响应
        return SearchResponse(
            results=response.get("results", []),
            answer=response.get("answer"),
            query=query
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
