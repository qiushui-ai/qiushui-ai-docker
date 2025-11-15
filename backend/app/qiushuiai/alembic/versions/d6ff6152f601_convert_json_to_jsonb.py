"""convert_json_to_jsonb

Revision ID: d6ff6152f601
Revises: 9ec69dd4c006
Create Date: 2025-11-05 08:35:12.654284

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'd6ff6152f601'
down_revision = '9ec69dd4c006'
branch_labels = None
depends_on = None


def upgrade():
    # 1. qsa_usr_user (用户表)
    op.execute("ALTER TABLE qsa_usr_user ALTER COLUMN preferences TYPE jsonb USING preferences::jsonb")
    
    # 2. qsa_ai_provider (AI提供商表)
    op.execute("ALTER TABLE qsa_ai_provider ALTER COLUMN auth_config TYPE jsonb USING auth_config::jsonb")
    
    # 3. qsa_ai_model (AI模型表)
    op.execute("ALTER TABLE qsa_ai_model ALTER COLUMN llm_type TYPE jsonb USING llm_type::jsonb")
    
    # 4. qsa_agent (智能体表)
    op.execute("ALTER TABLE qsa_agent ALTER COLUMN capabilities TYPE jsonb USING capabilities::jsonb")
    op.execute("ALTER TABLE qsa_agent ALTER COLUMN settings TYPE jsonb USING settings::jsonb")
    op.execute("ALTER TABLE qsa_agent ALTER COLUMN tags TYPE jsonb USING tags::jsonb")
    
    # 5. qsa_kb_knowledge (知识库表)
    op.execute("ALTER TABLE qsa_kb_knowledge ALTER COLUMN tags TYPE jsonb USING tags::jsonb")
    op.execute("ALTER TABLE qsa_kb_knowledge ALTER COLUMN settings TYPE jsonb USING settings::jsonb")
    
    # 6. qsa_kb_document (知识库文档表)
    op.execute("ALTER TABLE qsa_kb_document ALTER COLUMN extra_data TYPE jsonb USING extra_data::jsonb")
    
    # 7. qsa_kb_chunk (知识库分块表)
    op.execute("ALTER TABLE qsa_kb_chunk ALTER COLUMN extra_data TYPE jsonb USING extra_data::jsonb")
    
    # 8. qsa_tools (工具表)
    op.execute("ALTER TABLE qsa_tools ALTER COLUMN tags TYPE jsonb USING tags::jsonb")
    op.execute("ALTER TABLE qsa_tools ALTER COLUMN tool_conf TYPE jsonb USING tool_conf::jsonb")
    
    # 9. qsa_prompts_libs (提示词库表)
    op.execute("ALTER TABLE qsa_prompts_libs ALTER COLUMN tags TYPE jsonb USING tags::jsonb")
    
    # 10. qsa_sys_tags (系统标签表)
    op.execute("ALTER TABLE qsa_sys_tags ALTER COLUMN tags TYPE jsonb USING tags::jsonb")
    
    # 11. qsa_chat_conversation (对话会话表)
    op.execute("ALTER TABLE qsa_chat_conversation ALTER COLUMN extra_data TYPE jsonb USING extra_data::jsonb")
    
    # 12. qsa_chat_message (对话消息表)
    op.execute("ALTER TABLE qsa_chat_message ALTER COLUMN tool_calls TYPE jsonb USING tool_calls::jsonb")
    op.execute("ALTER TABLE qsa_chat_message ALTER COLUMN tool_results TYPE jsonb USING tool_results::jsonb")
    op.execute("ALTER TABLE qsa_chat_message ALTER COLUMN extra_data TYPE jsonb USING extra_data::jsonb")
    
    # 13. qsa_chat_document (对话文档表)
    op.execute("ALTER TABLE qsa_chat_document ALTER COLUMN extra_data TYPE jsonb USING extra_data::jsonb")
    
    # 14. qsa_note_tag (笔记标签表)
    op.execute("ALTER TABLE qsa_note_tag ALTER COLUMN ext_data TYPE jsonb USING ext_data::jsonb")
    
    # 15. qsa_note_mine (我的笔记表)
    op.execute("ALTER TABLE qsa_note_mine ALTER COLUMN attachments TYPE jsonb USING attachments::jsonb")
    op.execute("ALTER TABLE qsa_note_mine ALTER COLUMN tags TYPE jsonb USING tags::jsonb")
    op.execute("ALTER TABLE qsa_note_mine ALTER COLUMN category TYPE jsonb USING category::jsonb")
    op.execute("ALTER TABLE qsa_note_mine ALTER COLUMN ext_data TYPE jsonb USING ext_data::jsonb")
    
    # 16. qsa_note_collect (收藏笔记表)
    op.execute("ALTER TABLE qsa_note_collect ALTER COLUMN media_urls TYPE jsonb USING media_urls::jsonb")
    op.execute("ALTER TABLE qsa_note_collect ALTER COLUMN category TYPE jsonb USING category::jsonb")
    op.execute("ALTER TABLE qsa_note_collect ALTER COLUMN tags TYPE jsonb USING tags::jsonb")
    op.execute("ALTER TABLE qsa_note_collect ALTER COLUMN platform_data TYPE jsonb USING platform_data::jsonb")
    op.execute("ALTER TABLE qsa_note_collect ALTER COLUMN extdata TYPE jsonb USING extdata::jsonb")
    
    # 17. qsa_note_whiteboard (白板表)
    op.execute("ALTER TABLE qsa_note_whiteboard ALTER COLUMN snapshot TYPE jsonb USING snapshot::jsonb")
    
    # 18. qsa_note_whiteboard_note (白板笔记关联表)
    op.execute("ALTER TABLE qsa_note_whiteboard_note ALTER COLUMN note_snapshot TYPE jsonb USING note_snapshot::jsonb")


def downgrade():
    # 回滚：将 JSONB 转换回 JSON
    # 1. qsa_usr_user
    op.execute("ALTER TABLE qsa_usr_user ALTER COLUMN preferences TYPE json USING preferences::json")
    
    # 2. qsa_ai_provider
    op.execute("ALTER TABLE qsa_ai_provider ALTER COLUMN auth_config TYPE json USING auth_config::json")
    
    # 3. qsa_ai_model
    op.execute("ALTER TABLE qsa_ai_model ALTER COLUMN llm_type TYPE json USING llm_type::json")
    
    # 4. qsa_agent
    op.execute("ALTER TABLE qsa_agent ALTER COLUMN capabilities TYPE json USING capabilities::json")
    op.execute("ALTER TABLE qsa_agent ALTER COLUMN settings TYPE json USING settings::json")
    op.execute("ALTER TABLE qsa_agent ALTER COLUMN tags TYPE json USING tags::json")
    
    # 5. qsa_kb_knowledge
    op.execute("ALTER TABLE qsa_kb_knowledge ALTER COLUMN tags TYPE json USING tags::json")
    op.execute("ALTER TABLE qsa_kb_knowledge ALTER COLUMN settings TYPE json USING settings::json")
    
    # 6. qsa_kb_document
    op.execute("ALTER TABLE qsa_kb_document ALTER COLUMN extra_data TYPE json USING extra_data::json")
    
    # 7. qsa_kb_chunk
    op.execute("ALTER TABLE qsa_kb_chunk ALTER COLUMN extra_data TYPE json USING extra_data::json")
    
    # 8. qsa_tools
    op.execute("ALTER TABLE qsa_tools ALTER COLUMN tags TYPE json USING tags::json")
    op.execute("ALTER TABLE qsa_tools ALTER COLUMN tool_conf TYPE json USING tool_conf::json")
    
    # 9. qsa_prompts_libs
    op.execute("ALTER TABLE qsa_prompts_libs ALTER COLUMN tags TYPE json USING tags::json")
    
    # 10. qsa_sys_tags
    op.execute("ALTER TABLE qsa_sys_tags ALTER COLUMN tags TYPE json USING tags::json")
    
    # 11. qsa_chat_conversation
    op.execute("ALTER TABLE qsa_chat_conversation ALTER COLUMN extra_data TYPE json USING extra_data::json")
    
    # 12. qsa_chat_message
    op.execute("ALTER TABLE qsa_chat_message ALTER COLUMN tool_calls TYPE json USING tool_calls::json")
    op.execute("ALTER TABLE qsa_chat_message ALTER COLUMN tool_results TYPE json USING tool_results::json")
    op.execute("ALTER TABLE qsa_chat_message ALTER COLUMN extra_data TYPE json USING extra_data::json")
    
    # 13. qsa_chat_document
    op.execute("ALTER TABLE qsa_chat_document ALTER COLUMN extra_data TYPE json USING extra_data::json")
    
    # 14. qsa_note_tag
    op.execute("ALTER TABLE qsa_note_tag ALTER COLUMN ext_data TYPE json USING ext_data::json")
    
    # 15. qsa_note_mine
    op.execute("ALTER TABLE qsa_note_mine ALTER COLUMN attachments TYPE json USING attachments::json")
    op.execute("ALTER TABLE qsa_note_mine ALTER COLUMN tags TYPE json USING tags::json")
    op.execute("ALTER TABLE qsa_note_mine ALTER COLUMN category TYPE json USING category::json")
    op.execute("ALTER TABLE qsa_note_mine ALTER COLUMN ext_data TYPE json USING ext_data::json")
    
    # 16. qsa_note_collect
    op.execute("ALTER TABLE qsa_note_collect ALTER COLUMN media_urls TYPE json USING media_urls::json")
    op.execute("ALTER TABLE qsa_note_collect ALTER COLUMN category TYPE json USING category::json")
    op.execute("ALTER TABLE qsa_note_collect ALTER COLUMN tags TYPE json USING tags::json")
    op.execute("ALTER TABLE qsa_note_collect ALTER COLUMN platform_data TYPE json USING platform_data::json")
    op.execute("ALTER TABLE qsa_note_collect ALTER COLUMN extdata TYPE json USING extdata::json")
    
    # 17. qsa_note_whiteboard
    op.execute("ALTER TABLE qsa_note_whiteboard ALTER COLUMN snapshot TYPE json USING snapshot::json")
    
    # 18. qsa_note_whiteboard_note
    op.execute("ALTER TABLE qsa_note_whiteboard_note ALTER COLUMN note_snapshot TYPE json USING note_snapshot::json")
