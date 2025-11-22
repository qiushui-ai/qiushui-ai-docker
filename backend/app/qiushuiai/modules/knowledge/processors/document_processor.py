"""
文档处理器 - 负责文档分块、向量化和存储
"""

import os
import hashlib
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import logging

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from sqlmodel import Session, select

from qiushuiai.core.config import settings
from qiushuiai.schemas.knowledge import KbDocument, KbKnowledge
from qiushuiai.schemas.chat import ChatConversation, ChatDocument
from qiushuiai.core.db_filters import update_common_fields
from qiushuiai.modules.user.deps import CurrentUser
from qiushuiai.modules.knowledge.processors.vector_store import VectorStoreService
from qiushuiai.modules.knowledge.processors.document_status_manager import DocumentStatusManager

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """文档处理器类"""
    
    def __init__(self, session: Session, current_user: CurrentUser):
        self.session = session
        self.current_user = current_user
        # 初始化向量存储服务
        self.vector_store = VectorStoreService(session)
        # 初始化状态管理器
        self.status_manager = DocumentStatusManager(session, current_user)
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.DOCUMENT_CHUNK_SIZE,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def process_document(self, document: Union[KbDocument, ChatDocument]) -> Dict[str, Any]:
        """
        处理文档：分块、向量化并保存到向量存储
        
        Args:
            document: 文档对象（KbDocument 或 ChatDocument）
            
        Returns:
            处理结果字典
        """
        try:
            logger.info(f"开始处理文档: {document.title}")
            
            # 1. 文档分块
            chunks = self._split_document(document)
            logger.info(f"文档分块完成，共 {len(chunks)} 个块")
            
            # 2. 添加向量到 PGVector
            vector_ids = self._add_vectors_to_store(document, chunks)
            logger.info(f"向量添加到 PGVector 完成，共添加 {len(vector_ids)} 个向量")
            
            # 3. 更新文档状态为已向量化
            embedding_model = "dashscope-text-embedding-v4"
            success = self.status_manager.mark_as_embedded(document, len(chunks), embedding_model)
            if not success:
                logger.error("更新文档状态失败")
                return {
                    "success": False,
                    "error": "更新文档状态失败",
                    "message": "文档处理完成但状态更新失败"
                }
            
            return {
                "success": True,
                "document_id": document.id,
                "chunks_count": len(chunks),
                "vector_ids": vector_ids,
                "message": "文档处理完成"
            }
            
        except Exception as e:
            logger.error(f"文档处理失败: {str(e)}")
            # 更新文档状态为失败
            self.status_manager.mark_as_failed(document)
            return {
                "success": False,
                "error": str(e),
                "message": "文档处理失败"
            }
    
    def _split_document(self, document: Union[KbDocument, ChatDocument]) -> List[Document]:
        """文档分块"""
        if not document.content:
            raise ValueError("文档内容为空")
        
        # 创建 LangChain Document 对象
        doc = Document(
            page_content=document.content,
            metadata={
                "document_id": document.id,
                "tenant_id": document.tenant_id,
                "created_by": self.current_user.id,
                "view_permission": "public",
            }
        )
        
        # 根据文档类型添加相应的关联ID
        if hasattr(document, 'knowledge_base_id') and document.knowledge_base_id:
            doc.metadata["knowledge_base_id"] = document.knowledge_base_id
        elif hasattr(document, 'chat_conversation_id') and document.chat_conversation_id:
            doc.metadata["chat_conversation_id"] = document.chat_conversation_id
        
        # 执行分块
        chunks = self.text_splitter.split_documents([doc])
        return chunks
    
    def _add_vectors_to_store(self, document: Union[KbDocument, ChatDocument], chunks: List[Document]) -> List[str]:
        """添加向量到 PGVector 存储"""
                
        collection_name = None
        collection_metadata = {}
        
        # 判断使用哪个ID来获取UUID
        if hasattr(document, 'knowledge_base_id') and document.knowledge_base_id is not None:
            # 获取知识库信息
            knowledge_statement = select(KbKnowledge).where(KbKnowledge.id == document.knowledge_base_id)
            knowledge = self.session.exec(knowledge_statement).first()
            
            if knowledge:
                collection_name = str(knowledge.uuid)
                collection_metadata = {
                    "tenant_id": knowledge.tenant_id,
                    "name": knowledge.name,
                }
            else:
                raise ValueError(f"知识库不存在: {document.knowledge_base_id}")
                
        elif hasattr(document, 'chat_conversation_id') and document.chat_conversation_id is not None:
            # 获取聊天对话信息
            conversation_statement = select(ChatConversation).where(ChatConversation.id == document.chat_conversation_id)
            conversation = self.session.exec(conversation_statement).first()
            
            if conversation:
                collection_name = str(conversation.uuid)
                collection_metadata = {
                    "tenant_id": conversation.tenant_id,
                    "name": conversation.title or f"对话_{conversation.id}",
                }
            else:
                raise ValueError(f"聊天对话不存在: {document.chat_conversation_id}")
        else:
            # 两者都为空
            raise ValueError("文档必须关联知识库或聊天对话")
        
        # 添加到向量存储
        vector_ids = self.vector_store.add_documents(
            documents=chunks,
            collection_name=collection_name,
            metadata=collection_metadata
        )
        
        return vector_ids