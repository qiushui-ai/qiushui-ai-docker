from typing import Any, List, Optional
from datetime import datetime
import uuid as uuid_module

from sqlmodel import Session, select, func
from sqlmodel import SQLModel

from qiushuiai.schemas.sys import SysTags, SysTagsCreate, SysTagsUpdate, SysTagsPublic
from qiushuiai.core.exceptions import ResourceNotFoundException, ValidationException


class SysTagsService:
    """系统标签服务类"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def _get_node_by_uuid(self, uuid: uuid_module.UUID) -> Optional[SysTags]:
        """根据UUID获取节点"""
        statement = select(SysTags).where(SysTags.uuid == uuid)
        return self.session.exec(statement).first()
    
    def _get_children_by_puuid(self, puuid: str, current_user=None) -> List[SysTags]:
        """根据父UUID获取所有子节点，按照sortorder正排序，然后按照id正排序"""
        statement = select(SysTags).where(SysTags.puuid == puuid)
        
        # 应用租户过滤
        if current_user:
            from qiushuiai.core.db_filters import add_tenant_filter
            statement = add_tenant_filter(statement, SysTags, current_user.tenant_id)
        
        statement = statement.order_by(SysTags.sortorder.asc(), SysTags.id.asc())
        return self.session.exec(statement).all()
    
    def _get_all_descendants(self, node_uuid: str, current_user=None) -> List[SysTags]:
        """递归获取所有后代节点"""
        descendants = []
        children = self._get_children_by_puuid(node_uuid, current_user)
        
        for child in children:
            descendants.append(child)
            descendants.extend(self._get_all_descendants(str(child.uuid), current_user))
        
        return descendants
    
    def _update_children_pname(self, parent_uuid: str, new_parent_pname: str, new_parent_name: str):
        """递归更新所有子节点的pname"""
        children = self._get_children_by_puuid(parent_uuid)
        
        for child in children:
            # 计算新的pname
            new_pname = f"{new_parent_pname}/{new_parent_name}" if new_parent_pname else new_parent_name
            
            # 更新当前子节点的pname
            child.pname = new_pname
            self.session.add(child)
            
            # 递归更新子节点的子节点
            self._update_children_pname(str(child.uuid), new_pname, child.name)
    
    def _validate_parent_node(self, puuid: Optional[str], current_uuid: Optional[str] = None) -> None:
        """验证父节点是否存在，并检查循环引用"""
        if not puuid:
            return  # 根节点
        
        parent = self._get_node_by_uuid(uuid_module.UUID(puuid))
        if not parent:
            raise ValidationException(message=f"父节点不存在: {puuid}")
        
        # 检查循环引用
        if current_uuid:
            # 检查新父节点是否是当前节点的后代
            descendants = self._get_all_descendants(current_uuid)
            if parent in descendants:
                raise ValidationException(message="不能将节点设置为自己的后代节点")
    
    def _calculate_pname(self, puuid: Optional[str]) -> str:
        """根据父节点UUID计算pname"""
        if not puuid:
            return ""  # 根节点
        
        parent = self._get_node_by_uuid(uuid_module.UUID(puuid))
        if not parent:
            raise ValidationException(message=f"父节点不存在: {puuid}")
        
        # 父节点的完整路径
        parent_full_path = f"{parent.pname}/{parent.name}" if parent.pname else parent.name
        return parent_full_path
    
    def create_tag(self, tag_data: SysTagsCreate, current_user) -> SysTags:
        """创建新标签"""
        # 验证父节点
        self._validate_parent_node(tag_data.puuid)
        
        # 计算pname
        pname = self._calculate_pname(tag_data.puuid)
        
        # 创建标签对象
        tag_dict = tag_data.model_dump()
        tag_dict.update({
            "pname": pname,
        })
        
        # 使用通用字段更新函数
        from qiushuiai.core.db_filters import update_common_fields
        
        tag_dict = update_common_fields(tag_dict, current_user, is_create=True)
        
        tag = SysTags.model_validate(tag_dict)
        self.session.add(tag)
        self.session.commit()
        self.session.refresh(tag)
        
        return tag
    
    def update_tag(self, uuid: uuid_module.UUID, tag_data: SysTagsUpdate, current_user) -> SysTags:
        """更新标签"""
        tag = self._get_node_by_uuid(uuid)
        if not tag:
            raise ResourceNotFoundException(message="系统标签不存在")
        
        update_dict = tag_data.model_dump(exclude_unset=True)
        
        # 检查是否需要更新pname
        need_update_children = False
        old_name = tag.name
        old_puuid = tag.puuid
        
        # 如果修改了父节点
        if "puuid" in update_dict and update_dict["puuid"] != tag.puuid:
            self._validate_parent_node(update_dict["puuid"], str(uuid))
            new_pname = self._calculate_pname(update_dict["puuid"])
            update_dict["pname"] = new_pname
            need_update_children = True
        
        # 如果修改了名称
        if "name" in update_dict and update_dict["name"] != tag.name:
            need_update_children = True
        
        # 使用通用字段更新函数
        from qiushuiai.core.db_filters import update_common_fields
        
        update_dict = update_common_fields(update_dict, current_user, is_create=False)
        
        # 更新标签
        tag.sqlmodel_update(update_dict)
        self.session.add(tag)
        
        # 如果需要更新子节点
        if need_update_children:
            new_pname = tag.pname
            new_name = tag.name
            self._update_children_pname(str(uuid), new_pname, new_name)
        
        self.session.commit()
        self.session.refresh(tag)
        
        return tag
    
    def delete_tag(self, uuid: uuid_module.UUID) -> None:
        """删除标签及其所有子节点"""
        tag = self._get_node_by_uuid(uuid)
        if not tag:
            raise ResourceNotFoundException(message="系统标签不存在")
        
        # 获取所有后代节点
        descendants = self._get_all_descendants(str(uuid))
        
        # 删除所有后代节点
        for descendant in descendants:
            self.session.delete(descendant)
        
        # 删除当前节点
        self.session.delete(tag)
        self.session.commit()
    
    def get_tree_by_flag(self, flag: str, current_user=None) -> List[dict]:
        """根据flag获取树形结构数据"""
        # 获取所有指定flag的标签，按照sortorder正排序，然后按照id正排序
        statement = select(SysTags).where(SysTags.flag == flag)
        
        # 应用租户过滤
        if current_user:
            from qiushuiai.core.db_filters import add_tenant_filter
            statement = add_tenant_filter(statement, SysTags, current_user.tenant_id)
        
        statement = statement.order_by(SysTags.sortorder.asc(), SysTags.id.asc())
        all_tags = self.session.exec(statement).all()
        
        # 构建UUID到标签的映射
        tag_map = {str(tag.uuid): tag for tag in all_tags}
        
        # 构建树形结构
        tree = []
        for tag in all_tags:
            tag_uuid = str(tag.uuid)
            
            # 如果是根节点（没有父节点）
            if not tag.puuid:
                tree.append(self._build_tree_node(tag, tag_map, current_user))
        
        return tree
    
    def _build_tree_node(self, tag: SysTags, tag_map: dict, current_user=None) -> dict:
        """构建树节点"""
        node = {
            "id": str(tag.uuid),
            "name": tag.name,
            "pname": tag.pname,
            "remark": tag.remark,
            "sortorder": tag.sortorder,
            "flag": tag.flag,
            "created_at": tag.created_at,
            "updated_at": tag.updated_at
        }
        
        # 查找子节点并按照sortorder正排序，然后按照id正排序
        children = []
        for child_tag in tag_map.values():
            if child_tag.puuid == str(tag.uuid):
                children.append(self._build_tree_node(child_tag, tag_map, current_user))
        
        # 对子节点进行排序：先按sortorder正排序，再按id字符串排序
        children.sort(key=lambda x: (x["sortorder"], x["id"]))
        
        if children:
            node["children"] = children
        
        return node
    
    def get_tag_by_uuid(self, uuid: uuid_module.UUID) -> SysTags:
        """根据UUID获取标签详情"""
        tag = self._get_node_by_uuid(uuid)
        if not tag:
            raise ResourceNotFoundException(message="系统标签不存在")
        return tag 