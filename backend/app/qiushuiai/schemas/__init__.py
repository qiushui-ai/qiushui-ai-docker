# 导入所有 SQLModel 模型以便 Alembic 能够识别
from sqlmodel import SQLModel

# 导入所有模型以确保它们被注册到 SQLModel.metadata
from .user import UsrUser, UsrUserBase, UsrUserRegister, UsrUserUpdate, UsrUserUpdateMe, UsrUserUpdatePassword, Token, TokenPayload
from .agent import Agent, AgentBase, AgentUpdate
from .knowledge import KbKnowledge, KbKnowledgeBase, KbKnowledgeUpdate, KbDocument, KbDocumentBase, KbDocumentUpdate, KbChunk, KbChunkBase, KbChunkUpdate
from .prompts import PromptsLib, PromptsLibBase, PromptsLibCreate, PromptsLibUpdate, PromptsLibPublic
from .sys import SysTags, SysTagsBase, SysTagsCreate, SysTagsUpdate, SysTagsPublic
from .chat import (
    ChatConversation, ChatConversationBase, ChatConversationUpdate,
    ChatMessage, ChatMessageBase, ChatMessageUpdate,
    ChatDocument, ChatDocumentBase, ChatDocumentCreate, ChatDocumentUpdate, ChatDocumentPublic
)
from .tools import Tools, ToolsBase, ToolsUpdate
from .aimodel import AIModel, AIModelBase, AIModelUpdate, AIProvider, AIProviderBase, AIProviderUpdate
from .note import (
    NoteTag, NoteTagBase, NoteTagCreate, NoteTagUpdate, NoteTagPublic,
    NoteMine, NoteMineBase, NoteMineCreate, NoteMineUpdate, NoteMinePublic,
    NoteCollect, NoteCollectBase, NoteCollectCreate, NoteCollectUpdate, NoteCollectPublic
)

# 确保所有模型都被导入，这样 SQLModel.metadata 就能包含所有表
__all__ = [
    "SQLModel",
    "UsrUser", "UsrUserBase", "UsrUserRegister", "UsrUserUpdate", "UsrUserUpdateMe", "UsrUserUpdatePassword", "Token", "TokenPayload",
    "Agent", "AgentBase", "AgentUpdate",
    "KbKnowledge", "KbKnowledgeBase", "KbKnowledgeUpdate", "KbDocument", "KbDocumentBase", "KbDocumentUpdate", "KbChunk", "KbChunkBase", "KbChunkUpdate",
    "PromptsLib", "PromptsLibBase", "PromptsLibCreate", "PromptsLibUpdate", "PromptsLibPublic",
    "SysTags", "SysTagsBase", "SysTagsCreate", "SysTagsUpdate", "SysTagsPublic",
    "ChatConversation", "ChatConversationBase", "ChatConversationUpdate",
    "ChatMessage", "ChatMessageBase", "ChatMessageUpdate",
    "ChatDocument", "ChatDocumentBase", "ChatDocumentCreate", "ChatDocumentUpdate", "ChatDocumentPublic",
    "Tools", "ToolsBase", "ToolsUpdate",
    "AIModel", "AIModelBase", "AIModelUpdate", "AIProvider", "AIProviderBase", "AIProviderUpdate",
    "NoteTag", "NoteTagBase", "NoteTagCreate", "NoteTagUpdate", "NoteTagPublic",
    "NoteMine", "NoteMineBase", "NoteMineCreate", "NoteMineUpdate", "NoteMinePublic",
    "NoteCollect", "NoteCollectBase", "NoteCollectCreate", "NoteCollectUpdate", "NoteCollectPublic"
]
