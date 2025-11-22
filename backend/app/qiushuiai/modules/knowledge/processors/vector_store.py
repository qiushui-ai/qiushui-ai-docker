"""
向量存储服务 - 使用 PGVector 管理向量数据
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_core.documents import Document
from langchain_postgres.vectorstores import PGVector
from langchain_community.embeddings import ZhipuAIEmbeddings
from sqlmodel import Session, select

from qiushuiai.core.config import settings
from qiushuiai.schemas.knowledge import KbDocument, KbChunk

from qiushuiai.core.config import settings
from langchain_community.embeddings import DashScopeEmbeddings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """向量存储服务类"""


    
    def __init__(self, session: Session):
        self.session = session
        # 初始化 DashScope 嵌入模型

        self.embeddings = DashScopeEmbeddings(
            model=settings.DASHSCOPE_EMBEDDING_MODEL,
            dashscope_api_key=settings.DASHSCOPE_API_KEY
        )

        
        
        # 构建数据库连接字符串
        connection_string = (
            f"postgresql+psycopg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
        
        self.connection_string = connection_string
    
    def get_vectorstore(self, collection_name: str) -> PGVector:
        """获取 PGVector 实例"""
        return PGVector(
            embeddings=self.embeddings,
            collection_name=collection_name,
            connection=self.connection_string,
            use_jsonb=True
        )
    
    def add_documents(
        self, 
        documents: List[Document], 
        collection_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        添加文档到向量存储
        
        Args:
            documents: LangChain Document 列表
            collection_name: 集合名称（使用知识库UUID）
            metadata: 集合元数据（包含tenant_id和name）
            
        Returns:
            添加的文档ID列表（使用分块UUID）
        """
        try:
            store = self.get_vectorstore(collection_name)
            # 打印集合信息（将保存到 langchain_pg_collection）
            print(f"=== 集合信息 (langchain_pg_collection) ===")
            print(f"集合名称: {collection_name}")
            print(f"集合元数据: {metadata}")
            
            # 添加元数据到集合
            if metadata:
                store.collection_metadata = metadata

                
            
            # 为每个文档设置自定义ID（使用分块UUID）
            for doc in documents:
                if "chunk_uuid" in doc.metadata:
                    # 设置自定义ID为分块UUID
                    doc.id = doc.metadata["chunk_uuid"]
   
            print(f"documents:{documents}")
            # 添加文档
            doc_ids = store.add_documents(documents)
            
            logger.info(f"成功添加 {len(doc_ids)} 个文档到集合 {collection_name}")
            return doc_ids
            
        except Exception as e:
            logger.error(f"添加文档到向量存储失败: {str(e)}")
            raise
    
    def search_similar(
        self, 
        query: str, 
        collection_name: str,
        k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        在向量存储中搜索相似文档
        
        Args:
            query: 搜索查询
            collection_name: 集合名称（使用知识库UUID）
            k: 返回结果数量
            filter_dict: 过滤条件
            
        Returns:
            搜索结果列表
        """
        try:
            store = self.get_vectorstore(collection_name)
            
            # 执行相似性搜索
            results = store.similarity_search_with_score(
                query, 
                k=k,
                filter=filter_dict
            )
            
            # 格式化结果
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "id": doc.metadata.get("id", ""),
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": 1 - score,  # 转换为相似度分数
                    "document_id": doc.metadata.get("document_id"),
                    "position": doc.metadata.get("position", 0),
                    "tenant_id": doc.metadata.get("tenant_id"),
                    "chunk_uuid": doc.metadata.get("chunk_uuid")
                })
            
            logger.info(f"111111向量搜索完成，找到 {len(formatted_results)} 个相关结果")
            # print(f"-111111向量搜索完成，找到 {formatted_results} ")
            return formatted_results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            return []
    
    def delete_documents(
        self, 
        collection_name: str,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        删除向量存储中的文档
        
        Args:
            collection_name: 集合名称（使用知识库UUID）
            filter_dict: 过滤条件
            
        Returns:
            是否删除成功
        """
        try:
            store = self.get_vectorstore(collection_name)
            
            # 删除文档
            store.delete(filter=filter_dict)
            
            logger.info(f"成功删除集合 {collection_name} 中的文档")
            return True
            
        except Exception as e:
            logger.error(f"删除向量存储文档失败: {str(e)}")
            return False 