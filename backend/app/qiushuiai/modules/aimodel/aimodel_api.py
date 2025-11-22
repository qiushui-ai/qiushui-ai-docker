from typing import Any, Annotated
from datetime import datetime
import uuid as uuid_module

from fastapi import APIRouter, Body
from sqlmodel import select, join

from qiushuiai.core.config import settings
from qiushuiai.modules.user.deps import CurrentUser, SessionDep
from qiushuiai.core.db_filters import (
    apply_common_filters,
    apply_pagination,
    build_order_by,
    get_count_query,
    update_common_fields,
    apply_keyword_search
)
from qiushuiai.core.response import (
    BaseResponse,
    success_response,
    page_response,
    PageResponse,
    ResponseCode,
    ResponseMessage,
)
from qiushuiai.core.exceptions import ResourceNotFoundException
from qiushuiai.schemas.aimodel import (
    AIModel,
    AIModelCreate,
    AIModelPublic,
    AIModelUpdate,
    AIModelDetailResponse,
    AIProvider,
    AIProviderCreate,
    AIProviderPublic,
    AIProviderUpdate,
)

router = APIRouter(prefix="/aimodel", tags=["aimodel"])

# ==================== AI厂商相关API ====================

@router.post("/provider/page", response_model=BaseResponse[PageResponse[AIProviderPublic]])
def page_providers(
    session: SessionDep,
    current_user: CurrentUser,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取AI厂商列表。"""
    page = request_data.get("page", 1)
    rows = request_data.get("rows", 20)
    keyword = request_data.get("keyword")
    
    statement = select(AIProvider)
    
    # 应用关键词搜索
    statement = apply_keyword_search(
        statement=statement,
        model=AIProvider,
        keyword=keyword,
        search_fields=["name", "display_name", "description"]
    )
    
    count_statement = get_count_query(statement, AIProvider)
    count = session.exec(count_statement).one()

    statement = build_order_by(
        statement=statement,
        model=AIProvider,
        order_by="id",
        order_direction="desc"
    )

    statement, _, _ = apply_pagination(
        statement=statement,
        page=page,
        page_size=rows
    )

    providers = session.exec(statement).all()
    return page_response(
        items=providers,
        page=page,
        rows=rows,
        total=count,
        message="获取AI厂商列表成功"
    )

@router.post("/provider/detail/{uuid}", response_model=BaseResponse[AIProviderPublic])
def read_provider(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单个AI厂商。"""
    statement = select(AIProvider).where(AIProvider.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=AIProvider,
        current_user=current_user
    )
    provider = session.exec(statement).first()
    if not provider:
        raise ResourceNotFoundException(message="AI厂商不存在")
    return success_response(data=provider, message="获取AI厂商详情成功")

@router.post("/provider/create", response_model=BaseResponse[AIProviderPublic])
def create_provider(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    provider_in: AIProviderCreate
) -> Any:
    """创建新AI厂商。"""
    provider_data = provider_in.model_dump()
    provider_data = update_common_fields(
        data=provider_data,
        current_user=current_user,
        is_create=True
    )
    provider = AIProvider.model_validate(provider_data)
    session.add(provider)
    session.commit()
    session.refresh(provider)
    return success_response(
        data=provider,
        message=ResponseMessage.CREATED,
        code=ResponseCode.CREATED
    )

@router.post("/provider/update/{uuid}", response_model=BaseResponse[AIProviderPublic])
def update_provider(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    provider_in: AIProviderUpdate,
) -> Any:
    """更新AI厂商信息。"""
    statement = select(AIProvider).where(AIProvider.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=AIProvider,
        current_user=current_user
    )
    provider = session.exec(statement).first()
    if not provider:
        raise ResourceNotFoundException(message="AI厂商不存在")
    
    update_dict = provider_in.model_dump(exclude_unset=True)
    update_dict = update_common_fields(
        data=update_dict,
        current_user=current_user,
        is_create=False
    )
    provider.sqlmodel_update(update_dict)
    session.add(provider)
    session.commit()
    session.refresh(provider)
    return success_response(data=provider, message=ResponseMessage.UPDATED)

@router.post("/provider/delete/{uuid}", response_model=BaseResponse[None])
def delete_provider(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """删除AI厂商（直接删除）。"""
    statement = select(AIProvider).where(AIProvider.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=AIProvider,
        current_user=current_user
    )
    provider = session.exec(statement).first()
    if not provider:
        raise ResourceNotFoundException(message="AI厂商不存在")
    
    session.delete(provider)
    session.commit()
    return success_response(data=None, message=ResponseMessage.DELETED)

# ==================== AI模型相关API ====================

@router.post("/model/page", response_model=BaseResponse[PageResponse[AIModelPublic]])
def page_models(
    session: SessionDep,
    current_user: CurrentUser,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取AI模型列表。"""
    page = request_data.get("page", 1)
    rows = request_data.get("rows", 20)
    keyword = request_data.get("keyword")
    provider_id = request_data.get("provider_id")
    llm_type = request_data.get("llm_type")
    
    # 使用JOIN查询获取厂商名称
    statement = select(AIModel,
     AIProvider.display_name.label("provider_name"),
    AIProvider.api_base_url.label("provider_api_base_url"),
    AIProvider.api_secret.label("provider_api_secret")
    ).join(
        AIProvider, AIModel.provider_id == AIProvider.id, isouter=True
    )
    
    # 应用关键词搜索
    statement = apply_keyword_search(
        statement=statement,
        model=AIModel,
        keyword=keyword,
        search_fields=["name", "display_name", "llm_id"]
    )
    
    # 应用厂商过滤
    if provider_id:
        statement = statement.where(AIModel.provider_id == provider_id)
    
    # 应用模型类型过滤
    if llm_type:
        statement = statement.where(AIModel.llm_type == llm_type)
    
    count_statement = get_count_query(statement, AIModel)
    count = session.exec(count_statement).one()

    statement = build_order_by(
        statement=statement,
        model=AIModel,
        order_by="id",
        order_direction="desc"
    )

    statement, _, _ = apply_pagination(
        statement=statement,
        page=page,
        page_size=rows
    )

    results = session.exec(statement).all()
    
    # 构建包含provider_name的模型列表
    models_with_provider = []
    for result in results:
        llm_data = result[0].model_dump()
        llm_data["provider_name"] = result[1]  # provider_name from join
       
        llm_public = AIModelPublic.model_validate(llm_data)
        models_with_provider.append(llm_public)
    
    return page_response(
        items=models_with_provider,
        page=page,
        rows=rows,
        total=count,
        message="获取AI模型列表成功"
    )


@router.post("/model/mymodels", response_model=BaseResponse[PageResponse[AIModelPublic]])
def mymodels(
    session: SessionDep,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取AI模型列表。"""
    page = request_data.get("page", 1)
    rows = request_data.get("rows", settings.DEFAULT_PAGE_SIZE)
    keyword = request_data.get("keyword")
    provider_id = request_data.get("provider_id")
    llm_type = request_data.get("llm_type")
    
    # 使用JOIN查询获取厂商名称
    statement = select(AIModel,
     AIProvider.display_name.label("provider_name"),
    AIProvider.api_base_url.label("provider_api_base_url"),
    AIProvider.api_secret.label("provider_api_secret")
    ).join(
        AIProvider, AIModel.provider_id == AIProvider.id, isouter=True
    )
    
    # 应用关键词搜索
    statement = apply_keyword_search(
        statement=statement,
        model=AIModel,
        keyword=keyword,
        search_fields=["name", "display_name", "llm_id"]
    )
    
    # 应用厂商过滤
    if provider_id:
        statement = statement.where(AIModel.provider_id == provider_id)
    
    # 应用模型类型过滤
    if llm_type:
        statement = statement.where(AIModel.llm_type == llm_type)
    
    count_statement = get_count_query(statement, AIModel)
    count = session.exec(count_statement).one()

    statement = build_order_by(
        statement=statement,
        model=AIModel,
        order_by="id",
        order_direction="desc"
    )

    statement, _, _ = apply_pagination(
        statement=statement,
        page=page,
        page_size=rows
    )

    results = session.exec(statement).all()
    
    # 构建包含provider_name的模型列表
    models_with_provider = []
    for result in results:
        llm_data = result[0].model_dump()
        llm_data["provider_name"] = result[1]  # provider_name from join
        llm_data["provider_api_base_url"] = result[2]
        llm_data["provider_api_secret"] = result[3]
        llm_public = AIModelPublic.model_validate(llm_data)
        models_with_provider.append(llm_public)
    
    return page_response(
        items=models_with_provider,
        page=page,
        rows=rows,
        total=count,
        message="获取AI模型列表成功"
    )


@router.post("/model/detail/{uuid}", response_model=BaseResponse[AIModelDetailResponse])
def read_model(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单个AI模型详情（包含厂商信息）。"""
    statement = select(AIModel).where(AIModel.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=AIModel,
        current_user=current_user
    )
    model = session.exec(statement).first()
    if not model:
        raise ResourceNotFoundException(message="AI模型不存在")
    
    # 获取厂商信息
    provider = None
    if model.provider_id:
        provider_statement = select(AIProvider).where(AIProvider.id == model.provider_id)
        provider_statement = apply_common_filters(
            statement=provider_statement,
            model=AIProvider,
            current_user=current_user
        )
        provider = session.exec(provider_statement).first()
    
    # 构建响应数据
    llm_data = model.model_dump()
    llm_data["provider_name"] = provider.display_name if provider else None
    llm_public = AIModelPublic.model_validate(llm_data)
    provider_public = AIProviderPublic.model_validate(provider.model_dump()) if provider else None
    
    response_data = AIModelDetailResponse(
        llm_info=llm_public,
        provider_info=provider_public
    )
    
    return success_response(data=response_data, message="获取AI模型详情成功")

@router.post("/model/create", response_model=BaseResponse[AIModelPublic])
def create_model(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    llm_in: AIModelCreate
) -> Any:
    """创建新AI模型。"""
    llm_data = llm_in.model_dump()
    llm_data = update_common_fields(
        data=llm_data,
        current_user=current_user,
        is_create=True
    )
    model = AIModel.model_validate(llm_data)
    session.add(model)
    session.commit()
    session.refresh(model)
    return success_response(
        data=model,
        message=ResponseMessage.CREATED,
        code=ResponseCode.CREATED
    )

@router.post("/model/update/{uuid}", response_model=BaseResponse[AIModelPublic])
def update_model(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    llm_in: AIModelUpdate,
) -> Any:
    """更新AI模型信息。"""
    statement = select(AIModel).where(AIModel.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=AIModel,
        current_user=current_user
    )
    model = session.exec(statement).first()
    if not model:
        raise ResourceNotFoundException(message="AI模型不存在")
    
    update_dict = llm_in.model_dump(exclude_unset=True)
    update_dict = update_common_fields(
        data=update_dict,
        current_user=current_user,
        is_create=False
    )
    model.sqlmodel_update(update_dict)
    session.add(model)
    session.commit()
    session.refresh(model)
    return success_response(data=model, message=ResponseMessage.UPDATED)

@router.post("/model/delete/{uuid}", response_model=BaseResponse[None])
def delete_model(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """删除AI模型（直接删除）。"""
    statement = select(AIModel).where(AIModel.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=AIModel,
        current_user=current_user
    )
    model = session.exec(statement).first()
    if not model:
        raise ResourceNotFoundException(message="AI模型不存在")
    
    session.delete(model)
    session.commit()
    return success_response(data=None, message=ResponseMessage.DELETED)

@router.post("/model/set-default/{uuid}", response_model=BaseResponse[AIModelPublic])
def set_default_model(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """设置默认AI模型。"""
    # 先取消所有默认模型
    all_models_statement = select(AIModel)
    all_models_statement = apply_common_filters(
        statement=all_models_statement,
        model=AIModel,
        current_user=current_user
    )
    all_models = session.exec(all_models_statement).all()
    
    for model in all_models:
        if model.is_default:
            model.is_default = False
            session.add(model)
    
    # 设置指定模型为默认
    statement = select(AIModel).where(AIModel.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=AIModel,
        current_user=current_user
    )
    model = session.exec(statement).first()
    if not model:
        raise ResourceNotFoundException(message="AI模型不存在")
    
    model.is_default = True
    update_dict = update_common_fields(
        data={"is_default": True},
        current_user=current_user,
        is_create=False
    )
    model.sqlmodel_update(update_dict)
    session.add(model)
    session.commit()
    session.refresh(model)
    
    return success_response(data=model, message="设置默认模型成功") 