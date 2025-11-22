import os
import uuid
import logging
from typing import Any, List
from datetime import datetime
from pathlib import Path
from fastapi import Form
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Body
from fastapi.responses import FileResponse
from sqlmodel import select

from qiushuiai.modules.user.deps import CurrentUser, SessionDep
from qiushuiai.core.response import (
    BaseResponse,
    success_response,
    list_response,
    ResponseCode,
    ResponseMessage,
)
from qiushuiai.core.exceptions import ResourceNotFoundException
from qiushuiai.core.config import settings
from qiushuiai.core.db_filters import update_common_fields
from qiushuiai.schemas.knowledge import KbDocument, KbDocumentCreate, KbDocumentPublic
from qiushuiai.schemas.chat import ChatDocument, ChatDocumentCreate, ChatDocumentPublic
# 导入 OSS 服务
from qiushuiai.modules.utils.oss_service import oss_service
# 导入文档处理器
from qiushuiai.modules.knowledge.processors.document_processor import DocumentProcessor
from qiushuiai.modules.knowledge.processors.document_status_manager import DocumentStatusManager
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    CSVLoader,
    UnstructuredFileLoader
)
import subprocess
import tempfile
from langchain.text_splitter import MarkdownHeaderTextSplitter
import hashlib

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/utils/upload", tags=["upload"])

# 文件上传配置
UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {
    "image": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"},
    "document": {".pdf", ".doc", ".docx", ".txt", ".rtf",".md"},
    "spreadsheet": {".xls", ".xlsx", ".csv"},
    "presentation": {".ppt", ".pptx"},
    "archive": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "video": {".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm"},
    "audio": {".mp3", ".wav", ".flac", ".aac", ".ogg"}
}
# 文件大小限制从配置中获取


def get_file_type(filename: str) -> str:
    """根据文件扩展名判断文件类型"""
    ext = Path(filename).suffix.lower()
    for file_type, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return file_type
    return "other"


def is_allowed_file(filename: str) -> bool:
    """检查文件是否允许上传"""
    ext = Path(filename).suffix.lower()
    all_extensions = set()
    for extensions in ALLOWED_EXTENSIONS.values():
        all_extensions.update(extensions)
    return ext in all_extensions


def save_uploaded_file(file: UploadFile, user_id: int) -> dict:
    """
    保存上传的文件到阿里云 OSS

    Args:
        file: 上传的文件对象
        user_id: 用户ID (保留参数以兼容现有代码,实际未使用)

    Returns:
        文件信息字典

    Raises:
        HTTPException: OSS 上传失败
    """
    try:
        # 获取文件大小
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        # 上传到 OSS
        oss_url = oss_service.upload_file(
            file_obj=file.file,
            original_filename=file.filename,
            file_size=file_size
        )

        # 从 OSS URL 中提取路径 (用于后续可能需要的操作)
        # URL 格式: https://bucket.endpoint/path
        oss_path = oss_url.split('/', 3)[-1] if '/' in oss_url else ""

        # 生成文件 UUID (从 OSS 路径中提取)
        file_uuid = Path(oss_path).stem if oss_path else str(uuid.uuid4())

        # 返回文件信息
        return {
            "original_filename": file.filename,
            "filename": Path(oss_path).name if oss_path else file.filename,
            "file_path": oss_url,  # 返回 OSS URL 而不是本地路径
            "oss_url": oss_url,    # 明确标识为 OSS URL
            "oss_path": oss_path,  # OSS 对象路径
            "file_size": file_size,
            "file_type": get_file_type(file.filename),
            "content_type": file.content_type,
            "upload_time": datetime.now().isoformat(),
            "file_uuid": file_uuid,
            "storage_type": "oss"  # 标识存储类型
        }
    except Exception as e:
        logger.error(f"OSS 上传失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传到 OSS 失败: {str(e)}"
        )


