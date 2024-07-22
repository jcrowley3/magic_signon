from typing import Annotated
from fastapi import APIRouter, Depends, Body, Path
from app.dependencies import query_params
from app.schemas.user_service_schemas import (
    UserServiceUpdate,
    UserServiceCreate,
    ServiceBulkDelete,
    ServiceStatus,
    ServiceBulk,
    UserServiceResponse,
    ServiceListResponse,
)
from app.actions.user_service_actions import UserServiceActions
from app.actions.user_actions import UserActions
from app.models.user_models import UserModel
from app.utilities.auth_utils import Permissions

router = APIRouter(tags=["Users Service"], prefix="/users/{user_uuid}")


@router.get("/services", response_model=ServiceListResponse)
async def get_services(
    auth: Annotated[str, Depends(Permissions(level="1"))],
    user_uuid: str = Path(...),
    query_params: dict = Depends(query_params)
):
    return await UserServiceActions.get_all_services(user_uuid, query_params)


@router.get("/services/{service_uuid}", response_model=UserServiceResponse)
async def get_service(
    auth: Annotated[str, Depends(Permissions(level="1"))],
    user_uuid: str = Path(...),
    service_uuid: str = Path(...)
):
    return await UserServiceActions.get_service(user_uuid, service_uuid)


@router.post("/services", response_model=ServiceStatus)
async def create_service(
    auth: Annotated[str, Depends(Permissions(level="1"))],
    user_uuid: str = Path(...),
    user_service: UserServiceCreate = Depends(UserServiceActions.check_existing),
    user: UserModel = Depends(UserActions.get_user_by_uuid)
):
    return await UserServiceActions.create_user_service(user, user_service)


@router.put("/services/{service_uuid}", response_model=UserServiceResponse)
async def update_service(
    auth: Annotated[str, Depends(Permissions(level="1"))],
    user_uuid: str = Path(...),
    service_uuid: str = Path(...),
    service_updates: UserServiceUpdate = Body(...)
):
    return await UserServiceActions.update_service(user_uuid, service_uuid, service_updates)


@router.put("/services", response_model=list[UserServiceResponse])
async def bulk_update_services(
    auth: Annotated[str, Depends(Permissions(level="1"))],
    user_uuid: str = Path(...),
    updates: ServiceBulk = Body(...)
):
    return await UserServiceActions.bulk_update_services(user_uuid, updates)


@router.delete("/services/{service_uuid}")
async def delete_service(
    auth: Annotated[str, Depends(Permissions(level="1"))],
    service_uuid: str = Path(...)
):
    return await UserServiceActions.delete_service(service_uuid)


@router.delete("/services")
async def bulk_delete_service(
    auth: Annotated[str, Depends(Permissions(level="2"))],
    service_delete: ServiceBulkDelete = Body(...)
):
    return await UserServiceActions.bulk_delete_services(service_delete)
