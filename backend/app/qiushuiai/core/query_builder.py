"""
统一查询条件构建器

支持动态查询条件构建，包括：
- eq_field: 等于查询
- like_field: 模糊查询
- in_field: 包含查询
- gte_field: 大于等于
- lte_field: 小于等于
- range_field: 范围查询
- null_field: 空值查询
"""

import uuid
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
from enum import Enum

from sqlmodel import SQLModel, select, and_, or_, func, desc, asc
from pydantic import BaseModel, Field


class QueryOperator(str, Enum):
    """查询操作符"""
    EQ = "eq"           # 等于
    LIKE = "like"       # 模糊查询
    IN = "in"           # 包含
    NOT_IN = "not_in"   # 不包含
    GTE = "gte"         # 大于等于
    LTE = "lte"         # 小于等于
    GT = "gt"           # 大于
    LT = "lt"           # 小于
    NULL = "null"       # 空值
    NOT_NULL = "not_null"  # 非空值
    BETWEEN = "between"    # 范围查询


class QueryCondition(BaseModel):
    """查询条件"""
    field: str
    operator: QueryOperator
    value: Any
    case_sensitive: bool = True


class BaseQueryParams(BaseModel):
    """基础查询参数"""
    
    def to_conditions(self) -> List[QueryCondition]:
        """转换为查询条件列表"""
        conditions = []
        
        # 遍历所有字段
        for field_name, field_value in self.model_dump(exclude_unset=True).items():
            if field_value is None:
                continue
                
            # 解析字段名和操作符
            if '_' in field_name:
                parts = field_name.split('_', 1)
                operator_str = parts[0]
                field_name = parts[1]
                
                # 映射操作符
                operator_map = {
                    'eq': QueryOperator.EQ,
                    'like': QueryOperator.LIKE,
                    'in': QueryOperator.IN,
                    'not': QueryOperator.NOT_IN,
                    'gte': QueryOperator.GTE,
                    'lte': QueryOperator.LTE,
                    'gt': QueryOperator.GT,
                    'lt': QueryOperator.LT,
                    'null': QueryOperator.NULL,
                    'notnull': QueryOperator.NOT_NULL,
                    'between': QueryOperator.BETWEEN
                }
                
                operator = operator_map.get(operator_str, QueryOperator.EQ)
            else:
                # 默认为等于查询
                operator = QueryOperator.EQ
            
            conditions.append(QueryCondition(
                field=field_name,
                operator=operator,
                value=field_value
            ))
        
        return conditions


class QueryBuilder:
    """查询构建器"""
    
    def __init__(self, model: SQLModel):
        self.model = model
        self.query = select(model)
        self.conditions = []
    
    def add_condition(self, condition: QueryCondition):
        """添加查询条件"""
        self.conditions.append(condition)
        return self
    
    def add_conditions(self, conditions: List[QueryCondition]):
        """批量添加查询条件"""
        self.conditions.extend(conditions)
        return self
    
    def build(self):
        """构建查询"""
        if not self.conditions:
            return self.query
            
        where_clauses = []
        
        for condition in self.conditions:
            clause = self._build_condition_clause(condition)
            if clause is not None:
                where_clauses.append(clause)
        
        if where_clauses:
            self.query = self.query.where(and_(*where_clauses))
            
        return self.query
    
    def _build_condition_clause(self, condition: QueryCondition):
        """构建单个条件子句"""
        if not hasattr(self.model, condition.field):
            return None
            
        field = getattr(self.model, condition.field)
        value = condition.value
        
        if condition.operator == QueryOperator.EQ:
            return field == value
            
        elif condition.operator == QueryOperator.LIKE:
            if not condition.case_sensitive:
                return func.lower(field).contains(func.lower(str(value)))
            return field.contains(str(value))
            
        elif condition.operator == QueryOperator.IN:
            if isinstance(value, (list, tuple)):
                return field.in_(value)
            return field == value
            
        elif condition.operator == QueryOperator.NOT_IN:
            if isinstance(value, (list, tuple)):
                return ~field.in_(value)
            return field != value
            
        elif condition.operator == QueryOperator.GTE:
            return field >= value
            
        elif condition.operator == QueryOperator.LTE:
            return field <= value
            
        elif condition.operator == QueryOperator.GT:
            return field > value
            
        elif condition.operator == QueryOperator.LT:
            return field < value
            
        elif condition.operator == QueryOperator.NULL:
            return field.is_(None)
            
        elif condition.operator == QueryOperator.NOT_NULL:
            return field.is_not(None)
            
        elif condition.operator == QueryOperator.BETWEEN:
            if isinstance(value, (list, tuple)) and len(value) == 2:
                return field.between(value[0], value[1])
            return None
            
        return None
    
    def add_tenant_filter(self, tenant_id: Optional[uuid.UUID]):
        """添加租户过滤"""
        if tenant_id and hasattr(self.model, 'tenant_id'):
            self.query = self.query.where(self.model.tenant_id == tenant_id)
        return self
    
    def add_soft_delete_filter(self):
        """添加软删除过滤"""
        if hasattr(self.model, 'is_deleted'):
            self.query = self.query.where(self.model.is_deleted == False)
        return self
    
    def add_active_filter(self):
        """添加激活状态过滤"""
        if hasattr(self.model, 'is_active'):
            self.query = self.query.where(self.model.is_active == True)
        return self
    
    def add_user_scope_filter(self, user_id: Optional[uuid.UUID], check_owner: bool = True):
        """添加用户权限范围过滤"""
        if user_id and check_owner and hasattr(self.model, 'created_by'):
            self.query = self.query.where(self.model.created_by == user_id)
        return self
    
    def add_order_by(self, order_by: Optional[str] = None, order_desc: bool = False):
        """添加排序"""
        if order_by and hasattr(self.model, order_by):
            order_field = getattr(self.model, order_by)
            if order_desc:
                self.query = self.query.order_by(desc(order_field))
            else:
                self.query = self.query.order_by(asc(order_field))
        elif hasattr(self.model, 'created_at'):
            # 默认按创建时间倒序
            self.query = self.query.order_by(desc(self.model.created_at))
        return self


# 使用示例
"""
# 1. 定义查询参数模型
class KnowledgeBaseQueryParams(BaseQueryParams):
    eq_name: Optional[str] = Field(None, description="知识库名称（精确匹配）")
    like_name: Optional[str] = Field(None, description="知识库名称（模糊匹配）")
    eq_status: Optional[str] = Field(None, description="状态")
    in_type: Optional[List[str]] = Field(None, description="类型列表")
    gte_created_at: Optional[datetime] = Field(None, description="创建时间起始")
    lte_created_at: Optional[datetime] = Field(None, description="创建时间结束")

# 2. 在服务中使用
def search_knowledge_bases(
    self,
    query_params: KnowledgeBaseQueryParams,
    tenant_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None
):
    builder = QueryBuilder(KnowledgeBase)
    
    # 添加基础过滤
    builder.add_tenant_filter(tenant_id)
    builder.add_soft_delete_filter()
    builder.add_active_filter()
    builder.add_user_scope_filter(user_id)
    
    # 添加查询条件
    conditions = query_params.to_conditions()
    builder.add_conditions(conditions)
    
    # 构建查询
    query = builder.build()
    
    return self.session.exec(query).all()

# 3. API调用示例
{
    "eq_name": "我的知识库",
    "like_description": "AI",
    "in_status": ["active", "pending"],
    "gte_created_at": "2024-01-01T00:00:00"
}
""" 