@router.post("/files", response_model=BaseResponse[List[dict]])
def upload_files(
    session: SessionDep,
    current_user: CurrentUser,
    files: List[UploadFile] = File(..., description="要上传的文件列表")
) -> Any:
    """
    多文件上传接口
    
    Args:
        session: 数据库会话
        current_user: 当前用户
        files: 要上传的文件列表
        
    Returns:
        上传成功的文件信息列表
    """
    # 验证文件数量
    if len(files) > settings.MAX_FILES_COUNT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"一次最多只能上传 {settings.MAX_FILES_COUNT} 个文件"
        )
    
    uploaded_files = []
    user_id = current_user.id
    
    for file in files:
        # 验证文件
        if not file.filename:
            continue
            
        if not is_allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file.filename}"
            )
        
        # 检查文件大小
        file.file.seek(0, 2)  # 移动到文件末尾
        file_size = file.file.tell()
        file.file.seek(0)  # 重置到文件开头
        
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件 {file.filename} 超过最大大小限制 ({settings.MAX_FILE_SIZE // (1024*1024)}MB)"
            )
        
        try:
            # 保存文件
            file_info = save_uploaded_file(file, user_id)
            uploaded_files.append(file_info)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"保存文件 {file.filename} 时发生错误: {str(e)}"
            )
    
    return success_response(
        data=uploaded_files,
        message=f"成功上传 {len(uploaded_files)} 个文件",
        code=ResponseCode.CREATED
    )


