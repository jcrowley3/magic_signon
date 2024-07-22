import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import tests.testutil as utils
from app.actions.user_actions import UserActions
from app.actions.user_service_actions import UserServiceActions
from app.schemas.user_service_schemas import UserServiceCreate
from app.schemas.user_schemas import UserCreate


@pytest.mark.asyncio
async def test_send_auth_code(mock_sparkpost, user):
    if mock_sparkpost:
        with patch("app.actions.user_actions.send_add_service_code_email") as mock_send_add_service_code_email:
            mock_send_add_service_code_email.return_value = {"total_rejected_recipients": 0}
            auth_code_response = await UserActions.send_auth_code(user['uuid'], UserServiceCreate(**utils.new_service), True)
            mock_send_add_service_code_email.assert_called_once()
    else:
        auth_code_response = await UserActions.send_auth_code(user['uuid'], UserServiceCreate(**utils.new_service), True)

    assert auth_code_response['Message'] == 'Authroziation code successfully sent.'
    auth_user = await UserActions.get_user(user['uuid'])
    assert auth_user.auth_code > 0


@pytest.mark.asyncio
async def test_add_new_service(mock_sparkpost, user):
    try:
        if mock_sparkpost:
            with patch("app.actions.user_actions.send_add_service_code_email") as mock_send_add_service_code_email:
                mock_send_add_service_code_email.return_value = {"total_rejected_recipients": 0}
                auth_code_response = await UserActions.send_auth_code(user['uuid'], UserServiceCreate(**utils.new_service), True)
                mock_send_add_service_code_email.assert_called_once()
        else:
            auth_code_response = await UserActions.send_auth_code(user['uuid'], UserServiceCreate(**utils.new_service), True)
        auth_user = await UserActions.get_user(user['uuid'])
        new_service = await UserActions.confirm_code_add_service(user["uuid"], UserServiceCreate(service_type='email', service_user_id=utils.new_service['service_user_id'], auth_code=auth_user.auth_code), True)
        assert new_service
    finally:
        await UserServiceActions.delete_service(new_service.uuid)

@pytest.mark.asyncio
async def test_migrate_user(mock_sparkpost, user):
    try:
        new_user = await UserActions.create_user(UserCreate(**utils.new_user_2), True)
        if mock_sparkpost:
            with patch("app.actions.user_actions.send_add_service_code_email") as mock_send_add_service_code_email:
                mock_send_add_service_code_email.return_value = {"total_rejected_recipients": 0}
                auth_code_response = await UserActions.send_auth_code(new_user.uuid, UserServiceCreate(**utils.migrate_service), True)
                mock_send_add_service_code_email.assert_called_once()
        else:
            auth_code_response = await UserActions.send_auth_code(new_user.uuid, UserServiceCreate(**utils.migrate_service), True)
        new_user_auth = await UserActions.get_user(new_user.uuid)
        utils.migrate_service["auth_code"] = new_user_auth.auth_code
        migrated_user = await UserActions.confirm_code_migrate_user(new_user.uuid, UserServiceCreate(**utils.migrate_service))
        assert migrated_user['migration_successful'] == True
        migrated_services = await UserServiceActions.get_all_services(new_user.uuid)
        for service in migrated_services['email']:
            assert service.user_uuid == new_user.uuid
            assert service.service_user_id in [user['services']['email'][0]['service_user_id'], utils.new_user_2['work_email']]
    finally:
        for service in migrated_services['email']:
            await UserServiceActions.delete_service(service.uuid)
        await UserActions.delete_user(new_user.uuid)
