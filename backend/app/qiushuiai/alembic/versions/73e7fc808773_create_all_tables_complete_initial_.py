"""create_all_tables_complete_initial_schema

Revision ID: 73e7fc808773
Revises: 
Create Date: 2025-10-30 23:22:10.796074

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '73e7fc808773'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. 创建用户表 qsa_usr_user
    op.create_table(
        'qsa_usr_user',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=254), nullable=False),
        sa.Column('password', sa.String(length=128), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('avatar', sa.String(), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_phone_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='member'),
        sa.Column('last_login', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('login_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('preferences', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('is_del', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 2. 创建AI提供商表 qsa_ai_provider
    op.create_table(
        'qsa_ai_provider',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('logo_url', sa.String(length=300), nullable=True),
        sa.Column('api_base_url', sa.String(length=300), nullable=True),
        sa.Column('auth_config', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('api_secret', sa.String(length=300), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 3. 创建AI模型表 qsa_ai_model
    op.create_table(
        'qsa_ai_model',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('provider_id', sa.Integer(), nullable=False),
        sa.Column('llm_id', sa.String(length=200), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('llm_type', postgresql.JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('context_window', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 4. 创建智能体表 qsa_agent
    op.create_table(
        'qsa_agent',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('avatar', sa.String(), nullable=True),
        sa.Column('prompt_template', sa.String(), nullable=True),
        sa.Column('llm_id', sa.Integer(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('capabilities', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('settings', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('is_del', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 5. 创建知识库表 qsa_kb_knowledge
    op.create_table(
        'qsa_kb_knowledge',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True, server_default='default'),
        sa.Column('embedding_model', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('chunk_size', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('chunk_overlap', sa.Integer(), nullable=False, server_default='200'),
        sa.Column('document_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('index_status', sa.String(length=20), nullable=False, server_default='ready'),
        sa.Column('last_indexed', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('tags', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('settings', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('is_del', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 6. 创建知识库文档表 qsa_kb_document
    op.create_table(
        'qsa_kb_document',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('knowledge_base_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=True),
        sa.Column('file_type', sa.String(length=50), nullable=False, server_default='text'),
        sa.Column('file_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('content', sa.String(), nullable=True),
        sa.Column('extra_data', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('hash', sa.String(length=64), nullable=True),
        sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('token_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='processed'),
        sa.Column('extraction_tool', sa.String(length=100), nullable=True),
        sa.Column('embedding_model', sa.String(length=100), nullable=True),
        sa.Column('processed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 7. 创建知识库分块表 qsa_kb_chunk
    op.create_table(
        'qsa_kb_chunk',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('embedding', sa.Text(), nullable=True),
        sa.Column('extra_data', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('token_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('similarity_threshold', sa.Numeric(5, 4), nullable=False, server_default='0.8000'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 8. 创建工具表 qsa_tools
    op.create_table(
        'qsa_tools',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('tool_type', sa.String(length=50), nullable=False, server_default='function'),
        sa.Column('tags', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('last_used_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('tool_conf', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('sub_type', sa.String(length=50), nullable=False, server_default='function'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 9. 创建提示词库表 qsa_prompts_libs
    op.create_table(
        'qsa_prompts_libs',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('prompts', sa.String(), nullable=False),
        sa.Column('remark', sa.String(), nullable=True),
        sa.Column('tags', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 10. 创建系统标签表 qsa_sys_tags
    op.create_table(
        'qsa_sys_tags',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('puuid', sa.String(length=100), nullable=True),
        sa.Column('name', sa.String(length=300), nullable=False),
        sa.Column('pname', sa.String(length=300), nullable=True, server_default='active'),
        sa.Column('remark', sa.String(length=300), nullable=True, server_default='active'),
        sa.Column('sortorder', sa.Integer(), nullable=True),
        sa.Column('flag', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 11. 创建对话会话表 qsa_chat_conversation
    op.create_table(
        'qsa_chat_conversation',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('summary', sa.String(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_cost', sa.Float(), nullable=True),
        sa.Column('llm_uuid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_uuid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('prompt_uuid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('extra_data', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('last_message_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 12. 创建对话消息表 qsa_chat_message
    op.create_table(
        'qsa_chat_message',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(length=20), nullable=False, server_default='text'),
        sa.Column('tool_calls', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('tool_results', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('extra_data', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('parent_message_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 13. 创建对话文档表 qsa_chat_document
    op.create_table(
        'qsa_chat_document',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('chat_conversation_id', sa.Integer(), nullable=True),
        sa.Column('chat_conversation_uuid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=True),
        sa.Column('file_type', sa.String(length=50), nullable=False, server_default='text'),
        sa.Column('file_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('content', sa.String(), nullable=True),
        sa.Column('extra_data', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('hash', sa.String(length=64), nullable=True),
        sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('token_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='processed'),
        sa.Column('extraction_tool', sa.String(length=100), nullable=True),
        sa.Column('embedding_model', sa.String(length=100), nullable=True),
        sa.Column('processed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 14. 创建笔记标签表 qsa_note_tag
    op.create_table(
        'qsa_note_tag',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('tag_name', sa.String(length=50), nullable=False),
        sa.Column('tag_path', sa.String(length=500), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('use_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('ext_data', postgresql.JSON(), nullable=True),
        sa.Column('status', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 15. 创建我的笔记表 qsa_note_mine
    op.create_table(
        'qsa_note_mine',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content', sa.String(), nullable=True),
        sa.Column('attachments', postgresql.JSON(), nullable=True),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('category', postgresql.JSON(), nullable=True),
        sa.Column('collect_id', sa.Integer(), nullable=True),
        sa.Column('ext_data', postgresql.JSON(), nullable=True),
        sa.Column('status', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 16. 创建收藏笔记表 qsa_note_collect
    op.create_table(
        'qsa_note_collect',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.String(length=100), nullable=False),
        sa.Column('platform', sa.String(length=20), nullable=False),
        sa.Column('content_type', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('cn_content', sa.String(), nullable=True),
        sa.Column('cover_url', sa.String(length=500), nullable=True),
        sa.Column('media_urls', postgresql.JSON(), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('author_id', sa.String(length=100), nullable=True),
        sa.Column('author_name', sa.String(length=100), nullable=True),
        sa.Column('category', postgresql.JSON(), nullable=True),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('like_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('comment_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('share_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('collect_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('platform_data', postgresql.JSON(), nullable=True),
        sa.Column('publish_time', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('crawl_time', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('en_content', sa.String(), nullable=True),
        sa.Column('extdata', postgresql.JSON(), nullable=True),
        sa.Column('status', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 17. 创建白板表 qsa_note_whiteboard
    op.create_table(
        'qsa_note_whiteboard',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False, server_default='未命名白板'),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('snapshot', postgresql.JSON(), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=512), nullable=True),
        sa.Column('background_color', sa.String(length=20), nullable=False, server_default='#ffffff'),
        sa.Column('is_public', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 18. 创建白板笔记关联表 qsa_note_whiteboard_note
    op.create_table(
        'qsa_note_whiteboard_note',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('whiteboard_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('note_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shape_id', sa.String(length=100), nullable=False),
        sa.Column('shape_type', sa.String(length=50), nullable=False, server_default='note-card'),
        sa.Column('position_x', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('position_y', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('width', sa.Numeric(10, 2), nullable=False, server_default='300'),
        sa.Column('height', sa.Numeric(10, 2), nullable=False, server_default='200'),
        sa.Column('rotation', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('z_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_locked', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('note_snapshot', postgresql.JSON(), nullable=True),
        sa.Column('status', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 19. 创建智能体-知识库关联表 qsa_agent_knowledge
    op.create_table(
        'qsa_agent_knowledge',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('knowledge_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 20. 创建智能体-工具关联表 qsa_agent_tools
    op.create_table(
        'qsa_agent_tools',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('tool_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # 按依赖关系倒序删除表
    op.drop_table('qsa_agent_tools')
    op.drop_table('qsa_agent_knowledge')
    op.drop_table('qsa_note_whiteboard_note')
    op.drop_table('qsa_note_whiteboard')
    op.drop_table('qsa_note_collect')
    op.drop_table('qsa_note_mine')
    op.drop_table('qsa_note_tag')
    op.drop_table('qsa_chat_document')
    op.drop_table('qsa_chat_message')
    op.drop_table('qsa_chat_conversation')
    op.drop_table('qsa_sys_tags')
    op.drop_table('qsa_prompts_libs')
    op.drop_table('qsa_tools')
    op.drop_table('qsa_kb_chunk')
    op.drop_table('qsa_kb_document')
    op.drop_table('qsa_kb_knowledge')
    op.drop_table('qsa_agent')
    op.drop_table('qsa_ai_model')
    op.drop_table('qsa_ai_provider')
    op.drop_table('qsa_usr_user')
