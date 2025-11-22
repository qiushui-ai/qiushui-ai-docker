"""MCP工具发现服务"""
import json
import asyncio
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from fastmcp import Client
from fastmcp.client.auth import BearerAuth

from qiushuiai.schemas.tools import Tools

# 配置日志记录器
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MCPToolDiscoveryService:
    """MCP工具发现服务，用于连接MCP服务器并获取工具信息"""

    @staticmethod
    async def discover_tools(tool: Tools) -> Tuple[bool, Dict[str, Any]]:
        """
        发现MCP工具信息

        Args:
            tool: 工具对象，包含连接配置

        Returns:
            Tuple[bool, Dict[str, Any]]: (is_active, tool_info)
            - is_active: 连接是否成功
            - tool_info: 工具信息或错误信息
        """
        logger.info(f"=== 开始MCP工具发现 ===")
        logger.info(f"工具名称: {tool.name}")
        logger.info(f"工具类型: {tool.tool_type}")
        logger.info(f"子类型: {tool.sub_type}")

        try:
            # 检查是否是MCP类型工具
            if tool.tool_type != "mcp":
                logger.info(f"跳过非MCP类型工具: {tool.tool_type}")
                return True, {"message": "非MCP类型工具，跳过发现"}

            # 检查sub_type是否支持
            if tool.sub_type not in ["streamableHttp", "sse"]:
                logger.warning(f"不支持的MCP传输类型: {tool.sub_type}")
                return True, {"message": f"不支持的MCP传输类型: {tool.sub_type}"}

            # 解析配置
            logger.info("解析工具配置...")
            tool_conf = tool.tool_conf or {}
            logger.info(f"工具配置: {tool_conf}")

            url = tool_conf.get("url")
            if not url:
                logger.error("工具配置中缺少URL信息")
                return False, {"error": "工具配置中缺少URL信息"}

            logger.info(f"MCP服务器URL: {url}")

            # 解析认证头
            headers = MCPToolDiscoveryService._parse_headers(tool_conf.get("headers"))
            api_key = tool_conf.get("api_key", "")
            timeout = tool_conf.get("timeout", 60)

            logger.info(f"解析的认证头: {headers}")
            logger.info(f"API密钥长度: {len(api_key) if api_key else 0}")
            logger.info(f"连接超时设置: {timeout}秒")

            # 创建认证对象
            auth = None
            if api_key:
                # 移除Bearer前缀（如果存在）
                token = api_key.replace("Bearer ", "")
                auth = BearerAuth(token=token)
                logger.info(f"创建Bearer认证，Token长度: {len(token)}")
            else:
                logger.info("未配置API密钥，使用无认证连接")

            # 连接MCP服务器并获取信息
            logger.info("开始连接MCP服务器...")
            tool_info = await MCPToolDiscoveryService._connect_and_discover(
                tool=tool,
                url=url,
                auth=auth,
                timeout=timeout,
                headers=headers
            )

            logger.info("MCP工具发现成功完成")
            logger.info(f"发现的工具数量: {tool_info.get('total_tools', 0)}")
            logger.info(f"发现的资源数量: {tool_info.get('total_resources', 0)}")
            logger.info(f"发现的提示数量: {tool_info.get('total_prompts', 0)}")

            return True, tool_info

        except Exception as e:
            logger.error(f"MCP工具发现失败: {str(e)}")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.exception("详细错误信息:")

            error_info = {
                "error": f"MCP工具发现失败: {str(e)}",
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }
            return False, error_info

    @staticmethod
    def _parse_headers(headers_raw: Any) -> Dict[str, str]:
        """解析认证头信息"""
        try:
            if not headers_raw:
                return {}
            elif isinstance(headers_raw, dict):
                return headers_raw
            elif isinstance(headers_raw, str):
                return json.loads(headers_raw)
            else:
                return {}
        except Exception:
            return {}

    @staticmethod
    async def _connect_and_discover(
        tool: Tools,
        url: str,
        auth: Optional[BearerAuth],
        timeout: int,
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """连接MCP服务器并发现工具信息"""
        logger.info(f"创建MCP客户端连接...")
        logger.info(f"服务器地址: {url}")
        logger.info(f"超时时间: {timeout}秒")
        logger.info(f"认证方式: {'Bearer Token' if auth else '无认证'}")

        # 根据sub_type选择传输方式
        logger.info(f"选择传输方式: {tool.sub_type}")
        if tool.sub_type == "sse":
            from fastmcp.client.transports import SSETransport
            transport = SSETransport(url=url, auth=auth)
        else:  # streamableHttp
            from fastmcp.client.transports import StreamableHttpTransport
            transport = StreamableHttpTransport(url=url, auth=auth)

        async with Client(transport=transport) as client:
            logger.info("客户端连接已建立")

            # 测试连接
            logger.info("执行连接测试 (ping)...")
            await client.ping()
            logger.info("连接测试成功!")

            # 获取服务器信息
            logger.info("获取可用工具列表...")
            tools_list = await client.list_tools()
            logger.info(f"获取到 {len(tools_list)} 个工具")

            logger.info("获取可用资源列表...")
            resources_list = await client.list_resources()
            logger.info(f"获取到 {len(resources_list)} 个资源")

            logger.info("获取可用提示列表...")
            prompts_list = await client.list_prompts()
            logger.info(f"获取到 {len(prompts_list)} 个提示")

            # 转换为字典格式
            logger.info("转换工具信息为字典格式...")
            tools_info = []
            for i, mcp_tool in enumerate(tools_list):
                logger.info(f"处理工具 {i+1}/{len(tools_list)}: {mcp_tool.name}")
                tool_dict = {
                    "name": mcp_tool.name,
                    "description": mcp_tool.description,
                    "inputSchema": (
                        mcp_tool.inputSchema.model_dump()
                        if hasattr(mcp_tool.inputSchema, 'model_dump')
                        else mcp_tool.inputSchema
                    )
                }
                tools_info.append(tool_dict)
                logger.info(f"  - 描述: {mcp_tool.description}")

            logger.info("转换资源信息为字典格式...")
            resources_info = []
            for i, resource in enumerate(resources_list):
                logger.info(f"处理资源 {i+1}/{len(resources_list)}: {resource.name}")
                resource_dict = {
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description,
                    "mimeType": resource.mimeType
                }
                resources_info.append(resource_dict)
                logger.info(f"  - URI: {resource.uri}")
                logger.info(f"  - 类型: {resource.mimeType}")

            logger.info("转换提示信息为字典格式...")
            prompts_info = []
            for i, prompt in enumerate(prompts_list):
                logger.info(f"处理提示 {i+1}/{len(prompts_list)}: {prompt.name}")
                prompt_dict = {
                    "name": prompt.name,
                    "description": prompt.description,
                    "arguments": (
                        prompt.arguments.model_dump()
                        if hasattr(prompt.arguments, 'model_dump')
                        else prompt.arguments
                    )
                }
                prompts_info.append(prompt_dict)
                logger.info(f"  - 描述: {prompt.description}")

            result = {
                "connection_status": "success",
                "discovered_at": datetime.now().isoformat(),
                "server_url": url,
                "tools": tools_info,
                "resources": resources_info,
                "prompts": prompts_info,
                "total_tools": len(tools_info),
                "total_resources": len(resources_info),
                "total_prompts": len(prompts_info)
            }

            logger.info("=== MCP服务器信息获取完成 ===")
            logger.info(f"总计: {len(tools_info)} 工具, {len(resources_info)} 资源, {len(prompts_info)} 提示")

            return result

    @staticmethod
    async def update_tool_info(session, tool: Tools) -> Tools:
        """
        更新工具的MCP信息

        Args:
            session: 数据库会话
            tool: 工具对象

        Returns:
            Tools: 更新后的工具对象
        """
        logger.info(f"开始更新工具MCP信息: {tool.name} (ID: {tool.id})")

        is_active, tool_info = await MCPToolDiscoveryService.discover_tools(tool)

        logger.info(f"工具发现结果 - 连通状态: {is_active}")

        # 更新工具信息
        old_is_active = tool.is_active
        tool.is_active = is_active
        tool.tool_info = tool_info
        tool.updated_at = datetime.now()

        if old_is_active != is_active:
            logger.info(f"工具状态已变更: {old_is_active} -> {is_active}")

        # 保存到数据库
        logger.info("保存工具信息到数据库...")
        session.add(tool)
        session.commit()
        session.refresh(tool)

        logger.info(f"工具MCP信息更新完成: {tool.name}")
        logger.info(f"=== 工具发现流程结束 ===")

        return tool