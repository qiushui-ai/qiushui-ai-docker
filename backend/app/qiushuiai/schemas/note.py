import uuid as uuid_module
from datetime import datetime
from typing import Optional, Union

from sqlmodel import Field, SQLModel, JSON, Column
from sqlalchemy import TIMESTAMP, Identity, ARRAY, String
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel


# ==================== NoteTag 笔记标签（树形结构） ====================

class NoteTagBase(SQLModel):
    tag_name: str = Field(max_length=50, description="标签名称")
    tag_path: Optional[str] = Field(default=None, max_length=500, description="标签路径")
    parent_id: Optional[uuid_module.UUID] = Field(default=None, description="父标签UUID")
    level: int = Field(default=1, description="层级")
    sort_order: int = Field(default=0, description="排序")
    use_count: int = Field(default=0, description="使用次数")
    last_used_at: Optional[datetime] = Field(default=None, description="最后使用时间")
    ext_data: Optional[dict] = Field(default=None, sa_column=Column(JSONB), description="扩展数据")
    status: int = Field(default=1, description="状态：1启用 0禁用")


class NoteTagCreate(SQLModel):
    tag_name: str = Field(max_length=50, description="标签名称")
    parent_id: Optional[Union[uuid_module.UUID, str]] = Field(default=None, description="父标签UUID（支持UUID对象或UUID字符串）")
    sort_order: int = Field(default=0, description="排序")
    ext_data: Optional[dict] = Field(default=None, description="扩展数据")
    status: int = Field(default=1, description="状态：1启用 0禁用")


class NoteTagUpdate(SQLModel):
    tag_name: str | None = Field(default=None, max_length=50, description="标签名称")
    parent_id: Union[uuid_module.UUID, str] | None = Field(default=None, description="父标签UUID（支持UUID对象或UUID字符串）")
    sort_order: int | None = Field(default=None, description="排序")
    ext_data: dict | None = Field(default=None, description="扩展数据")
    status: int | None = Field(default=None, description="状态：1启用 0禁用")


class NoteTagBatchSortOrderUpdate(SQLModel):
    """批量更新标签排序顺序"""
    uuids: list[str] = Field(description="标签UUID列表，按顺序设置sort_order")


