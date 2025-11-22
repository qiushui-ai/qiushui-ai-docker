"""
文档状态管理器
负责管理文档的状态流转：uploaded -> extracted -> embedded
"""

import logging
from datetime import datetime
from typing import Union
from sqlmodel import Session

from qiushuiai.schemas.knowledge import KbDocument
from qiushuiai.schemas.chat import ChatDocument
from qiushuiai.core.db_filters import update_common_fields
from qiushuiai.modules.user.deps import CurrentUser

logger = logging.getLogger(__name__)


class DocumentStatusManager:
    """文档状态管理器"""
    
    # 文档状态定义
    STATUS_UPLOADED = "uploaded"      # 已上传
    STATUS_EXTRACTED = "extracted"    # 已提取内容
    STATUS_EMBEDDED = "embedded"      # 已向量化
    STATUS_FAILED = "failed"          # 处理失败
    
    # 状态流转规则
    STATUS_FLOW = {
        STATUS_UPLOADED: [STATUS_EXTRACTED, STATUS_FAILED],
        STATUS_EXTRACTED: [STATUS_EMBEDDED, STATUS_FAILED],
        STATUS_EMBEDDED: [],  # 最终状态
        STATUS_FAILED: []     # 最终状态
    }
    
    def __init__(self, session: Session, current_user: CurrentUser):
        self.session = session
        self.current_user = current_user
    
    def can_transition_to(self, current_status: str, target_status: str) -> bool:
        """
        检查是否可以从当前状态转换到目标状态
        
        Args:
            current_status: 当前状态
            target_status: 目标状态
            
        Returns:
            是否可以转换
        """
        allowed_transitions = self.STATUS_FLOW.get(current_status, [])
        return target_status in allowed_transitions
    
    def update_status(self, document: Union[KbDocument, ChatDocument], 
                     new_status: str, chunks_count: int = None) -> bool:
        """
        更新文档状态
        
        Args:
            document: 文档对象
            new_status: 新状态
            chunks_count: 分块数量（可选）
            
        Returns:
            是否更新成功
        """
        try:
            # 检查状态转换是否有效
            if not self.can_transition_to(document.status, new_status):
                logger.warning(f"无效的状态转换: {document.status} -> {new_status}")
                return False
            
            # 更新状态
            document.status = new_status
            
            # 更新分块数量（如果提供）
            if chunks_count is not None:
                document.chunk_count = chunks_count
            
            # 更新处理时间
            if new_status in [self.STATUS_EMBEDDED, self.STATUS_FAILED]:
                document.processed_at = datetime.now()
            
            # 更新公共字段
            update_data = update_common_fields(
                data={},
                current_user=self.current_user,
                is_create=False
            )
            document.sqlmodel_update(update_data)
            
            # 保存到数据库
            self.session.add(document)
            self.session.commit()
            self.session.refresh(document)
            
            logger.info(f"文档 {document.id} 状态已更新: {document.status} -> {new_status}")
            return True
            
        except Exception as e:
            logger.error(f"更新文档状态失败: {str(e)}")
            self.session.rollback()
            return False
    
    def mark_as_extracted(self, document: Union[KbDocument, ChatDocument]) -> bool:
        """标记文档为已提取内容"""
        return self.update_status(document, self.STATUS_EXTRACTED)
    
    def mark_as_embedded(self, document: Union[KbDocument, ChatDocument], 
                        chunks_count: int, embedding_model: str = None) -> bool:
        """
        标记文档为已向量化
        
        Args:
            document: 文档对象
            chunks_count: 分块数量
            embedding_model: 使用的向量模型名称
        """
        try:
            # 检查状态转换是否有效
            if not self.can_transition_to(document.status, self.STATUS_EMBEDDED):
                logger.warning(f"无效的状态转换: {document.status} -> {self.STATUS_EMBEDDED}")
                return False
            
            # 更新状态
            document.status = self.STATUS_EMBEDDED
            
            # 更新分块数量
            document.chunk_count = chunks_count
            
            # 更新向量模型（如果提供）
            if embedding_model:
                document.embedding_model = embedding_model
                logger.info(f"文档 {document.id} 使用向量模型: {embedding_model}")
            
            # 更新处理时间
            document.processed_at = datetime.now()
            
            # 更新公共字段
            update_data = update_common_fields(
                data={},
                current_user=self.current_user,
                is_create=False
            )
            document.sqlmodel_update(update_data)
            
            # 保存到数据库
            self.session.add(document)
            self.session.commit()
            self.session.refresh(document)
            
            logger.info(f"文档 {document.id} 状态已更新: {document.status} -> {self.STATUS_EMBEDDED}")
            return True
            
        except Exception as e:
            logger.error(f"更新文档状态失败: {str(e)}")
            self.session.rollback()
            return False
    
    def mark_as_failed(self, document: Union[KbDocument, ChatDocument]) -> bool:
        """标记文档为处理失败"""
        return self.update_status(document, self.STATUS_FAILED, 0)
    
    def get_status_description(self, status: str) -> str:
        """获取状态描述"""
        descriptions = {
            self.STATUS_UPLOADED: "已上传",
            self.STATUS_EXTRACTED: "已提取内容",
            self.STATUS_EMBEDDED: "已向量化",
            self.STATUS_FAILED: "处理失败"
        }
        return descriptions.get(status, "未知状态")
    
    def get_next_possible_statuses(self, current_status: str) -> list:
        """获取当前状态下可能的下一个状态"""
        return self.STATUS_FLOW.get(current_status, []) 