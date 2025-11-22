"""
向量检索API - 提供向量相似性搜索接口
"""

from typing import Any, Optional, Annotated
from fastapi import APIRouter, Body

from qiushuiai.modules.user.deps import CurrentUser, SessionDep
from qiushuiai.core.response import (
    BaseResponse,
    success_response,
    ResponseCode,
    ResponseMessage,
)
from qiushuiai.modules.knowledge.processors.vector_search import VectorSearchService

router = APIRouter(prefix="/vector-search", tags=["vector-search"])


@router.post("/search", response_model=BaseResponse[list])
def search_similar_chunks(
    session: SessionDep,
    current_user: CurrentUser,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """
    向量相似性搜索
    
    请求参数:
    - query: 搜索查询文本
    - knowledge_base_id: 知识库ID（可选）
    - limit: 返回结果数量限制（默认10）
    - similarity_threshold: 相似度阈值（默认0.8）
    """
    query = request_data.get("query")
    knowledge_base_id = request_data.get("knowledge_base_id")
    limit = request_data.get("limit", 10)
    similarity_threshold = request_data.get("similarity_threshold", 0.8)
    
    if not query:
        return success_response(
            data=[],
            message="搜索查询不能为空",
            code=ResponseCode.BAD_REQUEST
        )
    
    # 创建向量搜索服务
    search_service = VectorSearchService(session)
    
    # 执行搜索
    results = search_service.search_similar_chunks(
        query=query,
        knowledge_base_id=knowledge_base_id,
        limit=limit,
        similarity_threshold=similarity_threshold
    )
    
    return success_response(
        data=results,
        message=f"搜索完成，找到 {len(results)} 个相关结果"
    )


@router.post("/search-document", response_model=BaseResponse[list])
def search_in_document(
    session: SessionDep,
    current_user: CurrentUser,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """
    在指定文档中搜索相似分块
    
    请求参数:
    - document_id: 文档ID
    - query: 搜索查询文本
    - limit: 返回结果数量限制（默认5）
    """
    document_id = request_data.get("document_id")
    query = request_data.get("query")
    limit = request_data.get("limit", 5)
    
    if not document_id or not query:
        return success_response(
            data=[],
            message="文档ID和搜索查询不能为空",
            code=ResponseCode.BAD_REQUEST
        )
    
    # 创建向量搜索服务
    search_service = VectorSearchService(session)
    
    # 执行搜索
    results = search_service.search_by_document_id(
        document_id=document_id,
        query=query,
        limit=limit
    )
    
    return success_response(
        data=results,
        message=f"文档内搜索完成，找到 {len(results)} 个相关结果"
    )


@router.get("/chunk/{chunk_id}", response_model=BaseResponse[dict])
def get_chunk_detail(
    session: SessionDep,
    current_user: CurrentUser,
    chunk_id: int
) -> Any:
    """获取分块详情"""
    # 创建向量搜索服务
    search_service = VectorSearchService(session)
    
    # 获取分块详情
    chunk = search_service.get_chunk_by_id(chunk_id)
    
    if not chunk:
        return success_response(
            data=None,
            message="分块不存在",
            code=ResponseCode.NOT_FOUND
        )
    
    return success_response(
        data=chunk,
        message="获取分块详情成功"
    ) 