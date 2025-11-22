"""
现代化 React Agent 实现
====================

使用 LangChain 新版本 create_agent API 构建的智能代理，
包含持久化、工具集成和高级中间件功能。

设计为与 LangGraph 服务器架构兼容：
- 导出未编译的图，让服务器注入 checkpointer 和 store
- 保留完整的工具功能集，包括 PostgreSQL 持久化内存
- 支持动态中间件和高级状态管理
"""
import json
import os
import uuid
import httpx
import time
from typing import TypedDict, List, Any, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv
from threading import Lock

from langchain.agents import create_agent
from langchain.agents.middleware import (
    SummarizationMiddleware,
    AgentMiddleware,
    dynamic_prompt,
    ModelRequest,
    ModelResponse
)
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
import os
from langgraph.config import get_stream_writer


# 加载环境变量
load_dotenv()



import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

# ============== MCP 工具管理 ==============
_MCP_CLIENT = None
_MCP_TOOLS = []
_MCP_LOCK = Lock()
_MCP_INITIALIZED = False


def fetch_ai_mcps():
    """从 API 获取 AI 模型列表"""
    api_url = os.getenv("QIUSHUI_AI_BACKEND_HOST")+"/api/v1/tools/mytools"

    try:
        with httpx.Client() as client:
            response = client.post(api_url, json={})
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('items', [])
            else:
                print(f"API 请求失败，状态码: {response.status_code} - {response.text} - {api_url}")
                return []
    except Exception as e:
        print(f"获取 AI 模型列表时出错: {str(e)}")
        return []

