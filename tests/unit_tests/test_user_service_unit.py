import pytest
import tests.testutil as utils
from app.actions.user_service_actions import UserServiceActions
from app.schemas.user_service_schemas import UserServiceCreate, UserServiceUpdate
from app.models.user_models import UserModel


@pytest.mark.asyncio
async def test_get_all_services(user):
    get_all = await UserServiceActions.get_all_services(user["uuid"])
    assert len(get_all) == 1
    assert get_all["email"][0].uuid == user["services"]["email"][0]["uuid"]


@pytest.mark.asyncio
async def test_get_service(user):
    get_exact = await UserServiceActions.get_service(user["uuid"], user["services"]["email"][0]["uuid"])
    assert get_exact.service_type == utils.new_service["service_type"]


@pytest.mark.asyncio
async def test_create_user_service(user):
    try:
        create_model_service = UserServiceCreate(**utils.new_service)
        user_model = UserModel(**user)
        create = await UserServiceActions.create_user_service(user_model, create_model_service)
        assert create.user_uuid == user["uuid"]
        assert create.service_type == utils.new_service["service_type"]
        assert create.service_user_id == utils.new_service["service_user_id"]
    finally:
        await UserServiceActions.delete_service(create.uuid)


@pytest.mark.asyncio
async def test_update_user_service(user):
    update = UserServiceUpdate(**utils.update_service)
    updated = await UserServiceActions.update_service(user["uuid"], user["services"]["email"][0]["uuid"], update)
    assert updated.service_access_token == utils.update_service["service_access_token"]
