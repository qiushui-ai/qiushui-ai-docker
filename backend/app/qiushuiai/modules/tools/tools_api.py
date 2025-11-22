from typing import Any, Annotated
from datetime import datetime
import uuid as uuid_module
import asyncio
import logging

from fastapi import APIRouter, Body
from sqlmodel import select
from fastmcp import Client

# 配置日志记录器
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

from qiushuiai.core.config import settings
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
from qiushuiai.schemas.tools import (
    Tools,
    ToolsCreate,
    ToolsPublic,
    ToolsUpdate,
    ToolsMCPResponse,
)
from qiushuiai.modules.tools.mcp_service import MCPToolDiscoveryService

router = APIRouter(prefix="/tools", tags=["tools"])

@router.post("/page", response_model=BaseResponse[PageResponse[ToolsPublic]])
def page_tools(
    session: SessionDep,
    current_user: CurrentUser,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取工具列表。"""
    page = request_data.get("page", 1)
    rows = request_data.get("rows", 20)
    keyword = request_data.get("keyword")
    category = request_data.get("category")
    tool_type = request_data.get("tool_type")
    
    statement = select(Tools)

    statement = apply_common_filters(
        statement=statement,
        model=Tools,
        current_user=current_user
    )
    
    # 应用关键词搜索
    statement = apply_keyword_search(
        statement=statement,
        model=Tools,
        keyword=keyword,
        search_fields=["name", "description", "tags"]
    )
  
    # 应用分类过滤
    if category:
        statement = statement.where(Tools.category == category)
    
    # 应用工具类型过滤
    if tool_type:
        statement = statement.where(Tools.tool_type == tool_type)
    
  
    count_statement = get_count_query(statement, Tools)
 
    count = session.exec(count_statement).one()

    statement = build_order_by(
        statement=statement,
        model=Tools,
        order_by="id",
        order_direction="desc"
    )

    statement, _, _ = apply_pagination(
        statement=statement,
        page=page,
        page_size=rows
    )

    tools = session.exec(statement).all()
    return page_response(
        items=tools,
        page=page,
        rows=rows,
        total=count,
        message="获取工具列表成功"
    )



@router.post("/mytools", response_model=BaseResponse[PageResponse[ToolsPublic]])
def mytools(
    session: SessionDep,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取工具列表。"""
    page = request_data.get("page", 1)
    rows = request_data.get("rows", settings.DEFAULT_PAGE_SIZE)
    keyword = request_data.get("keyword")
    category = request_data.get("category")
    tool_type = request_data.get("tool_type")
    
    statement = select(Tools)

    
    # 应用关键词搜索
    statement = apply_keyword_search(
        statement=statement,
        model=Tools,
        keyword=keyword,
        search_fields=["name", "description", "tags"]
    )
  
    # 应用分类过滤
    if category:
        statement = statement.where(Tools.category == category)
    
    # 应用工具类型过滤
    if tool_type:
        statement = statement.where(Tools.tool_type == tool_type)
    
  
    count_statement = get_count_query(statement, Tools)
 
    count = session.exec(count_statement).one()

    statement = build_order_by(
        statement=statement,
        model=Tools,
        order_by="id",
        order_direction="desc"
    )

    statement, _, _ = apply_pagination(
        statement=statement,
        page=page,
        page_size=rows
    )

    tools = session.exec(statement).all()
    return page_response(
        items=tools,
        page=page,
        rows=rows,
        total=count,
        message="获取工具列表成功"
    )    

@router.post("/detail/{uuid}", response_model=BaseResponse[ToolsPublic])
def read_tool(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单个工具。"""
    statement = select(Tools).where(Tools.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=Tools,
        current_user=current_user
    )
    tool = session.exec(statement).first()
    if not tool:
        raise ResourceNotFoundException(message="工具不存在")
    return success_response(data=tool, message="获取工具详情成功")

@router.post("/create", response_model=BaseResponse[ToolsPublic])
async def create_tool(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    tool_in: ToolsCreate
) -> Any:
    """创建新工具。"""
    tool_data = tool_in.model_dump()
    tool_data = update_common_fields(
        data=tool_data,
        current_user=current_user,
        is_create=True
    )
    tool = Tools.model_validate(tool_data)
    session.add(tool)
    session.commit()
    session.refresh(tool)

    # 如果是MCP类型工具，触发工具发现
    if tool.tool_type == "mcp":
        logger.info(f"检测到MCP类型工具创建，开始工具发现: {tool.name}")
        try:
            tool = await MCPToolDiscoveryService.update_tool_info(session, tool)
            logger.info(f"MCP工具创建并发现完成: {tool.name}, 状态: {tool.is_active}")
        except Exception as e:
            # 发现失败时记录错误，但不中断创建流程
            logger.error(f"MCP工具发现失败: {str(e)}")
            logger.exception("详细错误信息:")
    else:
        logger.info(f"创建非MCP类型工具: {tool.name}, 类型: {tool.tool_type}")

    return success_response(
        data=tool,
        message=ResponseMessage.CREATED,
        code=ResponseCode.CREATED
    )

@router.post("/update/{uuid}", response_model=BaseResponse[ToolsPublic])
async def update_tool(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    tool_in: ToolsUpdate,
) -> Any:
    """更新工具信息。"""
    statement = select(Tools).where(Tools.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=Tools,
        current_user=current_user
    )
    tool = session.exec(statement).first()
    if not tool:
        raise ResourceNotFoundException(message="工具不存在")

    update_dict = tool_in.model_dump(exclude_unset=True)
    update_dict = update_common_fields(
        data=update_dict,
        current_user=current_user,
        is_create=False
    )
    tool.sqlmodel_update(update_dict)
    session.add(tool)
    session.commit()
    session.refresh(tool)

    # 如果是MCP类型工具或更新了MCP相关配置，触发工具发现
    mcp_related_fields = ['tool_type', 'tool_conf', 'sub_type']
    if (tool.tool_type == "mcp" or
        any(field in update_dict for field in mcp_related_fields)):
        logger.info(f"检测到MCP工具更新，开始重新发现: {tool.name}")
        logger.info(f"更新的字段: {list(update_dict.keys())}")
        try:
            tool = await MCPToolDiscoveryService.update_tool_info(session, tool)
            logger.info(f"MCP工具更新并重新发现完成: {tool.name}, 状态: {tool.is_active}")
        except Exception as e:
            # 发现失败时记录错误，但不中断更新流程
            logger.error(f"MCP工具发现失败: {str(e)}")
            logger.exception("详细错误信息:")
    else:
        logger.info(f"更新工具完成: {tool.name}, 未触发MCP发现")

    return success_response(data=tool, message=ResponseMessage.UPDATED)

@router.post("/delete/{uuid}", response_model=BaseResponse[None])
def delete_tool(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """删除工具（直接删除）。"""
    statement = select(Tools).where(Tools.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=Tools,
        current_user=current_user
    )
    tool = session.exec(statement).first()
    if not tool:
        raise ResourceNotFoundException(message="工具不存在")
    
    session.delete(tool)
    session.commit()
    return success_response(data=None, message=ResponseMessage.DELETED)

@router.post("/mcpinfo/{uuid}", response_model=BaseResponse[ToolsMCPResponse])
async def read_mcpinfo(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单个工具信息，如果是streamableHttp类型则获取MCP服务器信息。"""
    statement = select(Tools).where(Tools.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=Tools,
        current_user=current_user
    )
    tool = session.exec(statement).first()
    if not tool:
        raise ResourceNotFoundException(message="工具不存在")
    
    # 初始化默认值
    tools_dict_list = []
    resources_dict_list = []
    prompts_dict_list = []
    
    # 如果是 streamableHttp 类型，获取 MCP 服务器信息
    if tool.sub_type == "streamableHttp" or tool.sub_type == "sse":
        print(f"tool.sub_type: {tool.sub_type} - url:{tool.tool_conf.get('url')} - headers:{tool.tool_conf.get('headers')}")
        try:
            # 从 tool_conf 中获取 URL
            url = tool.tool_conf.get("url")
            if not url:
                raise ValueError("工具配置中缺少 URL 信息")
            
            # 创建 FastMCP 客户端
            import json
            from fastmcp.client.transports import StreamableHttpTransport

            try:
                headers_raw = tool.tool_conf.get('headers')
                if not headers_raw:
                    headers = {}
                elif isinstance(headers_raw, dict):
                    headers = headers_raw
                else:
                    headers = json.loads(headers_raw)
                authorization = headers.get("Authorization", "")
                print(f"------Authorization (no Bearer): {authorization.replace('Bearer ', '')}")
                print(f"------headers: {headers}")
            except Exception as e:
                headers = {}
                authorization = ""
                print(f"解析 headers 失败: {str(e)}")
           
            timeout = tool.tool_conf.get('timeout') or 60
            api_key = tool.tool_conf.get('api_key') or ""
            
            from fastmcp.client.auth import BearerAuth
            async with Client(
                url, 
                auth=BearerAuth(token=api_key.replace('Bearer ', '')),
                timeout=timeout
            ) as client:

                # 获取服务器信息
                await client.ping()
                
                # 获取可用操作
                tools_list = await client.list_tools()
                resources_list = await client.list_resources()
                prompts_list = await client.list_prompts()
                
                # 将 Tool 对象转换为字典格式
                for mcp_tool in tools_list:
                    tool_dict = {
                        "name": mcp_tool.name,
                        "description": mcp_tool.description,
                        "inputSchema": mcp_tool.inputSchema.model_dump() if hasattr(mcp_tool.inputSchema, 'model_dump') else mcp_tool.inputSchema
                    }
                    tools_dict_list.append(tool_dict)
                
                # 将 Resource 对象转换为字典格式
                for resource in resources_list:
                    resource_dict = {
                        "uri": resource.uri,
                        "name": resource.name,
                        "description": resource.description,
                        "mimeType": resource.mimeType
                    }
                    resources_dict_list.append(resource_dict)
                
                # 将 Prompt 对象转换为字典格式
                for prompt in prompts_list:
                    prompt_dict = {
                        "name": prompt.name,
                        "description": prompt.description,
                        "arguments": prompt.arguments.model_dump() if hasattr(prompt.arguments, 'model_dump') else prompt.arguments
                    }
                    prompts_dict_list.append(prompt_dict)
                
        except Exception as e:
            # 记录错误但不中断请求，返回工具信息但不包含 MCP 信息
            print(f"获取 MCP 服务器信息失败: {str(e)}")
    
    # 将数据库工具对象转换为 ToolsPublic 对象
    tool_public = ToolsPublic.model_validate(tool.model_dump())
    
    response_data = ToolsMCPResponse(
        tool_info=tool_public,
        tools=tools_dict_list,
        resources=resources_dict_list,
        prompts=prompts_dict_list
    )
    
    return success_response(data=response_data, message="获取工具详情成功")

@router.post("/discover/{uuid}", response_model=BaseResponse[ToolsPublic])
async def discover_tool_info(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """手动触发MCP工具发现。"""
    statement = select(Tools).where(Tools.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=Tools,
        current_user=current_user
    )
    tool = session.exec(statement).first()
    if not tool:
        raise ResourceNotFoundException(message="工具不存在")

    # 执行工具发现
    logger.info(f"手动触发MCP工具发现: {tool.name} (UUID: {uuid})")
    try:
        tool = await MCPToolDiscoveryService.update_tool_info(session, tool)
        message = "工具发现完成"
        logger.info(f"手动工具发现成功: {tool.name}, 状态: {tool.is_active}")
    except Exception as e:
        # 发现失败，返回错误信息但不抛出异常
        message = f"工具发现失败: {str(e)}"
        logger.error(f"手动工具发现失败: {tool.name}, 错误: {str(e)}")
        logger.exception("详细错误信息:")

    return success_response(data=tool, message=message)

@router.post("/toggle-status/{uuid}", response_model=BaseResponse[ToolsPublic])
async def toggle_tool_status(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """切换工具的启用/禁用状态。"""
    enable = request_data.get("enable", True)
    logger.info(f"切换工具状态: UUID={uuid}, enable={enable}")

    statement = select(Tools).where(Tools.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=Tools,
        current_user=current_user
    )
    tool = session.exec(statement).first()
    if not tool:
        raise ResourceNotFoundException(message="工具不存在")

    old_status = tool.is_active
    logger.info(f"工具 {tool.name} 当前状态: {old_status} -> 目标状态: {enable}")

    if enable:
        # 启用工具：需要连接MCP服务器获取工具信息
        logger.info(f"启用工具: {tool.name}, 开始MCP工具发现...")

        if tool.tool_type == "mcp":
            try:
                # 使用共享的MCP工具发现逻辑
                tool = await MCPToolDiscoveryService.update_tool_info(session, tool)

                if tool.is_active:
                    message = "工具已启用，MCP连接成功"
                    logger.info(f"工具启用成功: {tool.name}, 连接状态: {tool.is_active}")
                else:
                    # MCP连接失败，直接抛出异常
                    error_info = tool.tool_info.get("error", "MCP连接失败") if isinstance(tool.tool_info, dict) else "MCP连接失败"
                    logger.error(f"MCP工具连接失败: {tool.name}, 错误: {error_info}")
                    raise Exception("连接失败")

            except Exception as e:
                logger.error(f"MCP工具发现失败: {tool.name}, 错误: {str(e)}")
                logger.exception("详细错误信息:")

                # 记录错误信息到数据库，但不提交（因为要抛出异常）
                tool.is_active = False
                tool.tool_info = {
                    "error": f"启用时MCP连接失败: {str(e)}",
                    "error_type": type(e).__name__,
                    "timestamp": datetime.now().isoformat()
                }
                tool.updated_at = datetime.now()
                session.add(tool)
                session.commit()
                session.refresh(tool)

                # 直接抛出异常，让前端知道连接失败
                raise Exception("连接失败")
        else:
            # 非MCP工具直接设置为启用状态
            tool.is_active = True
            tool.updated_at = datetime.now()
            session.add(tool)
            session.commit()
            session.refresh(tool)
            message = "工具已启用"
            logger.info(f"非MCP工具启用成功: {tool.name}")

    else:
        # 禁用工具：直接设置状态
        logger.info(f"禁用工具: {tool.name}")
        tool.is_active = False
        tool.updated_at = datetime.now()

        # 清空MCP工具信息（可选，或者保留用于历史记录）
        if tool.tool_type == "mcp":
            tool.tool_info = {
                "status": "disabled",
                "disabled_at": datetime.now().isoformat(),
                "message": "工具已被手动禁用"
            }

        session.add(tool)
        session.commit()
        session.refresh(tool)
        message = "工具已禁用"
        logger.info(f"工具禁用成功: {tool.name}")

    return success_response(data=tool, message=message)