async def _init_mcp_client():
    """异步初始化 MCP 客户端"""
    global _MCP_CLIENT, _MCP_TOOLS
    
    try:
        mcps_data = fetch_ai_mcps()
        mcps_config = {}
        print(f"--mcps_data: {mcps_data}")
            
        for mcp_data in mcps_data:
            if mcp_data.get('sub_type') in ["sse", "streamableHttp"]:
                uuid = mcp_data.get('uuid')
                sub_type = mcp_data.get('sub_type')
                url = mcp_data.get('tool_conf').get('url')
                headers = mcp_data.get('tool_conf').get('headers')

                # headers 转换成 dict
                if isinstance(headers, str):
                    try:
                        headers = json.loads(headers)
                    except json.JSONDecodeError:
                        headers = None

                if headers:
                    mcps_config[uuid] = {
                        "transport": sub_type,
                        "url": url,
                        "headers": headers
                    }
                else:
                    mcps_config[uuid] = {
                        "transport": sub_type,
                        "url": url
                    }

        print(f"--mcps_config: {mcps_config}")
     
        print("  🔌 连接 MCP 服务器...")
        client = MultiServerMCPClient(mcps_config)
        
        print("  📦 获取 MCP 工具列表...")
        tools = await client.get_tools()
        
        _MCP_CLIENT = client
        _MCP_TOOLS = tools
        
        tool_names = [t.name for t in tools]
        print(f"  ✅ MCP 工具加载成功: {tool_names}")
        
    except Exception as e:
        print(f"  ❌ MCP 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        _MCP_TOOLS = []

def _run_async_in_thread():
    """在新线程中运行异步初始化"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_mcp_client())
    finally:
        loop.close()

def init_mcp_sync():
    """同步初始化 MCP 工具(线程安全)"""
    global _MCP_INITIALIZED
    
    with _MCP_LOCK:
        if _MCP_INITIALIZED:
            print("  ℹ️ MCP 工具已初始化,跳过")
            return
        
        try:
            print("  🔄 在独立线程中初始化 MCP...")
            # 使用线程池在新线程中执行异步代码
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_run_async_in_thread)
                future.result(timeout=30)  # 30秒超时
            
            _MCP_INITIALIZED = True
            print(f"  ✅ MCP 初始化完成,共 {len(_MCP_TOOLS)} 个工具")
            
        except Exception as e:
            print(f"  ❌ MCP 同步初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()

def get_mcp_tools():
    """获取 MCP 工具列表"""
    return _MCP_TOOLS

# ============== 模块初始化 ==============
print("🚀 初始化模块...")
print("🔄 加载 MCP 工具...")
init_mcp_sync()



# 全局模型字典和缓存控制
_ALL_MODELS = {}
_MODELS_CACHE_TIME = 0
_MODELS_LOCK = Lock()


def fetch_ai_models():
    """从 API 获取 AI 模型列表"""
    api_url = os.getenv("QIUSHUI_AI_BACKEND_HOST")+"/api/v1/aimodel/model/mymodels"

    try:
        with httpx.Client() as client:
            response = client.post(api_url, json={})
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('items', [])
            else:
                print(f"API 请求失败，状态码: {response.status_code} - {response.text} - {api_url}")
                return []
    except Exception as e:
        print(f"获取 AI 模型列表时出错: {str(e)}")
        return []


def refresh_models_cache() -> Dict[str, ChatOpenAI]:
    """刷新模型缓存"""
    global _ALL_MODELS, _MODELS_CACHE_TIME
    
    with _MODELS_LOCK:
        print("🔄 开始刷新模型缓存...")
        try:
            models_data = fetch_ai_models()
            new_models = {}
            default_model = None
            
            for model_data in models_data:
                try:
                    llm_id = model_data.get('llm_id')
                    api_base_url = model_data.get('provider_api_base_url')
                    api_secret = model_data.get('provider_api_secret')
                    max_tokens = model_data.get('max_tokens')
                    is_default = model_data.get('is_default', False)
                    
                    # 限制 max_tokens，避免超出模型限制
                    if max_tokens and max_tokens > 128000:
                        print(f"⚠️ 模型 {llm_id} 的 max_tokens ({max_tokens}) 超过限制，调整为 128000")
                        max_tokens = 128000
                    
                    # 创建模型实例
                    model = ChatOpenAI(
                        model=llm_id,
                        # temperature=0.1,
                        max_tokens=max_tokens,
                        api_key=api_secret,
                        base_url=api_base_url
                    )
                    
                    new_models[llm_id] = model
                    
                    if is_default:
                        default_model = model
                    
                    print(f"  ✓ 加载模型: {llm_id} (默认: {is_default}, max_tokens: {max_tokens})")
                    
                except Exception as e:
                    print(f"  ✗ 加载模型 {model_data.get('llm_id', 'unknown')} 失败: {str(e)}")
                    continue
            
            _ALL_MODELS = new_models
            _MODELS_CACHE_TIME = time.time()
            print(f"✅ 模型缓存刷新完成，共 {len(_ALL_MODELS)} 个模型: {list(_ALL_MODELS.keys())}")
            
            return _ALL_MODELS, default_model
            
        except Exception as e:
            print(f"❌ 刷新模型缓存失败: {str(e)}")
            return _ALL_MODELS, None


def get_models() -> Dict[str, ChatOpenAI]:
    """获取模型字典（不刷新）"""
    return _ALL_MODELS


def instantiate_models(models_data: List[Dict]) -> tuple[List[ChatOpenAI], Optional[ChatOpenAI]]:
    """实例化模型列表并返回所有模型和默认模型（初始化时使用）"""
    global _ALL_MODELS, _MODELS_CACHE_TIME
    
    instantiated_models = []
    default_model = None

    for model_data in models_data:
        try:
            # 提取模型配置
            api_base_url = model_data.get('provider_api_base_url')
            api_secret = model_data.get('provider_api_secret')
            llm_id = model_data.get('llm_id')
            max_tokens = model_data.get('max_tokens')
            is_default = model_data.get('is_default', False)

            # 限制 max_tokens
            if max_tokens and max_tokens > 128000:
                print(f"⚠️ 模型 {llm_id} 的 max_tokens ({max_tokens}) 超过限制，调整为 128000")
                max_tokens = 128000

            # 创建模型实例
            model = ChatOpenAI(
                model=llm_id,
                # temperature=0.1,
                max_tokens=max_tokens,
                api_key=api_secret,
                base_url=api_base_url
            )

            instantiated_models.append(model)
            
            # 存储到全局字典中
            _ALL_MODELS[llm_id] = model

            # 设置默认模型
            if is_default:
                default_model = model

            print(f"已实例化模型: {llm_id} (默认: {is_default}, max_tokens: {max_tokens})")

        except Exception as e:
            print(f"实例化模型 {model_data.get('llm_id', 'unknown')} 时出错: {str(e)}")
            continue

    _MODELS_CACHE_TIME = time.time()
    print(f"全局模型字典已填充: {list(_ALL_MODELS.keys())}")
    return instantiated_models, default_model


@tool
def memory_tool(action: str, key: str = "", value: str = "", runtime: ToolRuntime = None) -> str:
    """使用 LangGraph store 存储和检索记忆.

    参数:
    - action: 操作类型 ("store", "retrieve", "list")
    - key: 记忆的关键词（用于存储和检索）
    - value: 要存储的值（仅在 action="store" 时需要）

    功能:
    - 跨会话永久存储重要信息
    - 按用户隔离，确保隐私安全
    - 支持关键词检索和列表查看
    """
    if not runtime:
        return "记忆功能需要运行时环境支持"

    try:
        # 从运行时获取 store 和用户信息
        store = runtime.store
        config = runtime.config

        if not store:
            return "记忆存储服务暂时不可用"

        # 获取用户ID，用于数据隔离
        user_id = config.get("configurable", {}).get("user_id", "default") if config else "default"
        namespace = ("memories", user_id)

        if action == "store":
            if not key or not value:
                return "存储记忆需要提供关键词和内容"

            memory_id = str(uuid.uuid4())
            store.put(namespace, memory_id, {
                "key": key,
                "value": value,
                "timestamp": datetime.now().isoformat()
            })
            return f"✅ 已存储记忆: {key} -> {value}"

        elif action == "retrieve":
            if not key:
                return "检索记忆需要提供关键词"

            memories = store.search(namespace, query=key)
            if memories:
                results = [f"{m.value['key']}: {m.value['value']}" for m in memories[:5]]
                return f"🧠 找到的记忆:\n" + "\n".join(results)
            return f"❌ 未找到关键词 '{key}' 相关的记忆"

        elif action == "list":
            memories = store.search(namespace)
            if memories:
                results = [f"{m.value['key']}: {m.value['value']}" for m in memories[:10]]
                return f"📝 所有记忆 (最近10条):\n" + "\n".join(results)
            return "📭 暂无存储的记忆"

        return "❌ 无效操作。请使用: store（存储）, retrieve（检索）, 或 list（列表）"

    except Exception as e:
        return f"记忆操作失败: {str(e)}"


# 动态系统提示中间件
@dynamic_prompt
def adaptive_system_prompt(request: ModelRequest) -> str:
    """根据用户角色和会话生成上下文感知的系统提示."""
    context = getattr(request.runtime, 'context', {}) or {}
    prompt = None
    if isinstance(context, dict):
        chat_config = context.get('chat_config', {})
        system_prompt_cfg = chat_config.get('system_prompt', {})
        prompt = system_prompt_cfg.get('prompt') if isinstance(system_prompt_cfg, dict) else None
    
    if prompt:
        return prompt
    
    return ""

# 动态模型选择中间件
class DynamicModelMiddleware(AgentMiddleware):
    """同时支持同步和异步的模型选择中间件，根据前端配置动态切换模型"""
    
    def wrap_model_call(self, request: ModelRequest, handler) -> ModelResponse:
        """同步版本"""
        context = getattr(request.runtime, 'context', {}) or {}
        if isinstance(context, dict):
            chat_config = context.get('chat_config', {})
            model_config = chat_config.get('model_config', {})
            
            if model_config:
                # 检查是否需要更新模型列表
                is_update = model_config.get('is_update_model_list', False)
                if is_update:
                    print(f"[同步] 前端请求更新模型列表")
                    refresh_models_cache()
                
                # 获取前端指定的模型名称 - 使用 llm_id
                model_name = model_config.get('llm_id')
                print(f"[同步] 前端请求使用模型: {model_name} (uuid: {model_config.get('uuid')})")
                
                # 获取可用模型
                available_models = get_models()
                
                if model_name and model_name in available_models:
                    request.model = available_models[model_name]
                    print(f"[同步] ✅ 已切换到模型: {model_name}")
                else:
                    print(f"[同步] ⚠️ 模型 {model_name} 未找到，使用默认模型")
                    print(f"[同步] 可用模型列表: {list(available_models.keys())}")
        
        return handler(request)
    
    async def awrap_model_call(self, request: ModelRequest, handler) -> ModelResponse:
        """异步版本 - LangGraph 服务器会调用这个"""
        context = getattr(request.runtime, 'context', {}) or {}
        if isinstance(context, dict):
            chat_config = context.get('chat_config', {})
            model_config = chat_config.get('model_config', {})
            
            if model_config:
                # 检查是否需要更新模型列表
                is_update = model_config.get('is_update_model_list', False)
                if is_update:
                    print(f"[异步] 🔄 前端请求更新模型列表")
                    refresh_models_cache()
                
                # 获取前端指定的模型名称 - 使用 llm_id
                model_name = model_config.get('llm_id')
                print(f"[异步] 前端请求使用模型: {model_name} (uuid: {model_config.get('uuid')})")
                
                # 获取可用模型
                available_models = get_models()
                
                if model_name and model_name in available_models:
                    request.model = available_models[model_name]
                    print(f"[异步] ✅ 已切换到模型: {model_name}")
                else:
                    print(f"[异步] ⚠️ 模型 {model_name} 未找到，使用默认模型")
                    print(f"[异步] 可用模型列表: {list(available_models.keys())}")
        
        return await handler(request)

@tool
def search_multiple_knowledgebases(query: str,runtime: ToolRuntime) -> str:
    """在多个知识库中搜索相关内容"""

    print(f"runtime:{runtime}")
    context = getattr(runtime, 'context', {}) or {}
    print(f"context: {context}")

    writer = get_stream_writer()  
    writer(f"==============在多个知识库中搜索相关内容")
   
    knowledge_ids = []
    
    if isinstance(context, dict):
        chat_config = context.get('chat_config', {})
        agent_config = chat_config.get('agent_config', {})
        knowledge_list=agent_config.get('knowledge_list', [])
        print(f"knowledge_list: {knowledge_list}")
        for knowledge in knowledge_list:
            knowledge_ids.append(knowledge.get('knowledge_id'))
        print(f"knowledge_ids: {knowledge_ids}")
        if(len(knowledge_ids) == 0):
            return ""

    api_url = os.getenv("QIUSHUI_AI_BACKEND_HOST")+"/api/v1/knowledge-search/search-multiple-knowledge-bases"

    try:
        with httpx.Client() as client:
            response = client.post(api_url, json={"query": query,"similarity_threshold":os.getenv("SIMILARITY_THRESHOLD")
            ,"limit":5
            ,"knowledge_base_ids":knowledge_ids})
            if response.status_code == 200:
                data = response.json()
                # print(f"知识库中找到内容了: {data}")
                return data.get('data')
            else:
                print(f"获取知识库出现异常1: {response.status_code} - {response.text} - {api_url}")
                
    except Exception as e:
        print(f"获取知识库出现异常2: {str(e)}")
    
  
    return f"{data}"

def create_complete_agent():
    """创建完整功能的代理，包含所有新版本特性."""

    # 获取 AI 模型列表
    try:
        models_data = fetch_ai_models()
    except Exception as e:
        print(f"获取模型列表失败，使用环境变量配置: {str(e)}")
        models_data = []

    print("================")
    # 使用 API 获取的模型
    all_models, default_model = instantiate_models(models_data)

    if default_model:
        model = default_model
        print(f"使用默认模型: {model}")
    else:
        if all_models:
            model = all_models[0]
            print(f"使用第一个可用模型: {model}")
        else:
            raise ValueError("没有可用的模型，请检查模型配置")

     # 获取 MCP 工具
    mcp_tools = get_mcp_tools()
    print(f"📦 MCP 工具数量: {len(mcp_tools)}")
    print(f"-----mcp_tools: {mcp_tools}") 

    # 定义完整工具集
    tools = [
         search_multiple_knowledgebases,
        # memory_tool,
        *mcp_tools,  # 展开 MCP 工具列表
    ]
    
    print(f"🔧 总工具数: {len(tools)}")

    # 创建中间件实例
    dynamic_model_middleware = DynamicModelMiddleware()

    # 创建代理
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=None,
        middleware=[
            adaptive_system_prompt,
            dynamic_model_middleware
        ]
    )

    return agent


def create_graph():
    """创建并返回未编译的代理，用于服务器部署."""
    return create_complete_agent()


# LangGraph 服务器默认加载的 graph 导出
graph = create_graph()