class NoteTag(NoteTagBase, table=True):
    __tablename__ = "qsa_note_tag"

    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()})
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="标签UUID")
    tenant_id: int = Field(description="所属租户ID")
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int = Field(description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int = Field(description="最后修改者")


class NoteTagPublic(NoteTagBase):
    id: int
    uuid: uuid_module.UUID
    tenant_id: int
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    full_name: Optional[str] = Field(default=None, description="完整路径名称（tag_path/tag_name）")


class NoteTagSimple(SQLModel):
    """简化的标签响应，只包含 uuid 和 full_name"""
    uuid: uuid_module.UUID
    full_name: str


# ==================== NoteMine 我的笔记 ====================

class NoteMineBase(SQLModel):
    title: str = Field(max_length=500, description="标题")
    content: Optional[str] = Field(default=None, description="内容")
    attachments: Optional[dict] = Field(default=None, sa_column=Column(JSONB), description="附件")
    tags: Optional[dict] = Field(default=None, sa_column=Column(JSONB), description="标签")
    category: Optional[dict] = Field(default=None, sa_column=Column(JSONB), description="分类")
    collect_id: Optional[int] = Field(default=None, description="关联的收藏ID")
    ext_data: Optional[dict] = Field(default=None, sa_column=Column(JSONB), description="扩展数据")
    status: int = Field(default=1, description="状态：1正常 0删除")


class NoteMineCreate(SQLModel):
    title: str = Field(max_length=500, description="标题")
    content: Optional[str] = Field(default=None, description="内容")
    attachments: Optional[dict] = Field(default=None, description="附件")
    tags: Optional[dict] = Field(default=None, description="标签")
    category: Optional[dict] = Field(default=None, description="分类")
    collect_id: Optional[int] = Field(default=None, description="关联的收藏ID")
    ext_data: Optional[dict] = Field(default=None, description="扩展数据")
    status: int = Field(default=1, description="状态：1正常 0删除")


class NoteMineUpdate(SQLModel):
    title: str | None = Field(default=None, max_length=500, description="标题")
    content: str | None = Field(default=None, description="内容")
    attachments: dict | None = Field(default=None, description="附件")
    tags: dict | None = Field(default=None, description="标签")
    category: dict | None = Field(default=None, description="分类")
    collect_id: int | None = Field(default=None, description="关联的收藏ID")
    ext_data: dict | None = Field(default=None, description="扩展数据")
    status: int | None = Field(default=None, description="状态：1正常 0删除")


class NoteMine(NoteMineBase, table=True):
    __tablename__ = "qsa_note_mine"

    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()})
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="笔记UUID")
    tenant_id: int = Field(description="所属租户ID")
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int = Field(description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int = Field(description="最后修改者")


class NoteMinePublic(NoteMineBase):
    id: int
    uuid: uuid_module.UUID
    tenant_id: int
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int


class TagInfo(SQLModel):
    """标签详细信息"""
    id: int = Field(description="标签ID")
    tag_name: str = Field(description="标签名称")
    tag_path: str = Field(description="标签路径")
    full_path: str = Field(description="完整路径")
    parent_id: Optional[uuid_module.UUID] = Field(default=None, description="父标签UUID")
    is_new: bool = Field(default=False, description="是否是本次保存新创建的标签")


class NoteMineWithTags(NoteMinePublic):
    """包含标签详情的笔记响应"""
    tag_details: Optional[list[TagInfo]] = Field(default=None, description="标签详细信息列表")


# ==================== NoteCollect 收藏笔记 ====================

class NoteCollectBase(SQLModel):
    content_id: str = Field(max_length=100, description="内容ID（唯一）")
    platform: str = Field(max_length=20, description="平台")
    content_type: str = Field(max_length=20, description="内容类型")
    title: Optional[str] = Field(default=None, max_length=500, description="标题")
    description: Optional[str] = Field(default=None, description="描述")
    cover_url: Optional[str] = Field(default=None, max_length=500, description="封面URL")
    media_urls: Optional[dict] = Field(default=None, sa_column=Column(JSONB), description="媒体URL列表")
    source_url: Optional[str] = Field(default=None, max_length=500, description="原文URL")
    author_id: Optional[str] = Field(default=None, max_length=100, description="作者ID")
    author_name: Optional[str] = Field(default=None, max_length=100, description="作者名称")
    category: Optional[dict] = Field(default=None, sa_column=Column(JSONB), description="分类")
    tags: Optional[list[str]] = Field(default=None, sa_column=Column(JSONB), description="标签列表")
    view_count: Optional[int] = Field(default=0, description="浏览数")
    like_count: Optional[int] = Field(default=0, description="点赞数")
    comment_count: Optional[int] = Field(default=0, description="评论数")
    share_count: Optional[int] = Field(default=0, description="分享数")
    collect_count: Optional[int] = Field(default=0, description="收藏数")
    word_count: Optional[int] = Field(default=None, description="字数")
    platform_data: Optional[dict] = Field(default=None, sa_column=Column(JSONB), description="平台特定数据")
    publish_time: Optional[datetime] = Field(default=None, description="发布时间")
    crawl_time: Optional[datetime] = Field(default=None, description="爬取时间")
    status: Optional[str] = Field(default=None, max_length=255, description="状态")


class NoteCollectCreate(SQLModel):
    content_id: str = Field(max_length=100, description="内容ID（唯一）")
    platform: str = Field(max_length=20, description="平台")
    content_type: str = Field(max_length=20, description="内容类型")
    title: Optional[str] = Field(default=None, max_length=500, description="标题")
    description: Optional[str] = Field(default=None, description="描述")
    cover_url: Optional[str] = Field(default=None, max_length=500, description="封面URL")
    media_urls: Optional[dict] = Field(default=None, description="媒体URL列表")
    source_url: Optional[str] = Field(default=None, max_length=500, description="原文URL")
    author_id: Optional[str] = Field(default=None, max_length=100, description="作者ID")
    author_name: Optional[str] = Field(default=None, max_length=100, description="作者名称")
    category: Optional[dict] = Field(default=None, description="分类")
    tags: Optional[list[str]] = Field(default=None, description="标签列表")
    view_count: Optional[int] = Field(default=0, description="浏览数")
    like_count: Optional[int] = Field(default=0, description="点赞数")
    comment_count: Optional[int] = Field(default=0, description="评论数")
    share_count: Optional[int] = Field(default=0, description="分享数")
    collect_count: Optional[int] = Field(default=0, description="收藏数")
    word_count: Optional[int] = Field(default=None, description="字数")
    platform_data: Optional[dict] = Field(default=None, description="平台特定数据")
    publish_time: Optional[datetime] = Field(default=None, description="发布时间")
    crawl_time: Optional[datetime] = Field(default=None, description="爬取时间")
    status: Optional[str] = Field(default=None, max_length=255, description="状态")


class NoteCollectUpdate(SQLModel):
    content_id: str | None = Field(default=None, max_length=100, description="内容ID（唯一）")
    platform: str | None = Field(default=None, max_length=20, description="平台")
    content_type: str | None = Field(default=None, max_length=20, description="内容类型")
    title: str | None = Field(default=None, max_length=500, description="标题")
    description: str | None = Field(default=None, description="描述")
    cover_url: str | None = Field(default=None, max_length=500, description="封面URL")
    media_urls: dict | None = Field(default=None, description="媒体URL列表")
    source_url: str | None = Field(default=None, max_length=500, description="原文URL")
    author_id: str | None = Field(default=None, max_length=100, description="作者ID")
    author_name: str | None = Field(default=None, max_length=100, description="作者名称")
    category: dict | None = Field(default=None, description="分类")
    tags: list[str] | None = Field(default=None, description="标签列表")
    view_count: int | None = Field(default=None, description="浏览数")
    like_count: int | None = Field(default=None, description="点赞数")
    comment_count: int | None = Field(default=None, description="评论数")
    share_count: int | None = Field(default=None, description="分享数")
    collect_count: int | None = Field(default=None, description="收藏数")
    duration: int | None = Field(default=None, description="时长（秒）")
    word_count: int | None = Field(default=None, description="字数")
    platform_data: dict | None = Field(default=None, description="平台特定数据")
    publish_time: datetime | None = Field(default=None, description="发布时间")
    crawl_time: datetime | None = Field(default=None, description="爬取时间")
    status: str | None = Field(default=None, max_length=255, description="状态")


class NoteCollect(NoteCollectBase, table=True):
    __tablename__ = "qsa_note_collect"

    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()})
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="收藏UUID")
    tenant_id: int = Field(description="所属租户ID")
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int = Field(description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int = Field(description="最后修改者")


class NoteCollectPublic(NoteCollectBase):
    id: int
    uuid: uuid_module.UUID
    tenant_id: int
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int


# ==================== API接口用的组合模型 ====================

class NoteCollectWithContent(NoteCollectBase):
    """API接口返回的完整数据模型，包含主表和内容表的数据"""
    id: int
    uuid: uuid_module.UUID
    tenant_id: int
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    # 来自内容表的字段
    cn_content: Optional[str] = Field(default=None, description="中文内容")
    en_content: Optional[str] = Field(default=None, description="英文内容")
    extdata: Optional[dict] = Field(default=None, description="扩展数据")


class NoteCollectCreateWithContent(SQLModel):
    """API接口创建时的输入模型，包含主表和内容表的数据"""
    content_id: str = Field(max_length=100, description="内容ID（唯一）")
    platform: str = Field(max_length=20, description="平台")
    content_type: str = Field(max_length=20, description="内容类型")
    title: Optional[str] = Field(default=None, max_length=500, description="标题")
    description: Optional[str] = Field(default=None, description="描述")
    cover_url: Optional[str] = Field(default=None, max_length=500, description="封面URL")
    media_urls: Optional[dict] = Field(default=None, description="媒体URL列表")
    source_url: Optional[str] = Field(default=None, max_length=500, description="原文URL")
    author_id: Optional[str] = Field(default=None, max_length=100, description="作者ID")
    author_name: Optional[str] = Field(default=None, max_length=100, description="作者名称")
    category: Optional[dict] = Field(default=None, description="分类")
    tags: Optional[list[str]] = Field(default=None, description="标签列表")
    view_count: Optional[int] = Field(default=0, description="浏览数")
    like_count: Optional[int] = Field(default=0, description="点赞数")
    comment_count: Optional[int] = Field(default=0, description="评论数")
    share_count: Optional[int] = Field(default=0, description="分享数")
    collect_count: Optional[int] = Field(default=0, description="收藏数")
    word_count: Optional[int] = Field(default=None, description="字数")
    platform_data: Optional[dict] = Field(default=None, description="平台特定数据")
    publish_time: Optional[datetime] = Field(default=None, description="发布时间")
    crawl_time: Optional[datetime] = Field(default=None, description="爬取时间")
    status: Optional[str] = Field(default=None, max_length=255, description="状态")
    # 内容表字段
    cn_content: Optional[str] = Field(default=None, description="中文内容")
    en_content: Optional[str] = Field(default=None, description="英文内容")
    extdata: Optional[dict] = Field(default=None, description="扩展数据")


class NoteCollectUpdateWithContent(SQLModel):
    """API接口更新时的输入模型，包含主表和内容表的数据"""
    content_id: str | None = Field(default=None, max_length=100, description="内容ID（唯一）")
    platform: str | None = Field(default=None, max_length=20, description="平台")
    content_type: str | None = Field(default=None, max_length=20, description="内容类型")
    title: str | None = Field(default=None, max_length=500, description="标题")
    description: str | None = Field(default=None, description="描述")
    cover_url: str | None = Field(default=None, max_length=500, description="封面URL")
    media_urls: dict | None = Field(default=None, description="媒体URL列表")
    source_url: str | None = Field(default=None, max_length=500, description="原文URL")
    author_id: str | None = Field(default=None, max_length=100, description="作者ID")
    author_name: str | None = Field(default=None, max_length=100, description="作者名称")
    category: dict | None = Field(default=None, description="分类")
    tags: list[str] | None = Field(default=None, description="标签列表")
    view_count: int | None = Field(default=None, description="浏览数")
    like_count: int | None = Field(default=None, description="点赞数")
    comment_count: int | None = Field(default=None, description="评论数")
    share_count: int | None = Field(default=None, description="分享数")
    collect_count: int | None = Field(default=None, description="收藏数")
    duration: int | None = Field(default=None, description="时长（秒）")
    word_count: int | None = Field(default=None, description="字数")
    platform_data: dict | None = Field(default=None, description="平台特定数据")
    publish_time: datetime | None = Field(default=None, description="发布时间")
    crawl_time: datetime | None = Field(default=None, description="爬取时间")
    status: str | None = Field(default=None, max_length=255, description="状态")
    # 内容表字段
    cn_content: str | None = Field(default=None, description="中文内容")
    en_content: str | None = Field(default=None, description="英文内容")
    extdata: dict | None = Field(default=None, description="扩展数据")


# ==================== NoteCollectContent 收藏笔记内容 ====================

class NoteCollectContentBase(SQLModel):
    cn_content: Optional[str] = Field(default=None, description="中文内容")
    en_content: Optional[str] = Field(default=None, description="英文内容")
    extdata: Optional[dict] = Field(default=None, sa_column=Column(JSONB), description="扩展数据")


class NoteCollectContentCreate(SQLModel):
    cn_content: Optional[str] = Field(default=None, description="中文内容")
    en_content: Optional[str] = Field(default=None, description="英文内容")
    extdata: Optional[dict] = Field(default=None, description="扩展数据")


class NoteCollectContentUpdate(SQLModel):
    cn_content: str | None = Field(default=None, description="中文内容")
    en_content: str | None = Field(default=None, description="英文内容")
    extdata: dict | None = Field(default=None, description="扩展数据")


class NoteCollectContent(NoteCollectContentBase, table=True):
    __tablename__ = "qsa_note_collect_content"

    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()})
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="内容UUID")
    collect_uuid: uuid_module.UUID = Field(description="关联的收藏UUID")
    tenant_id: int = Field(description="所属租户ID")
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int = Field(description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int = Field(description="最后修改者")


class NoteCollectContentPublic(NoteCollectContentBase):
    id: int
    uuid: uuid_module.UUID
    collect_uuid: uuid_module.UUID
    tenant_id: int
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int


# ==================== NoteCollectCreater 收藏创作者 ====================

class NoteCollectCreaterBase(SQLModel):
    blogger_name: str = Field(max_length=100, description="博主名称")
    username: str = Field(max_length=100, description="用户名")
    website_url: Optional[str] = Field(default=None, max_length=500, description="网址")
    platform: str = Field(max_length=20, description="所在平台")
    is_collecting: bool = Field(default=False, description="是否采集")
    ext_data: Optional[dict] = Field(default=None, sa_column=Column(JSONB), description="扩展数据")
    status: Optional[str] = Field(default=None, max_length=255, description="状态")


class NoteCollectCreaterCreate(SQLModel):
    blogger_name: str = Field(max_length=100, description="博主名称")
    username: str = Field(max_length=100, description="用户名")
    website_url: Optional[str] = Field(default=None, max_length=500, description="网址")
    platform: str = Field(max_length=20, description="所在平台")
    is_collecting: bool = Field(default=False, description="是否采集")
    ext_data: Optional[dict] = Field(default=None, description="扩展数据")
    status: Optional[str] = Field(default=None, max_length=255, description="状态")


class NoteCollectCreaterUpdate(SQLModel):
    blogger_name: str | None = Field(default=None, max_length=100, description="博主名称")
    username: str | None = Field(default=None, max_length=100, description="用户名")
    website_url: str | None = Field(default=None, max_length=500, description="网址")
    platform: str | None = Field(default=None, max_length=20, description="所在平台")
    is_collecting: bool | None = Field(default=None, description="是否采集")
    ext_data: dict | None = Field(default=None, description="扩展数据")
    status: str | None = Field(default=None, max_length=255, description="状态")


class NoteCollectCreater(NoteCollectCreaterBase, table=True):
    __tablename__ = "qsa_note_collect_creater"

    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()})
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="创作者UUID")
    tenant_id: int = Field(description="所属租户ID")
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int = Field(description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int = Field(description="最后修改者")


class NoteCollectCreaterPublic(NoteCollectCreaterBase):
    id: int
    uuid: uuid_module.UUID
    tenant_id: int
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
