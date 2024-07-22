from typing import Annotated
from fastapi import APIRouter, Depends, Body, Path, Query
from app.pagination import Page
from app.dependencies import query_params, test_mode
from app.actions.user_actions import UserActions
from app.actions.user_service_actions import UserServiceActions
from app.models.base_models import DeleteWarning
from app.schemas.user_service_schemas import UserServiceCreate
from app.schemas.user_schemas import (
    UserUpdate,
    UserCreate,
    UserExpanded,
    UserResponse,
    UserDelete,
    UserAlt,
)
from app.utilities.auth_utils import Permissions


router = APIRouter(tags=["Users"])


@router.get("/users", response_model=Page[UserResponse])
async def get_users(
    auth: Annotated[str, Depends(Permissions(level="2"))],
    query_params: dict = Depends(query_params)
):
    return await UserActions.get_all_users(query_params)


@router.get("/users/{user_uuid}", response_model=UserExpanded | None)
async def get_user(
    auth: Annotated[str, Depends(Permissions(level="1"))],
    user_uuid: str = Path(...),
    expand_services: bool = Query(False)
):
    return await UserActions.get_user(user_uuid, expand_services)


@router.post("/users/alt", response_model=UserResponse | None)
async def get_user_by_service_id(
    auth: Annotated[str, Depends(Permissions(level="1"))],
    service_obj: UserAlt = Body(...)
):
    return await UserActions.get_user_by_service_id(service_obj.service_user_id)


@router.post("/users", response_model=UserExpanded)
async def create_user(
    auth: Annotated[str, Depends(Permissions(level="1"))],
    users: UserCreate = Body(...),
    expand_services: bool = Query(False)
):
    return await UserActions.create_user(users, expand_services)


@router.put("/users/{user_uuid}", response_model=UserResponse)
async def update_user(
    auth: Annotated[str, Depends(Permissions(level="1"))],
    user_uuid: str = Path(...),
    users_updates: UserUpdate = Body(...)
):
    return await UserActions.update_user(user_uuid, users_updates)


@router.delete("/users/{user_uuid}", response_model=UserDelete | DeleteWarning)
async def delete_user(
    auth: Annotated[str, Depends(Permissions(level="2"))],
    user_uuid: str = Path(...)
):
    return await UserActions.delete_user(user_uuid)


@router.delete("/delete_test_user/{user_uuid}", dependencies=[Depends(test_mode)])
async def delete_test_user(
    auth: Annotated[str, Depends(Permissions(level="2"))],
    user_uuid: str = Path(...)
):
    from fastapi import Response
    await UserActions.delete_test_user(user_uuid)
    return Response(status_code=200, content="Test User Deleted")


@router.post("/users/{user_uuid}/services/add")
async def set_auth_code_for_additional_service(
    # unsure of permission needed for adding service
    auth: Annotated[str, Depends(Permissions(level="1"))],
    user_uuid: str = Path(...),
    user_service: UserServiceCreate = Body(...)
):
    return await UserActions.send_auth_code(user_uuid, user_service)


@router.post("/users/{user_uuid}/services/confirm")
async def confirm_code_add_service(
    # unsure of permission needed for adding service
    auth: Annotated[str, Depends(Permissions(level="1"))],
    user_uuid: str = Path(...),
    user_service: UserServiceCreate = Depends(UserServiceActions.check_existing)
):
    return await UserActions.confirm_code_add_service(user_uuid, user_service)


@router.post("/users/{user_uuid}/services/migrate")
async def confirm_code_migrate_user(
    # unsure of permission needed for adding service
    auth: Annotated[str, Depends(Permissions(level="1"))],
    user_uuid: str = Path(...),
    user_service: UserServiceCreate = Body(...)
):
    return await UserActions.confirm_code_migrate_user(user_uuid, user_service)
