import pytest
import tests.testutil as utils
from app.actions.user_actions import UserActions
from app.actions.user_service_actions import UserServiceActions
from app.schemas.user_schemas import UserUpdate, UserCreate


@pytest.mark.asyncio
async def test_get_all_users(user):
    users = await UserActions.get_all_users(query_params={}, paginate=False)
    assert isinstance(users, list)
    assert any(user_db.uuid == user["uuid"] for user_db in users)


@pytest.mark.asyncio
async def test_get_user(user):
    user_response = await UserActions.get_user(user["uuid"])
    assert user_response.uuid == user["uuid"]
    assert user_response.first_name == utils.new_user["first_name"]


@pytest.mark.asyncio
async def test_create_user():
    try:
        create_model = UserCreate(**utils.new_user)
        new = await UserActions.create_user(create_model, True)
        assert new.uuid
        assert new.first_name == "Test"
    finally:
        await UserActions.delete_user(new.uuid)
        await UserServiceActions.delete_service(new.services["email"][0].uuid)


@pytest.mark.asyncio
async def test_update_user(user):
    update_model = UserUpdate(**utils.update_user)
    updated_user = await UserActions.update_user(user["uuid"], update_model)
    assert user["uuid"] == updated_user.uuid
    assert updated_user.first_name == utils.update_user["first_name"]


@pytest.mark.asyncio
async def test_delete_user(user):
    await UserActions.delete_user(user["uuid"])
    user = await UserActions.get_user(user["uuid"])
    assert user is None
