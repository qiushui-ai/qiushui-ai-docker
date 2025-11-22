from typing import Any, List, Optional, Union
from datetime import datetime
import uuid as uuid_module

from sqlmodel import Session, select, func

from qiushuiai.schemas.note import (
    NoteTag, 
    NoteTagCreate, 
    NoteTagUpdate, 
    NoteTagPublic,
    NoteTagBatchSortOrderUpdate
)
from qiushuiai.core.exceptions import ResourceNotFoundException, ValidationException


class NoteTagService:
    """笔记标签服务类 - 树形结构管理"""

    def __init__(self, session: Session):
        self.session = session

    def _get_tag_by_id(self, tag_id: int) -> Optional[NoteTag]:
        """根据ID获取标签"""
        statement = select(NoteTag).where(NoteTag.id == tag_id)
        return self.session.exec(statement).first()

    def _get_tag_by_uuid(self, uuid: uuid_module.UUID) -> Optional[NoteTag]:
        """根据UUID获取标签"""
        statement = select(NoteTag).where(NoteTag.uuid == uuid)
        return self.session.exec(statement).first()

    def _get_children_by_parent_id(self, parent_id: Optional[uuid_module.UUID], current_user=None) -> List[NoteTag]:
        """根据父UUID获取所有子标签，按照sort_order正排序，然后按照id正排序"""
        if parent_id is None:
            statement = select(NoteTag).where(NoteTag.parent_id.is_(None))
        else:
            statement = select(NoteTag).where(NoteTag.parent_id == parent_id)

        # 应用租户过滤
        if current_user:
            from qiushuiai.core.db_filters import add_tenant_filter
            statement = add_tenant_filter(statement, NoteTag, current_user.tenant_id)

        statement = statement.order_by(NoteTag.sort_order.asc(), NoteTag.id.asc())
        return self.session.exec(statement).all()

    def _get_all_descendants(self, tag_uuid: uuid_module.UUID, current_user=None) -> List[NoteTag]:
        """递归获取所有后代标签"""
        descendants = []
        children = self._get_children_by_parent_id(tag_uuid, current_user)

        for child in children:
            descendants.append(child)
            descendants.extend(self._get_all_descendants(child.uuid, current_user))

        return descendants

    def _calculate_tag_path(self, parent_id: Optional[uuid_module.UUID]) -> str:
        """根据父标签UUID计算tag_path"""
        if parent_id is None:
            return "/"  # 根标签

        parent = self._get_tag_by_uuid(parent_id)
        if not parent:
            raise ValidationException(message=f"父标签不存在: {parent_id}")

        # 父标签的完整路径 + 父标签名称
        if parent.tag_path == "/":
            return f"/{parent.tag_name}"
        else:
            return f"{parent.tag_path}/{parent.tag_name}"

    def _calculate_level(self, tag_path: str) -> int:
        """根据tag_path计算层级"""
        if tag_path == "/":
            return 1
        # 去掉开头的 /，然后按 / 分割计数
        return len([p for p in tag_path.split("/") if p]) + 1

    def _update_children_path(self, parent_id: uuid_module.UUID, new_parent_path: str, new_parent_name: str):
        """递归更新所有子标签的tag_path和level"""
        children = self._get_children_by_parent_id(parent_id)

        for child in children:
            # 计算新的tag_path
            if new_parent_path == "/":
                new_path = f"/{new_parent_name}"
            else:
                new_path = f"{new_parent_path}/{new_parent_name}"

            # 更新当前子标签的tag_path和level
            child.tag_path = new_path
            child.level = self._calculate_level(new_path)
            self.session.add(child)

            # 递归更新子标签的子标签
            self._update_children_path(child.uuid, new_path, child.tag_name)

    def _resolve_parent_id(self, parent_id: Optional[Union[uuid_module.UUID, str]]) -> Optional[uuid_module.UUID]:
        """将parent_id转换为UUID对象
        
        Args:
            parent_id: 可以是UUID对象或UUID字符串
            
        Returns:
            UUID对象，如果parent_id为None则返回None
            
        Raises:
            ValidationException: 当UUID无效或标签不存在时
        """
        if parent_id is None:
            return None
        
        if isinstance(parent_id, uuid_module.UUID):
            # 验证标签是否存在
            parent_tag = self._get_tag_by_uuid(parent_id)
            if not parent_tag:
                raise ValidationException(message=f"父标签不存在: {parent_id}")
            return parent_id
        
        if isinstance(parent_id, str):
            # 尝试解析为UUID
            try:
                uuid_obj = uuid_module.UUID(parent_id)
                parent_tag = self._get_tag_by_uuid(uuid_obj)
                if parent_tag:
                    return uuid_obj
                else:
                    raise ValidationException(message=f"父标签不存在: {parent_id}")
            except ValueError:
                raise ValidationException(message=f"无效的parent_id格式: {parent_id}")
        
        raise ValidationException(message=f"不支持的parent_id类型: {type(parent_id)}")

    def _validate_parent_tag(self, parent_id: Optional[uuid_module.UUID], current_tag_uuid: Optional[uuid_module.UUID] = None) -> None:
        """验证父标签是否存在，并检查循环引用"""
        if parent_id is None:
            return  # 根标签

        parent = self._get_tag_by_uuid(parent_id)
        if not parent:
            raise ValidationException(message=f"父标签不存在: {parent_id}")

        # 检查循环引用
        if current_tag_uuid:
            # 检查新父标签是否是当前标签的后代
            descendants = self._get_all_descendants(current_tag_uuid)
            descendant_uuids = [d.uuid for d in descendants]
            if parent.uuid in descendant_uuids:
                raise ValidationException(message="不能将标签设置为自己的后代标签")

    def create_tag(self, tag_data: NoteTagCreate, current_user) -> NoteTag:
        """创建新标签"""
        # 转换parent_id
        resolved_parent_id = self._resolve_parent_id(tag_data.parent_id)
        
        # 验证父标签
        self._validate_parent_tag(resolved_parent_id)

        # 计算tag_path
        tag_path = self._calculate_tag_path(resolved_parent_id)

        # 计算level
        level = self._calculate_level(tag_path)

        # 创建标签对象
        tag_dict = tag_data.model_dump()
        tag_dict.update({
            "parent_id": resolved_parent_id,  # 使用转换后的ID
            "tag_path": tag_path,
            "level": level,
        })

        # 使用通用字段更新函数
        from qiushuiai.core.db_filters import update_common_fields

        tag_dict = update_common_fields(tag_dict, current_user, is_create=True)

        tag = NoteTag.model_validate(tag_dict)
        self.session.add(tag)
        self.session.commit()
        self.session.refresh(tag)

        return tag

    def update_tag(self, uuid: uuid_module.UUID, tag_data: NoteTagUpdate, current_user) -> NoteTag:
        """更新标签"""
        tag = self._get_tag_by_uuid(uuid)
        if not tag:
            raise ResourceNotFoundException(message="笔记标签不存在")

        update_dict = tag_data.model_dump(exclude_unset=True)

        # 检查是否需要更新子标签
        need_update_children = False
        old_name = tag.tag_name
        old_parent_id = tag.parent_id

        # 如果修改了父标签
        if "parent_id" in update_dict and update_dict["parent_id"] != tag.parent_id:
            # 转换parent_id
            resolved_parent_id = self._resolve_parent_id(update_dict["parent_id"])
            update_dict["parent_id"] = resolved_parent_id
            
            self._validate_parent_tag(resolved_parent_id, tag.uuid)
            new_tag_path = self._calculate_tag_path(resolved_parent_id)
            new_level = self._calculate_level(new_tag_path)
            update_dict["tag_path"] = new_tag_path
            update_dict["level"] = new_level
            need_update_children = True

        # 如果修改了名称
        if "tag_name" in update_dict and update_dict["tag_name"] != tag.tag_name:
            need_update_children = True

        # 使用通用字段更新函数
        from qiushuiai.core.db_filters import update_common_fields

        update_dict = update_common_fields(update_dict, current_user, is_create=False)

        # 更新标签
        tag.sqlmodel_update(update_dict)
        self.session.add(tag)

        # 如果需要更新子标签
        if need_update_children:
            new_path = tag.tag_path
            new_name = tag.tag_name
            self._update_children_path(tag.uuid, new_path, new_name)

        self.session.commit()
        self.session.refresh(tag)

        return tag

    def delete_tag(self, uuid: uuid_module.UUID) -> None:
        """删除标签及其所有子标签"""
        tag = self._get_tag_by_uuid(uuid)
        if not tag:
            raise ResourceNotFoundException(message="笔记标签不存在")

        # 获取所有后代标签
        descendants = self._get_all_descendants(tag.uuid)

        # 删除所有后代标签
        for descendant in descendants:
            self.session.delete(descendant)

        # 删除当前标签
        self.session.delete(tag)
        self.session.commit()

    def get_tree(self, current_user=None) -> List[dict]:
        """获取树形结构数据"""
        # 获取所有标签，按照sort_order正排序，然后按照id正排序
        statement = select(NoteTag)

        # 应用租户过滤
        if current_user:
            from qiushuiai.core.db_filters import add_tenant_filter
            statement = add_tenant_filter(statement, NoteTag, current_user.tenant_id)

        statement = statement.order_by(NoteTag.sort_order.asc(), NoteTag.id.asc())
        all_tags = self.session.exec(statement).all()

        # 构建UUID到标签的映射
        tag_map = {tag.uuid: tag for tag in all_tags}

        # 构建树形结构
        tree = []
        for tag in all_tags:
            # 如果是根标签（没有父标签）
            if tag.parent_id is None:
                tree.append(self._build_tree_node(tag, tag_map))

        return tree

    def _build_tree_node(self, tag: NoteTag, tag_map: dict) -> dict:
        """构建树节点"""
        node = {
            "id": tag.id,
            "uuid": str(tag.uuid),
            "tag_name": tag.tag_name,
            "tag_path": tag.tag_path,
            "parent_id": str(tag.parent_id) if tag.parent_id else None,
            "level": tag.level,
            "sort_order": tag.sort_order,
            "use_count": tag.use_count,
            "last_used_at": tag.last_used_at,
            "status": tag.status,
            "created_at": tag.created_at,
            "updated_at": tag.updated_at
        }

        # 查找子节点并按照sort_order正排序，然后按照id正排序
        children = []
        for child_tag in tag_map.values():
            if child_tag.parent_id == tag.uuid:
                children.append(self._build_tree_node(child_tag, tag_map))

        # 对子节点进行排序：先按sort_order正排序，再按id排序
        children.sort(key=lambda x: (x["sort_order"], x["id"]))

        if children:
            node["children"] = children

        return node

    def get_tag_by_uuid(self, uuid: uuid_module.UUID) -> NoteTag:
        """根据UUID获取标签详情"""
        tag = self._get_tag_by_uuid(uuid)
        if not tag:
            raise ResourceNotFoundException(message="笔记标签不存在")
        return tag

    def increment_use_count(self, tag_id: int) -> None:
        """增加标签使用次数"""
        tag = self._get_tag_by_id(tag_id)
        if tag:
            tag.use_count += 1
            tag.last_used_at = datetime.now()
            self.session.add(tag)
            self.session.commit()

    def batch_update_sort_order(self, uuids: List[str], current_user) -> dict:
        """批量更新标签的排序顺序
        
        Args:
            uuids: UUID列表，按顺序设置sort_order
            current_user: 当前用户
            
        Returns:
            更新结果字典，包含success和updated_count
            
        Raises:
            ResourceNotFoundException: 当标签不存在时
        """
        try:
            # 使用事务确保原子性
            updated_count = 0
            
            for index, uuid_str in enumerate(uuids):
                # 将字符串转换为UUID对象
                try:
                    uuid_obj = uuid_module.UUID(uuid_str)
                except ValueError:
                    raise ValidationException(message=f"无效的UUID格式: {uuid_str}")
                
                # 获取标签
                tag = self._get_tag_by_uuid(uuid_obj)
                if not tag:
                    raise ResourceNotFoundException(message=f"标签不存在: {uuid_str}")
                
                # 更新排序顺序
                tag.sort_order = index
                self.session.add(tag)
                updated_count += 1
            
            # 提交事务
            self.session.commit()
            
            return {
                "success": True,
                "updated_count": updated_count
            }
            
        except Exception as e:
            # 发生错误时回滚
            self.session.rollback()
            raise
