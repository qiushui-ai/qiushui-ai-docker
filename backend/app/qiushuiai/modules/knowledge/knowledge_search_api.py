from typing import List, Dict, Any, Optional, Annotated
from fastapi import APIRouter, Body
import logging
import uuid as uuid_module

from sqlmodel import Session, select
from qiushuiai.core.db import engine
from qiushuiai.core.response import BaseResponse, success_response
from qiushuiai.modules.knowledge.processors.vector_search import VectorSearchService
from qiushuiai.schemas.knowledge import KbDocument, KbKnowledge

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge-search", tags=["knowledge-search"])


def search_similar_content(
    query: str,
    knowledge_base_id: Optional[int] = None,
    document_id: Optional[int] = None,
    limit: int = 5,
    similarity_threshold: float = 0.3
) -> List[Dict[str, Any]]:
    """
    搜索相似内容的工具函数
    """
    try:
        with Session(engine) as session:
            search_service = VectorSearchService(session)
            
            if document_id:
                results = search_service.search_by_document_id(
                    document_id=document_id,
                    query=query,
                    limit=limit
                )
            else:
                results = search_service.search_similar_chunks(
                    query=query,
                    knowledge_base_id=knowledge_base_id,
                    limit=limit,
                    similarity_threshold=similarity_threshold
                )
            print(f"==search_similar_content===results: {results}")
            formatted_results = []
            for result in results:
                formatted_result = {
                    "content": result.get("content", ""),
                    "similarity_score": result.get("similarity_score", 0.0),
                    "document_id": result.get("document_id"),
                    "chunk_id": result.get("chunk_id"),
                    "position": result.get("position", 0)
                }
                formatted_results.append(formatted_result)
            
            logger.info(f"===向量搜索完成，找到 {len(formatted_results)} 个相关结果")
            return formatted_results
            
    except Exception as e:
        logger.error(f"向量搜索失败: {str(e)}")
        return []


