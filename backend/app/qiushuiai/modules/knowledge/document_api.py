from typing import Any, Annotated
from datetime import datetime
import uuid as uuid_module
import logging

from fastapi import APIRouter, Body
from sqlmodel import func, select

from qiushuiai.modules.user.deps import CurrentUser, SessionDep
from qiushuiai.core.db_filters import (
    apply_common_filters,
    apply_pagination,
    build_order_by,
    get_count_query,
    update_common_fields,
    apply_keyword_search
)
from qiushuiai.core.response import (
    BaseResponse,
    success_response,
    page_response,
    PageResponse,
    ResponseCode,
    ResponseMessage,
)
from qiushuiai.core.exceptions import ResourceNotFoundException
from qiushuiai.schemas.knowledge import (
    KbDocument,
    KbDocumentCreate,
    KbDocumentPublic,
    KbDocumentUpdate,
)
# 导入文档处理器
from qiushuiai.modules.knowledge.processors.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/document", tags=["document"])

 
@router.post("/page", response_model=BaseResponse[PageResponse[KbDocumentPublic]])
def page_documents(
    session: SessionDep, 
    current_user: CurrentUser, 
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取文档列表。"""
    # 提取参数，设置默认值
    page = request_data.get("page", 1)
    rows = request_data.get("rows", 20)
    keyword = request_data.get("keyword")
    knowledge_base_id = request_data.get("knowledge_base_id")
    
    # 构建基础查询
    statement = select(KbDocument)
    
    # 应用通用过滤条件
    statement = apply_common_filters(
        statement=statement,
        model=KbDocument,
        current_user=current_user
    )
    
    # 如果指定了知识库ID，添加过滤条件
    if knowledge_base_id:
        statement = statement.where(KbDocument.knowledge_base_id == knowledge_base_id)
    
    # 如果指定了对话ID，添加过滤条件
    chat_conversation_id = request_data.get("chat_conversation_id")
    if chat_conversation_id:
        statement = statement.where(KbDocument.chat_conversation_id == chat_conversation_id)
    
    # 应用关键词搜索
    statement = apply_keyword_search(
        statement=statement,
        model=KbDocument,
        keyword=keyword,
        search_fields=["title", "filename", "content"]
    )
    
    # 构建计数查询
    count_statement = get_count_query(statement, KbDocument)
    count = session.exec(count_statement).one()
    
    # 添加排序
    statement = build_order_by(
        statement=statement,
        model=KbDocument,
        order_by="id",
        order_direction="desc"
    ) 
    
    # 应用分页
    statement, _, _ = apply_pagination(
        statement=statement,
        page=page,
        page_size=rows
    )
    
    # 执行查询
    documents = session.exec(statement).all()
    
    # 使用标准分页响应格式
    return page_response(
        items=documents,
        page=page,
        rows=rows,
        total=count,
        message="获取文档列表成功"
    )


@router.post("/detail/{uuid}", response_model=BaseResponse[KbDocumentPublic])
def read_document(
    session: SessionDep, 
    current_user: CurrentUser, 
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单个文档。"""
    statement = select(KbDocument).where(KbDocument.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=KbDocument,
        current_user=current_user
    )
    document = session.exec(statement).first()
    
    if not document:
        raise ResourceNotFoundException(message="文档不存在")
    
    return success_response(data=document, message="获取文档详情成功")


@router.post("/create", response_model=BaseResponse[KbDocumentPublic])
def create_document(
    *, 
    session: SessionDep, 
    current_user: CurrentUser, 
    document_in: KbDocumentCreate
) -> Any:
    """创建新文档。"""
    logger.info(f"=== 开始创建文档 ===")
    logger.info(f"文档标题: {document_in.title}")
    logger.info(f"文件名: {document_in.filename}")
    logger.info(f"文件类型: {document_in.file_type}")
    logger.info(f"知识库ID: {document_in.knowledge_base_id}")
    logger.info(f"聊天会话ID: {document_in.chat_conversation_id}")
    logger.info(f"文档内容长度: {len(document_in.content) if document_in.content else 0}")
    if document_in.content:
        logger.info(f"文档内容前100字符: {document_in.content[:100]}...")
    
    document_data = document_in.model_dump()
    
    # 使用通用函数更新公共字段
    document_data = update_common_fields(
        data=document_data,
        current_user=current_user,
        is_create=True
    )
    
    # 添加tenant_id字段
    document_data["tenant_id"] = current_user.tenant_id
    
    document = KbDocument.model_validate(document_data)
    session.add(document)
    session.commit()
    session.refresh(document)
    
    logger.info(f"文档创建成功，ID: {document.id}, UUID: {document.uuid}")
    
    # 如果文档有内容，则进行分块和向量化处理
    if document.content:
        logger.info(f"文档有内容，开始进行分块和向量化处理...")
        try:
            # 创建文档处理器
            logger.info("创建文档处理器...")
            processor = DocumentProcessor(session, current_user)
            
            # 异步处理文档（在实际应用中应该使用后台任务）
            # 这里为了演示，同步处理
            logger.info("开始处理文档...")
            result = processor.process_document(document)
            
            logger.info(f"文档处理结果: {result}")
            
            if result["success"]:
                logger.info(f"文档处理成功，共处理 {result['chunks_count']} 个分块")
                return success_response(
                    data=document, 
                    message=f"文档创建成功，已处理 {result['chunks_count']} 个分块",
                    code=ResponseCode.CREATED
                )
            else:
                logger.error(f"文档处理失败: {result['message']}")
                return success_response(
                    data=document, 
                    message=f"文档创建成功，但处理失败: {result['message']}",
                    code=ResponseCode.CREATED
                )
        except Exception as e:
            logger.error(f"文档处理过程中发生异常: {str(e)}", exc_info=True)
            # 即使处理失败，文档仍然创建成功
            return success_response(
                data=document, 
                message=f"文档创建成功，但处理失败: {str(e)}",
                code=ResponseCode.CREATED
            )
    else:
        logger.info("文档内容为空，跳过分块和向量化处理")
    
    logger.info(f"=== 文档创建完成 ===")
    return success_response(
        data=document, 
        message=ResponseMessage.CREATED,
        code=ResponseCode.CREATED
    )


@router.post("/update/{uuid}", response_model=BaseResponse[KbDocumentPublic])
def update_document(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    document_in: KbDocumentUpdate,
) -> Any:
    """更新文档信息。"""
    statement = select(KbDocument).where(KbDocument.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=KbDocument,
        current_user=current_user
    )
    document = session.exec(statement).first()
    
    if not document:
        raise ResourceNotFoundException(message="文档不存在")
    
    update_dict = document_in.model_dump(exclude_unset=True)
    
    # 使用通用函数更新公共字段
    update_dict = update_common_fields(
        data=update_dict,
        current_user=current_user,
        is_create=False
    )
    
    document.sqlmodel_update(update_dict)
    session.add(document)
    session.commit()
    session.refresh(document)
    return success_response(data=document, message=ResponseMessage.UPDATED)


@router.post("/delete/{uuid}", response_model=BaseResponse[None])
def delete_document(
    session: SessionDep, 
    current_user: CurrentUser, 
    uuid: uuid_module.UUID
) -> Any:
    """删除文档（硬删除）。"""
    statement = select(KbDocument).where(KbDocument.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=KbDocument,
        current_user=current_user
    )
    document = session.exec(statement).first()
    
    if not document:
        raise ResourceNotFoundException(message="文档不存在")
    
    # 直接从数据库中删除
    session.delete(document)
    session.commit()
    return success_response(data=None, message=ResponseMessage.DELETED)


@router.post("/batch-delete", response_model=BaseResponse[None])
def batch_delete_documents(
    session: SessionDep, 
    current_user: CurrentUser, 
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """批量删除文档（硬删除）。"""
    uuids = request_data.get("uuids", [])
    
    if not uuids:
        return success_response(data=None, message="没有选择要删除的文档")
    
    # 查询要删除的文档
    statement = select(KbDocument).where(KbDocument.uuid.in_(uuids))
    statement = apply_common_filters(
        statement=statement,
        model=KbDocument,
        current_user=current_user
    )
    documents = session.exec(statement).all()
    
    if not documents:
        raise ResourceNotFoundException(message="未找到要删除的文档")
    
    # 批量硬删除
    for document in documents:
        session.delete(document)
    
    session.commit()
    return success_response(data=None, message=f"成功删除 {len(documents)} 个文档")


@router.post("/process/{uuid}", response_model=BaseResponse[dict])
def process_document(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """手动触发文档处理（分块和向量化）。"""
    logger.info(f"=== 手动触发文档处理 ===")
    logger.info(f"文档UUID: {uuid}")
    
    # 查找文档
    statement = select(KbDocument).where(KbDocument.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=KbDocument,
        current_user=current_user
    )
    document = session.exec(statement).first()
    
    if not document:
        logger.error(f"文档不存在: {uuid}")
        raise ResourceNotFoundException(message="文档不存在")
    
    logger.info(f"找到文档: ID={document.id}, 标题={document.title}")
    logger.info(f"文档内容长度: {len(document.content) if document.content else 0}")
    
    if not document.content:
        logger.warning("文档内容为空，无法处理")
        return success_response(
            data=None,
            message="文档内容为空，无法处理",
            code=ResponseCode.BAD_REQUEST
        )
    
    try:
        # 创建文档处理器
        logger.info("创建文档处理器...")
        processor = DocumentProcessor(session, current_user)
        
        # 处理文档
        logger.info("开始处理文档...")
        result = processor.process_document(document)
        
        logger.info(f"文档处理结果: {result}")
        
        if result["success"]:
            logger.info(f"文档处理成功，共处理 {result['chunks_count']} 个分块")
            return success_response(
                data=result,
                message=f"文档处理成功，共处理 {result['chunks_count']} 个分块"
            )
        else:
            logger.error(f"文档处理失败: {result['message']}")
            return success_response(
                data=result,
                message=f"文档处理失败: {result['message']}",
                code=ResponseCode.INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"文档处理过程中发生异常: {str(e)}", exc_info=True)
        return success_response(
            data={"error": str(e)},
            message=f"文档处理失败: {str(e)}",
            code=ResponseCode.INTERNAL_SERVER_ERROR
        )
