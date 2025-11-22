from fastapi import APIRouter

from qiushuiai.core.config import settings

from qiushuiai.modules.knowledge import knowledge_api, document_api, vector_search_api
from qiushuiai.modules.user import user_api
from qiushuiai.modules.agent import agent_api
from qiushuiai.modules.chat import conversation_api, message_api
from qiushuiai.modules.utils import upload_api
from qiushuiai.modules.tools import tools_router
from qiushuiai.modules.aimodel import aimodel_api
from qiushuiai.modules.prompts import prompts_router
from qiushuiai.modules.sys import sys_tags_api
from qiushuiai.modules.note import note_tag_api, note_mine_api, note_collect_api, note_collect_creater_api
from qiushuiai.modules.whiteboard import whiteboard_api, whiteboard_note_api
from qiushuiai.modules.knowledge import knowledge_search_api

api_router = APIRouter()

api_router.include_router(knowledge_api.router)
api_router.include_router(document_api.router)
api_router.include_router(vector_search_api.router)
api_router.include_router(knowledge_search_api.router)
api_router.include_router(user_api.router)
api_router.include_router(agent_api.router)
api_router.include_router(conversation_api.router)
api_router.include_router(message_api.router)
api_router.include_router(upload_api.router)
api_router.include_router(tools_router)
api_router.include_router(aimodel_api.router)
api_router.include_router(prompts_router)
api_router.include_router(sys_tags_api.router)
api_router.include_router(note_tag_api.router)
api_router.include_router(note_mine_api.router)
api_router.include_router(note_collect_api.router)
api_router.include_router(note_collect_creater_api.router)
api_router.include_router(whiteboard_api.router)
api_router.include_router(whiteboard_note_api.router)