def get_available_documents(knowledge_base_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    获取可用的文档列表
    """
    try:
        with Session(engine) as session:
            if knowledge_base_id:
                statement = select(KbDocument).where(KbDocument.knowledge_base_id == knowledge_base_id)
            else:
                statement = select(KbDocument)
            
            documents = session.exec(statement).all()
            
            formatted_documents = []
            for doc in documents:
                formatted_doc = {
                    "document_id": doc.id,
                    "document_name": doc.title,
                    "knowledge_base_id": doc.knowledge_base_id,
                    "filename": doc.filename,
                    "file_size": doc.file_size,
                    "status": doc.status
                }
                formatted_documents.append(formatted_doc)
            
            logger.info(f"获取到 {len(formatted_documents)} 个文档")
            return formatted_documents
            
    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}")
        return []


def get_available_knowledge_bases() -> List[Dict[str, Any]]:
    """
    获取可用的知识库列表
    """
    try:
        with Session(engine) as session:
            statement = select(KbKnowledge)
            knowledge_bases = session.exec(statement).all()
            
            formatted_kbs = []
            for kb in knowledge_bases:
                formatted_kb = {
                    "knowledge_base_id": kb.id,
                    "knowledge_base_name": kb.name,
                    "description": kb.description,
                    "index_status": kb.index_status
                }
                formatted_kbs.append(formatted_kb)
            
            logger.info(f"获取到 {len(formatted_kbs)} 个知识库")
            return formatted_kbs
            
    except Exception as e:
        logger.error(f"获取知识库列表失败: {str(e)}")
        return []


# -------------------- API 接口 --------------------

@router.post("/search-multiple-knowledge-bases", response_model=BaseResponse[str])
def api_search_multiple_knowledge_bases(
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """
    在多个知识库中搜索相关内容

    Body参数:
    - query: str, 搜索查询文本
    - knowledge_base_ids: List[int], 指定要搜索的知识库ID列表（必填）
    - limit: int, 每个知识库返回结果数量限制，默认5
    """
    query: str = request_data.get("query")
    knowledge_base_ids: List[int] = request_data.get("knowledge_base_ids")
    limit: int = request_data.get("limit", 5)
    similarity_threshold: float = request_data.get("similarity_threshold", 0.5)

    print(f"query: {query} - knowledge_base_ids: {knowledge_base_ids} - limit: {limit} - similarity_threshold: {similarity_threshold}")

    all_results = []

    try:
        # 在指定的知识库中逐个搜索
        for kb_id in knowledge_base_ids:
            results = search_similar_content(
                query=query,
                knowledge_base_id=kb_id,
                limit=limit,
                similarity_threshold=similarity_threshold
            )
            if results:
                all_results.extend(results)

        if not all_results:
            return success_response(f"未找到相关内容。")

        all_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        response = f"找到 {len(all_results)} 个相关内容：\n\n"
        for i, result in enumerate(all_results, 1):
            response += f"{i}. 内容: {result['content']}\n"
            response += f"   相似度: {result['similarity_score']:.2f}\n"
            response += f"   文档ID: {result['document_id']}\n"
            response += f"   知识库ID: {result.get('knowledge_base_id', '未知')}\n\n"

        return success_response(response)
    except Exception as e:
        logger.error(f"搜索知识库失败: {str(e)}")
        return success_response(f"搜索失败: {str(e)}")


@router.post("/search-in-document", response_model=BaseResponse[str])
def api_search_in_document(
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """
    在指定文档中搜索相关内容

    Body参数:
    - query: str, 搜索查询文本
    - document_id: int, 文档ID
    - limit: int, 返回结果数量限制，默认5
    """
    query: str = request_data.get("query")
    document_id: int = request_data.get("document_id")
    limit: int = request_data.get("limit", 5)

    try:
        results = search_similar_content(
            query=query,
            document_id=document_id,
            limit=limit
        )

        if not results:
            return success_response(f"在文档 {document_id} 中未找到相关内容。")

        response = f"在文档 {document_id} 中找到 {len(results)} 个相关内容：\n\n"
        for i, result in enumerate(results, 1):
            response += f"{i}. 内容: {result['content']}\n"
            response += f"   相似度: {result['similarity_score']:.2f}\n"
            response += f"   位置: {result['position']}\n\n"

        return success_response(response)
    except Exception as e:
        logger.error(f"在文档中搜索失败: {str(e)}")
        return success_response(f"搜索失败: {str(e)}")


@router.post("/list-available-knowledge-bases", response_model=BaseResponse[str])
def api_list_available_knowledge_bases() -> Any:
    """
    列出所有可用的知识库
    """
    try:
        knowledge_bases = get_available_knowledge_bases()
        if not knowledge_bases:
            return success_response("当前没有可用的知识库。")

        response = f"找到 {len(knowledge_bases)} 个知识库：\n\n"
        for kb in knowledge_bases:
            response += f"- ID: {kb['knowledge_base_id']}\n"
            response += f"  名称: {kb['knowledge_base_name']}\n"
            response += f"  描述: {kb['description']}\n"
            response += f"  状态: {kb['index_status']}\n\n"

        return success_response(response)
    except Exception as e:
        logger.error(f"获取知识库列表失败: {str(e)}")
        return success_response(f"获取知识库列表失败: {str(e)}")


@router.post("/list-available-documents-multiple", response_model=BaseResponse[str])
def api_list_available_documents_multiple(
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """
    列出多个知识库中可用的文档

    Body参数:
    - knowledge_base_id: Optional[int], 指定知识库ID，可选
    """
    knowledge_base_id: Optional[int] = request_data.get("knowledge_base_id")

    # 构建知识库ID列表
    knowledge_base_ids = []
    with Session(engine) as session:
        statement = select(KbKnowledge)
        all_kbs = session.exec(statement).all()
        for kb in all_kbs:
            knowledge_base_ids.append(kb.id)

    all_documents = []

    try:
        if knowledge_base_id is not None:
            documents = get_available_documents(knowledge_base_id)
            if documents:
                all_documents.extend(documents)
        else:
            for kb_id in knowledge_base_ids:
                documents = get_available_documents(kb_id)
                if documents:
                    all_documents.extend(documents)

        if not all_documents:
            return success_response("未找到可用文档。")

        response = f"找到 {len(all_documents)} 个文档：\n\n"
        for doc in all_documents:
            response += f"- ID: {doc['document_id']}\n"
            response += f"  名称: {doc['document_name']}\n"
            response += f"  知识库ID: {doc['knowledge_base_id']}\n"
            response += f"  状态: {doc['status']}\n\n"

        return success_response(response)
    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}")
        return success_response(f"获取文档列表失败: {str(e)}")
