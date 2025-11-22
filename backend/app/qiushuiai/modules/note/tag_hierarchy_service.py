"""
标签层级管理服务

处理标签的层级关系，如 aaa/bbb/ccc 格式的标签
"""
import uuid as uuid_module
from typing import List, Optional, Tuple
from sqlmodel import Session, select
from qiushuiai.schemas.note import NoteTag


class TagHierarchyService:
    """标签层级服务"""

    @staticmethod
    def parse_tag_path(tag_full: str) -> Tuple[str, str]:
        """
        解析标签的完整路径为 tag_path 和 tag_name

        规则:
        - tag_full = "aaa/bbb/ccc"
        - tag_path = "/aaa/bbb"  (去掉最后一级，前面加 /)
        - tag_name = "ccc"

        特殊情况:
        - tag_full = "aaa" -> tag_path = "", tag_name = "aaa"

        Args:
            tag_full: 完整标签路径，如 "aaa/bbb/ccc" 或 "aaa"

        Returns:
            (tag_path, tag_name) 元组

        示例:
            >>> parse_tag_path("Python/机器学习/深度学习")
            ("/Python/机器学习", "深度学习")

            >>> parse_tag_path("Python")
            ("", "Python")
        """
        parts = tag_full.split("/")

        if len(parts) == 1:
            # 没有父级路径
            return "", parts[0]
        else:
            # 有父级路径
            tag_name = parts[-1]
            tag_path = "/" + "/".join(parts[:-1])
            return tag_path, tag_name

    @staticmethod
    def ensure_tag_exists(
        db: Session,
        tag_full: str,
        tenant_id: int,
        user_id: int,
    ) -> tuple[NoteTag, bool]:
        """
        确保标签存在，如果不存在则创建（包括父级标签）

        逻辑:
        1. 解析 tag_full 为 tag_path 和 tag_name
        2. 检查 qsa_note_tag 表中是否存在该标签
        3. 如果不存在，先递归创建父级标签，然后创建当前标签

        Args:
            db: 数据库会话
            tag_full: 完整标签路径，如 "aaa/bbb/ccc"
            tenant_id: 租户ID
            user_id: 用户ID

        Returns:
            (标签记录, 是否新创建)
            - NoteTag: 创建或找到的标签记录
            - bool: True 表示新创建，False 表示已存在

        示例:
            标签 "Python/机器学习/深度学习":
            1. 先创建 "Python" (tag_path="", tag_name="Python", parent_id=None)
            2. 再创建 "Python/机器学习" (tag_path="/Python", tag_name="机器学习", parent_id=Python.id)
            3. 最后创建 "Python/机器学习/深度学习" (tag_path="/Python/机器学习", tag_name="深度学习", parent_id=机器学习.id)
        """
        tag_path, tag_name = TagHierarchyService.parse_tag_path(tag_full)

        # 1. 检查标签是否已存在
        existing_tag = db.exec(
            select(NoteTag).where(
                NoteTag.tag_path == tag_path,
                NoteTag.tag_name == tag_name,
                NoteTag.tenant_id == tenant_id,
            )
        ).first()

        if existing_tag:
            return existing_tag, False  # 已存在，不是新创建

        # 2. 标签不存在，需要创建
        parent_id: Optional[uuid_module.UUID] = None

        # 3. 如果有父级路径，先确保父级标签存在
        if tag_path:
            # 构建父级的完整路径
            # tag_path = "/aaa/bbb" -> parent_full = "aaa/bbb"
            parent_full = tag_path.lstrip("/")
            parent_tag, _ = TagHierarchyService.ensure_tag_exists(
                db, parent_full, tenant_id, user_id
            )
            parent_id = parent_tag.uuid

        # 4. 创建当前标签
        new_tag = NoteTag(
            tag_name=tag_name,
            tag_path=tag_path,
            parent_id=parent_id,
            tenant_id=tenant_id,
            created_by=user_id,
            updated_by=user_id,
            status=1,
            sort_order=0,
        )

        db.add(new_tag)
        db.commit()
        db.refresh(new_tag)

        return new_tag, True  # 新创建

    @staticmethod
    def ensure_tags_batch(
        db: Session,
        tag_list: List[str],
        tenant_id: int,
        user_id: int,
    ) -> dict[str, bool]:
        """
        批量确保标签存在

        Args:
            db: 数据库会话
            tag_list: 标签列表，如 ["Python", "AI/机器学习", "编程/Python/Django"]
            tenant_id: 租户ID
            user_id: 用户ID

        Returns:
            字典，key 为标签完整路径，value 为是否新创建
            {"Python": False, "AI/机器学习": True, "编程/Python/Django": True}

        示例:
            >>> result = ensure_tags_batch(db, ["Python", "AI/机器学习"], tenant_id=3, user_id=1)
            >>> result
            {"Python": False, "AI/机器学习": True}  # Python 已存在，AI/机器学习 是新创建的
        """
        creation_status = {}

        for tag_full in tag_list:
            tag_record, is_new = TagHierarchyService.ensure_tag_exists(
                db, tag_full, tenant_id, user_id
            )
            creation_status[tag_full] = is_new

        return creation_status

    @staticmethod
    def get_tags_info_by_names(
        db: Session,
        tag_names: List[str],
        tenant_id: int,
    ) -> List[dict]:
        """
        根据标签名称列表获取标签的完整信息

        Args:
            db: 数据库会话
            tag_names: 标签名称列表（完整路径），如 ["Python", "AI/机器学习/深度学习"]
            tenant_id: 租户ID

        Returns:
            标签信息字典列表，每个字典包含:
            {
                "id": 标签ID,
                "tag_name": 标签名称,
                "tag_path": 标签路径,
                "full_path": 完整路径（用于前端显示）
            }

        示例:
            >>> get_tags_info_by_names(db, ["Python", "AI/机器学习"], tenant_id=3)
            [
                {"id": 1, "tag_name": "Python", "tag_path": "", "full_path": "Python"},
                {"id": 2, "tag_name": "机器学习", "tag_path": "/AI", "full_path": "AI/机器学习"}
            ]
        """
        tags_info = []

        for tag_full in tag_names:
            tag_path, tag_name = TagHierarchyService.parse_tag_path(tag_full)

            # 查询标签
            tag = db.exec(
                select(NoteTag).where(
                    NoteTag.tag_path == tag_path,
                    NoteTag.tag_name == tag_name,
                    NoteTag.tenant_id == tenant_id,
                )
            ).first()

            if tag:
                tags_info.append({
                    "id": tag.id,
                    "tag_name": tag.tag_name,
                    "tag_path": tag.tag_path,
                    "full_path": tag_full,
                    "parent_id": tag.parent_id,
                })

        return tags_info

    @staticmethod
    def get_tag_full_path(db: Session, tag: NoteTag) -> str:
        """
        获取标签的完整路径

        Args:
            db: 数据库会话
            tag: 标签记录

        Returns:
            完整路径，如 "Python/机器学习/深度学习"

        示例:
            tag.tag_path = "/Python/机器学习"
            tag.tag_name = "深度学习"
            返回: "Python/机器学习/深度学习"
        """
        if tag.tag_path:
            # 去掉前导的 /
            return f"{tag.tag_path.lstrip('/')}/{tag.tag_name}"
        else:
            return tag.tag_name