@router.post("/knowledge", response_model=BaseResponse[List[dict]])
def upload_to_knowledge(
    session: SessionDep,
    current_user: CurrentUser,
    files: List[UploadFile] = File(..., description="要上传的文件列表"),
    knowledge_base_id: int | None = Form(default=None, description="知识库ID"),
    chat_conversation_id: str | None = Form(default=None, description="聊天会话ID"),
    chat_conversation_uuid: str | None =   Form(default=None, description="聊天会话UUID")
) -> Any:
    """
    将文件上传到知识库或聊天对话并创建文档记录，上传成功后自动进行文档分块和向量化处理
    
    Args:
        session: 数据库会话
        current_user: 当前用户
        files: 要上传的文件列表
        knowledge_base_id: 知识库ID（与chat_conversation_id二选一）
        chat_conversation_id: 聊天会话ID（与knowledge_base_id二选一）
        
    Returns:
        上传成功的文档信息列表
    """
    print("------------------")
    logger.info(f"=== 开始上传文件到知识库或聊天对话 ===")
    logger.info(f"知识库ID: {knowledge_base_id}")
    logger.info(f"聊天会话ID: {chat_conversation_id}")
    logger.info(f"文件数量: {len(files)}")
    
    # 验证参数：必须提供其中一个ID
    if not knowledge_base_id and not chat_conversation_id and not chat_conversation_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供知识库ID或聊天会话ID"
        )
    
    if knowledge_base_id and (chat_conversation_id or chat_conversation_uuid):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能同时提供知识库ID和聊天会话ID"
        )
    
    # 验证文件数量
    if len(files) > settings.MAX_FILES_COUNT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"一次最多只能上传 {settings.MAX_FILES_COUNT} 个文件"
        )
    
    uploaded_documents = []
    processed_documents = []
    user_id = current_user.id
    
    for file in files:
        # 验证文件
        if not file.filename:
            continue
            
        if not is_allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file.filename}"
            )
        
        # 检查文件大小
        file.file.seek(0, 2)  # 移动到文件末尾
        file_size = file.file.tell()
        file.file.seek(0)  # 重置到文件开头
        
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件 {file.filename} 超过最大大小限制 ({settings.MAX_FILE_SIZE // (1024*1024)}MB)"
            )

        try:
            # 保存文件到 OSS
            file_info = save_uploaded_file(file, user_id)

            # 对于知识库文档,需要下载 OSS 文件到临时位置进行内容提取
            # 因为文档处理器需要访问本地文件
            temp_file_path = None
            if knowledge_base_id:
                # 创建临时文件
                temp_dir = Path(tempfile.gettempdir()) / "qiushui_oss_downloads"
                temp_dir.mkdir(parents=True, exist_ok=True)

                temp_file_path = temp_dir / file_info["filename"]

                # 从 OSS 下载文件到临时位置
                try:
                    oss_service.bucket.get_object_to_file(
                        file_info["oss_path"],
                        str(temp_file_path)
                    )
                    # 更新 file_info 中的 file_path 为临时文件路径 (用于内容提取)
                    file_info["temp_file_path"] = str(temp_file_path)
                    logger.info(f"从 OSS 下载文件到临时位置: {temp_file_path}")
                except Exception as download_error:
                    logger.error(f"从 OSS 下载文件失败: {str(download_error)}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"从 OSS 下载文件失败: {str(download_error)}"
                    )

            # 添加文件内容提取函数
            def extract_file_content(file_path: str, file_type: str, original_filename: str) -> tuple[str, str]:
                """从文件中提取文本内容，使用Docling CLI进行统一文档处理
                
                Returns:
                    tuple: (content, extraction_tool) - 提取的内容和使用的工具名称
                """
                try:
                    file_extension = Path(original_filename).suffix.lower()
                    logger.info(f"开始提取文件内容: {original_filename}, 扩展名: {file_extension}, 文件路径: {file_path}")
                    
                    # 检查文件是否存在
                    if not Path(file_path).exists():
                        logger.error(f"文件不存在: {file_path}")
                        return "", "none"
                    
                    # Docling支持的文件格式映射
                    docling_format_map = {
                        '.pdf': 'pdf',
                        '.docx': 'docx', 
                        '.xlsx': 'xlsx',
                        '.pptx': 'pptx',
                        '.md': 'md',
                        '.html': 'html',
                        '.csv': 'csv',
                        '.png': 'image',
                        '.jpg': 'image',
                        '.jpeg': 'image',
                        '.tiff': 'image',
                        '.bmp': 'image',
                        '.webp': 'image'
                    }
                    
                    # 检查是否支持Docling处理
                    if file_extension in docling_format_map:
                        logger.info(f"使用Docling CLI处理文件: {file_extension} -> {docling_format_map[file_extension]}")
                        try:
                            # 创建临时输出目录
                            with tempfile.TemporaryDirectory() as output_dir:
                                # 构建Docling命令
                                cmd = [
                                    "docling",
                                    "--from", docling_format_map[file_extension],
                                    "--to", "md",  # 输出Markdown格式
                                    "--output", output_dir,
                                    file_path
                                ]
                                
                                logger.info(f"执行Docling命令: {' '.join(cmd)}")
                                
                                # 执行Docling转换
                                result = subprocess.run(
                                    cmd,
                                    capture_output=True,
                                    text=True,
                                    timeout=300  # 5分钟超时
                                )
                                
                                if result.returncode == 0:
                                    logger.info("Docling转换成功")
                                    
                                    # 查找输出文件
                                    output_files = list(Path(output_dir).glob("*.md"))
                                    if output_files:
                                        output_file = output_files[0]
                                        logger.info(f"找到输出文件: {output_file}")
                                        
                                        # 读取Markdown内容
                                        with open(output_file, 'r', encoding='utf-8') as f:
                                            content = f.read()
                                        
                                        if content.strip():
                                            logger.info(f"Docling文本提取成功，内容长度: {len(content)} 字符")
                                            return content, f"docling_{docling_format_map[file_extension]}"
                                        else:
                                            logger.warning("Docling提取的内容为空")
                                            return _fallback_extract_content(file_path, file_extension, original_filename)
                                    else:
                                        logger.warning("Docling未生成输出文件")
                                        return _fallback_extract_content(file_path, file_extension, original_filename)
                                else:
                                    logger.error(f"Docling转换失败: {result.stderr}")
                                    return _fallback_extract_content(file_path, file_extension, original_filename)
                                    
                        except subprocess.TimeoutExpired:
                            logger.error("Docling转换超时")
                            return _fallback_extract_content(file_path, file_extension, original_filename)
                        except Exception as docling_error:
                            logger.error(f"Docling处理失败: {str(docling_error)}")
                            logger.info("回退到传统文档处理方法")
                            return _fallback_extract_content(file_path, file_extension, original_filename)
                    else:
                        # 对于不支持的文件类型，使用传统方法
                        logger.info(f"文件类型 {file_extension} 不在Docling支持范围内，使用传统方法")
                        return _fallback_extract_content(file_path, file_extension, original_filename)
                    
                except Exception as e:
                    logger.error(f"提取文件内容失败: {str(e)}", exc_info=True)
                    return f"文件内容提取失败: {str(e)}", "error"
            
            def _fallback_extract_content(file_path: str, file_extension: str, original_filename: str) -> tuple[str, str]:
                """传统文档提取方法作为回退方案
                
                Returns:
                    tuple: (content, extraction_tool) - 提取的内容和使用的工具名称
                """
                try:
                    logger.info(f"使用传统方法提取文件内容: {original_filename}")
                    
                    # 根据文件类型选择相应的加载器
                    if file_extension == '.txt':
                        logger.info("使用TextLoader处理TXT文件")
                        loader = TextLoader(file_path, encoding='utf-8')
                        tool_name = "text_loader"
                    elif file_extension == '.pdf':
                        logger.info("使用PyPDFLoader处理PDF文件")
                        try:
                            loader = PyPDFLoader(file_path)
                            documents = loader.load()
                            logger.info(f"PyPDFLoader成功，共 {len(documents)} 页")
                            
                            # 检查是否成功提取到内容
                            content_parts = []
                            for i, doc in enumerate(documents):
                                if doc.page_content:
                                    content_parts.append(doc.page_content)
                                    logger.info(f"页面 {i+1} 内容长度: {len(doc.page_content)} 字符")
                                else:
                                    logger.warning(f"页面 {i+1} 内容为空")
                            
                            content = "\n\n".join(content_parts)
                            
                            # 如果PyPDFLoader没有提取到内容，可能是扫描版PDF
                            if not content.strip():
                                logger.warning("PyPDFLoader未提取到内容，可能是扫描版PDF")
                                logger.info("建议使用OCR工具处理扫描版PDF文件")
                                return "扫描版PDF文件，需要OCR处理才能提取文本内容。", "pypdf_loader_failed"
                            
                            logger.info(f"PDF内容提取完成，总长度: {len(content)} 字符")
                            return content, "pypdf_loader"
                            
                        except Exception as pdf_error:
                            logger.error(f"PyPDFLoader初始化失败: {str(pdf_error)}")
                            logger.warning("PDF处理失败，可能是扫描版或损坏的PDF文件")
                            return "PDF文件处理失败，可能是扫描版或损坏的PDF文件。", "pypdf_loader_error"
                            
                    elif file_extension in ['.docx', '.doc']:
                        logger.info("使用Docx2txtLoader处理Word文件")
                        loader = Docx2txtLoader(file_path)
                        tool_name = "docx2txt_loader"
                    elif file_extension == '.csv':
                        logger.info("使用CSVLoader处理CSV文件")
                        loader = CSVLoader(file_path)
                        tool_name = "csv_loader"
                    else:
                        logger.info(f"使用UnstructuredFileLoader处理文件: {file_extension}")
                        # 对于其他文件类型，使用通用加载器
                        loader = UnstructuredFileLoader(file_path)
                        tool_name = "unstructured_loader"
                    
                    # 加载文档（非PDF文件）
                    logger.info("开始加载文档...")
                    documents = loader.load()
                    logger.info(f"文档加载完成，共 {len(documents)} 个页面/部分")
                    
                    # 合并所有页面的内容
                    content_parts = []
                    for i, doc in enumerate(documents):
                        if doc.page_content:
                            content_parts.append(doc.page_content)
                            logger.info(f"页面 {i+1} 内容长度: {len(doc.page_content)} 字符")
                        else:
                            logger.warning(f"页面 {i+1} 内容为空")
                    
                    content = "\n\n".join(content_parts)
                    logger.info(f"文件内容提取完成，总长度: {len(content)} 字符")
                    
                    if not content.strip():
                        logger.warning("提取的内容为空或只包含空白字符")
                    
                    return content, tool_name
                    
                except Exception as e:
                    logger.error(f"传统方法提取文件内容失败: {str(e)}", exc_info=True)
                    return f"文件内容提取失败: {str(e)}", "fallback_error"

            # 在创建 document_data 之前添加内容提取
            logger.info(f"开始提取文件内容: {file_info['original_filename']}")

            # 对于知识库文档,使用临时文件路径进行内容提取
            # 对于聊天文档,暂不提取内容
            extraction_file_path = file_info.get("temp_file_path", file_info["file_path"])

            file_content, extraction_tool = extract_file_content(
                extraction_file_path,
                file_info["file_type"],
                file_info["original_filename"]
            )
            
            logger.info(f"文件内容提取结果: 长度={len(file_content)}, 是否为空={not file_content.strip()}, 工具={extraction_tool}")
            
            # 检查内容提取是否成功
            # 排除扫描版PDF和其他提取失败的情况
            failed_extraction_indicators = [
                "文件内容提取失败",
                "扫描版PDF文件，需要OCR处理才能提取文本内容",
                "PDF文件处理失败，可能是扫描版或损坏的PDF文件"
            ]
            
            content_extraction_success = bool(
                file_content and 
                file_content.strip() and 
                not any(indicator in file_content for indicator in failed_extraction_indicators)
            )

            # 计算文件哈希
            file_hash = hashlib.sha256(file_content.encode()).hexdigest() if file_content else None

            # 根据ID类型选择对应的文档表
            if knowledge_base_id:
                # 使用知识库文档表
                document_data = {
                    "knowledge_base_id": knowledge_base_id,
                    "title": file_info["original_filename"],
                    "filename": file_info["filename"],
                    "file_type": file_info["file_type"],
                    "file_size": file_info["file_size"],
                    "content": file_content,  # 使用提取的内容
                    "extra_data": {
                        "original_filename": file_info["original_filename"],
                        "file_path": file_info["file_path"],  # OSS URL
                        "oss_url": file_info.get("oss_url"),
                        "oss_path": file_info.get("oss_path"),
                        "storage_type": file_info.get("storage_type", "oss"),
                        "content_type": file_info["content_type"],
                        "upload_time": file_info["upload_time"],
                        "file_uuid": file_info["file_uuid"],
                        "file_extension": Path(file_info["original_filename"]).suffix.lower().lstrip(".")
                    },
                    "source_url": file_info.get("oss_url"),  # 设置 source_url 为 OSS URL
                    "hash": file_hash,  # 设置文件哈希
                    "chunk_count": 0,
                    "token_count": 0,
                    "status": "uploaded",  # 初始状态：已上传
                    "extraction_tool": extraction_tool,  # 设置提取工具
                    "processed_at": None
                }
                
                # 使用通用函数更新公共字段
                document_data = update_common_fields(
                    data=document_data,
                    current_user=current_user,
                    is_create=True
                )
                
                # 创建知识库文档对象并保存到数据库
                document = KbDocument.model_validate(document_data)
                
            else:
                # 使用聊天对话文档表
                document_data = {
                    "chat_conversation_id": int(chat_conversation_id) if chat_conversation_id else None,
                    "chat_conversation_uuid": chat_conversation_uuid,
                    "title": file_info["original_filename"],
                    "filename": file_info["filename"],
                    "file_type": file_info["file_type"],
                    "file_size": file_info["file_size"],
                    "content": file_content,  # 使用提取的内容
                    "extra_data": {
                        "original_filename": file_info["original_filename"],
                        "file_path": file_info["file_path"],  # OSS URL
                        "oss_url": file_info.get("oss_url"),
                        "oss_path": file_info.get("oss_path"),
                        "storage_type": file_info.get("storage_type", "oss"),
                        "content_type": file_info["content_type"],
                        "upload_time": file_info["upload_time"],
                        "file_uuid": file_info["file_uuid"],
                        "file_extension": Path(file_info["original_filename"]).suffix.lower().lstrip(".")
                    },
                    "source_url": file_info.get("oss_url"),  # 设置 source_url 为 OSS URL
                    "hash": file_hash,  # 设置文件哈希
                    "chunk_count": 0,
                    "token_count": 0,
                    "status": "uploaded",  # 初始状态：已上传
                    "extraction_tool": extraction_tool,  # 设置提取工具
                    "processed_at": None
                }
                
                # 使用通用函数更新公共字段
                document_data = update_common_fields(
                    data=document_data,
                    current_user=current_user,
                    is_create=True
                )
                
                # 创建聊天对话文档对象并保存到数据库
                document = ChatDocument.model_validate(document_data)
            
            session.add(document)
            session.commit()
            session.refresh(document)

            print(f"文档创建成功，ID: {document.id}, UUID: {document.uuid}")
            if hasattr(document, 'knowledge_base_id'):
                print(f"knowledge_base_id: {document.knowledge_base_id}")
            if hasattr(document, 'chat_conversation_id'):
                print(f"chat_conversation_id: {document.chat_conversation_id}")
            if hasattr(document, 'chat_conversation_uuid'):
                print(f"chat_conversation_uuid: {document.chat_conversation_uuid}")
            print(f"tenant_id: {document.tenant_id}")
            
            logger.info(f"文档标题: {document.title}")
            logger.info(f"文件名: {document.filename}")
            logger.info(f"文件类型: {document.file_type}")
            
            uploaded_documents.append(document)
            
            # 如果文档有内容，则进行分块和向量化处理
            print("------------------1", document.content)

            if document.content and content_extraction_success:
                # 创建状态管理器
                status_manager = DocumentStatusManager(session, current_user)
                
                # 如果是聊天对话文档，跳过向量化处理
                if chat_conversation_id or chat_conversation_uuid:
                    logger.info("聊天对话文档，跳过分块和向量化处理")
                    # 更新状态为已提取内容
                    success = status_manager.mark_as_extracted(document)
                    if not success:
                        logger.error("更新聊天文档状态失败")
                    
                    processed_documents.append({
                        "document": document,
                        "chunks_count": 0,
                        "status": "skipped",
                        "reason": "聊天对话文档无需向量化"
                    })
                else:
                    print("------------------2")
                    logger.info(f"知识库文档有内容，开始进行分块和向量化处理...")
                    
                    # 更新状态为已提取内容
                    success = status_manager.mark_as_extracted(document)
                    if not success:
                        logger.error("更新文档状态为extracted失败")
                    
                    try:
                        # 创建文档处理器
                        logger.info("创建文档处理器...")
                        print("------------------3")
                        processor = DocumentProcessor(session, current_user)
                        print("------------------4")
                        
                        # 异步处理文档（在实际应用中应该使用后台任务）
                        # 这里为了演示，同步处理
                        logger.info("开始处理文档...")
                        result = processor.process_document(document)
                        
                        logger.info(f"文档处理结果: {result}")
                        
                        if result["success"]:
                            logger.info(f"文档处理成功，共处理 {result['chunks_count']} 个分块")
                            processed_documents.append({
                                "document": document,
                                "chunks_count": result['chunks_count'],
                                "status": "success"
                            })
                        else:
                            logger.error(f"文档处理失败: {result['message']}")
                            processed_documents.append({
                                "document": document,
                                "chunks_count": 0,
                                "status": "failed",
                                "error": result['message']
                            })
                    except Exception as e:
                        logger.error(f"文档处理过程中发生异常: {str(e)}", exc_info=True)
                        processed_documents.append({
                            "document": document,
                            "chunks_count": 0,
                            "status": "failed",
                            "error": str(e)
                        })
            else:
                logger.info("文档内容为空或提取失败，跳过分块和向量化处理")
                processed_documents.append({
                    "document": document,
                    "chunks_count": 0,
                    "status": "skipped",
                    "reason": "文档内容为空或提取失败"
                })

            # 清理临时文件
            if temp_file_path and Path(temp_file_path).exists():
                try:
                    Path(temp_file_path).unlink()
                    logger.info(f"已清理临时文件: {temp_file_path}")
                except Exception as cleanup_error:
                    logger.warning(f"清理临时文件失败: {str(cleanup_error)}")

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"保存文件 {file.filename} 时发生错误: {str(e)}"
            )
    
    # 统计处理结果
    success_count = len([d for d in processed_documents if d["status"] == "success"])
    failed_count = len([d for d in processed_documents if d["status"] == "failed"])
    skipped_count = len([d for d in processed_documents if d["status"] == "skipped"])
    total_chunks = sum([d["chunks_count"] for d in processed_documents])
    
    logger.info(f"=== 文件上传完成 ===")
    logger.info(f"成功上传: {len(uploaded_documents)} 个文件")
    logger.info(f"成功处理: {success_count} 个文档")
    logger.info(f"处理失败: {failed_count} 个文档")
    logger.info(f"跳过处理: {skipped_count} 个文档")
    logger.info(f"总分块数: {total_chunks}")
    
    # 将文档对象转换为字典格式
    document_dicts = []
    for document in uploaded_documents:
        # 根据文档类型转换为字典
        if hasattr(document, 'knowledge_base_id'):
            # KbDocument
            doc_dict = {
                "id": document.id,
                "uuid": str(document.uuid),
                "tenant_id": document.tenant_id,
                "knowledge_base_id": document.knowledge_base_id,
                "title": document.title,
                "filename": document.filename,
                "file_type": document.file_type,
                "file_size": document.file_size,
                "content": document.content,
                "extra_data": document.extra_data,
                "source_url": document.source_url,
                "hash": document.hash,
                "chunk_count": document.chunk_count,
                "token_count": document.token_count,
                "status": document.status,
                "extraction_tool": document.extraction_tool,
                "processed_at": document.processed_at.isoformat() if document.processed_at else None,
                "created_at": document.created_at.isoformat(),
                "created_by": document.created_by,
                "updated_at": document.updated_at.isoformat(),
                "updated_by": document.updated_by,
                "document_type": "kb_document"
            }
        else:
            # ChatDocument
            doc_dict = {
                "id": document.id,
                "uuid": str(document.uuid),
                "tenant_id": document.tenant_id,
                "chat_conversation_id": document.chat_conversation_id,
                "chat_conversation_uuid": document.chat_conversation_uuid,
                "title": document.title,
                "filename": document.filename,
                "file_type": document.file_type,
                "file_size": document.file_size,
                "content": document.content,
                "extra_data": document.extra_data,
                "source_url": document.source_url,
                "hash": document.hash,
                "chunk_count": document.chunk_count,
                "token_count": document.token_count,
                "status": document.status,
                "extraction_tool": document.extraction_tool,
                "processed_at": document.processed_at.isoformat() if document.processed_at else None,
                "created_at": document.created_at.isoformat(),
                "created_by": document.created_by,
                "updated_at": document.updated_at.isoformat(),
                "updated_by": document.updated_by,
                "document_type": "chat_document"
            }
        document_dicts.append(doc_dict)
    
    # 构建响应消息
    if chat_conversation_id or chat_conversation_uuid:
        # 聊天对话文档上传
        message = f"成功上传 {len(uploaded_documents)} 个文件到聊天对话并创建文档记录"
        if skipped_count > 0:
            message += f"（聊天对话文档无需向量化处理）"
    else:
        # 知识库文档上传
        if success_count > 0:
            message = f"成功上传 {len(uploaded_documents)} 个文件到知识库并创建文档记录，其中 {success_count} 个文档已成功处理（共 {total_chunks} 个分块）"
            if failed_count > 0:
                message += f"，{failed_count} 个文档处理失败"
            if skipped_count > 0:
                message += f"，{skipped_count} 个文档跳过处理"
        else:
            message = f"成功上传 {len(uploaded_documents)} 个文件到知识库并创建文档记录"
            if failed_count > 0:
                message += f"，{failed_count} 个文档处理失败"
            if skipped_count > 0:
                message += f"，{skipped_count} 个文档跳过处理"
    
    return success_response(
        data=document_dicts,
        message=message,
        code=ResponseCode.CREATED
    )


@router.get("/file/{file_uuid}")
def download_file(
    session: SessionDep,
    current_user: CurrentUser,
    file_uuid: str
) -> Any:
    """
    下载指定文件
    
    Args:
        session: 数据库会话
        current_user: 当前用户
        file_uuid: 文件UUID
        
    Returns:
        文件响应
    """
    user_id = current_user.id
    user_upload_dir = UPLOAD_DIR / str(user_id)
    
    # 查找文件
    for file_path in user_upload_dir.iterdir():
        if file_path.is_file() and file_uuid in file_path.name:
            if file_path.exists():
                return FileResponse(
                    path=str(file_path),
                    filename=file_path.name,
                    media_type="application/octet-stream"
                )
    
    raise ResourceNotFoundException(message="文件不存在")
