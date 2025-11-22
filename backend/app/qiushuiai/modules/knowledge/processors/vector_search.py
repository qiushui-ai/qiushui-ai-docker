"""
向量检索服务 - 使用 PGVector 进行向量相似性搜索
"""

import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal

from sqlmodel import Session, select

from qiushuiai.schemas.knowledge import KbChunk, KbDocument, KbKnowledge
from qiushuiai.modules.knowledge.processors.vector_store import VectorStoreService

logger = logging.getLogger(__name__)


class VectorSearchService:
    """向量检索服务类"""
    
    def __init__(self, session: Session):
        self.session = session
        self.vector_store = VectorStoreService(session)
    
    def search_similar_chunks(
        self, 
        query: str, 
        knowledge_base_id: Optional[int] = None,
        limit: int = 10,
        similarity_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        搜索相似的分块
        
        Args:
            query: 搜索查询
            knowledge_base_id: 知识库ID（可选）
            limit: 返回结果数量限制
            similarity_threshold: 相似度阈值
            
        Returns:
            相似分块列表
        """
        try:
            if knowledge_base_id:
                # 获取知识库UUID作为集合名称
                knowledge_statement = select(KbKnowledge).where(KbKnowledge.id == knowledge_base_id)
                knowledge = self.session.exec(knowledge_statement).first()
                
                if not knowledge:
                    logger.warning(f"知识库 {knowledge_base_id} 不存在")
                    return []
                
                collection_name = str(knowledge.uuid)
                filter_dict = {"knowledge_base_id": knowledge_base_id}
            else:
                # 在所有知识库中搜索（需要获取所有集合）
                collections = self._get_all_collections()
                all_results = []
                
                for collection_name in collections:
                    results = self.vector_store.search_similar(
                        query=query,
                        collection_name=collection_name,
                        k=limit,
                        filter_dict=None
                    )
                    all_results.extend(results)
                
                # 按相似度排序并过滤
                all_results.sort(key=lambda x: x["similarity_score"], reverse=True)
                all_results = [r for r in all_results if r["similarity_score"] >= similarity_threshold]
                
                return all_results[:limit]
            
            # 在指定集合中搜索
            results = self.vector_store.search_similar(
                query=query,
                collection_name=collection_name,
                k=limit * 2,  # 获取更多候选
                filter_dict=filter_dict
            )
           
            
            # 过滤相似度阈值
            print("--------------------------------")
            print(f"similarity_threshold: {similarity_threshold}")
            print(f"results---: {results}")
            filtered_results = [r for r in results if r["similarity_score"] >= similarity_threshold]
            # print(f"-----rfiltered_resultsesults: {filtered_results}")
            
            # 限制结果数量
            filtered_results = filtered_results[:limit]
            
            logger.info(f"-----向量搜索完成，找到 {len(filtered_results)} 个相关结果")
            # print(f"-----向量搜索完成，找到 {filtered_results} ")
            return filtered_results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            return []
    
    def search_by_document_id(
        self, 
        document_id: int, 
        query: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        在指定文档中搜索相似分块
        
        Args:
            document_id: 文档ID
            query: 搜索查询
            limit: 返回结果数量限制
            
        Returns:
            相似分块列表
        """
        try:
            # 获取文档信息
            statement = select(KbDocument).where(KbDocument.id == document_id)
            document = self.session.exec(statement).first()
            
            if not document:
                logger.warning(f"文档 {document_id} 不存在")
                return []
            
            # 获取知识库UUID作为集合名称
            knowledge_statement = select(KbKnowledge).where(KbKnowledge.id == document.knowledge_base_id)
            knowledge = self.session.exec(knowledge_statement).first()
            
            if not knowledge:
                logger.warning(f"知识库 {document.knowledge_base_id} 不存在")
                return []
            
            collection_name = str(knowledge.uuid)
            filter_dict = {"document_id": document_id}
            
            results = self.vector_store.search_similar(
                query=query,
                collection_name=collection_name,
                k=limit,
                filter_dict=filter_dict
            )
            
            return results
            
        except Exception as e:
            logger.error(f"文档内搜索失败: {str(e)}")
            return []
    
    def get_chunk_by_id(self, chunk_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取分块详情"""
        try:
            statement = select(KbChunk).where(KbChunk.id == chunk_id)
            chunk = self.session.exec(statement).first()
            
            if not chunk:
                return None
            
            return {
                "chunk_id": chunk.id,
                "chunk_uuid": str(chunk.uuid),
                "document_id": chunk.document_id,
                "content": chunk.content,
                "position": chunk.position,
                "extra_data": chunk.extra_data,
                "token_count": chunk.token_count,
                "similarity_threshold": float(chunk.similarity_threshold),
                "tenant_id": chunk.tenant_id
            }
            
        except Exception as e:
            logger.error(f"获取分块详情失败: {str(e)}")
            return None
    
    def _get_all_collections(self) -> List[str]:
        """获取所有集合名称（使用知识库UUID）"""
        # 从数据库查询所有知识库，然后生成集合名称
        statement = select(KbKnowledge.uuid)
        knowledge_uuids = self.session.exec(statement).all()
        
        collections = [str(uuid) for uuid in knowledge_uuids]
        return collections 