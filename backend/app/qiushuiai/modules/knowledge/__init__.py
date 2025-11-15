# 知识库模块

from .document_api import router as document_router
from .knowledge_api import router as knowledge_router
from .vector_search_api import router as vector_search_router
from .knowledge_search_api import router as knowledge_search_router

# 导出所有路由
__all__ = ["document_router", "knowledge_router", "vector_search_router", "knowledge_search_router"]
