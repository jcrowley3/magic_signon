import os
import random

from fastapi import HTTPException
from starlette import status

from app.database.base_crud import BaseCRUD
from app.actions.user_actions import UserActions
from app.actions.user_service_actions import UserServiceActions
from app.libraries.sms import send_sms_worker
from app.libraries.sparkpost import send_auth_email
from app.schemas.user_service_schemas import UserServiceUpdate
from app.models.user_service_models import UserServiceModelDB
from app.schemas.auth_schemas import CreateAuthModel, AuthResponseModel, RedeemAuthModel
from app.utilities.utils import GenerateUUID
from cryptography.fernet import Fernet, InvalidToken


secretish_key = os.environ["FERNET_KEY"]
key = bytes(secretish_key, "UTF-8")
da_vinci = Fernet(key)


class ExpiredMessage:
    detail: str = "Expired Login Token"


class AuthActions:

    @classmethod
    async def post_auth_handler(cls, auth_model: CreateAuthModel):
        check_user_service = await cls.post_auth_creation(auth_model)
        if check_user_service:
            new_auth_response = AuthResponseModel(
                login_secret=check_user_service.login_secret,
                login_token=check_user_service.login_token,
                service_user_id=check_user_service.service_user_id,
                service_type=check_user_service.service_type
            )
            return new_auth_response

    @classmethod
    async def post_auth_creation(cls, auth_model):
        service = await BaseCRUD.get_one_where(
            UserServiceModelDB,
            [
                UserServiceModelDB.service_type == auth_model.service_type,
                UserServiceModelDB.service_user_id == auth_model.service_user_id
            ]
        )

        if not service:
            raise HTTPException(status_code=400, detail="No Matching Service Found.")

        auth_object = await cls.generate_auth(service)

        updates = UserServiceUpdate(
            login_token=auth_object.login_token,
            login_secret=auth_object.login_secret
        )

        response = await UserServiceActions.update_service(
            auth_object.user_uuid,
            auth_object.uuid,
            updates
        )

        return response

    @classmethod
    async def redeem_auth_handler(cls, redeem_auth_model):
        check_redeem = await cls.check_for_match_put(redeem_auth_model)
        if check_redeem:
            return await UserActions.get_user_by_uuid(check_redeem.user_uuid)
        else:
            return check_redeem

    @classmethod
    async def check_for_match_put(cls, redeem_auth_model: RedeemAuthModel):
        is_match = await BaseCRUD.check_if_exists(
            UserServiceModelDB,
            [
                UserServiceModelDB.login_token == redeem_auth_model.login_token,
                UserServiceModelDB.login_secret == redeem_auth_model.login_secret
            ]
        )

        if not is_match:
            raise HTTPException(status_code=400, detail="Login Credentials Don't Match.")

        try:
            da_vinci.decrypt(redeem_auth_model.login_secret, ttl=900)
            await cls.update_token_secret(redeem_auth_model)
            return is_match
        except InvalidToken:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ExpiredMessage().detail
            )

    @classmethod
    async def generate_auth(cls, service_obj):
        if service_obj.service_type == "email":
            service_obj.login_token = GenerateUUID.hex()
            service_obj.login_secret = da_vinci.encrypt(GenerateUUID.bytes())

            sent_email = await cls.send_email_handler(service_obj)
            if sent_email:
                return service_obj
            else:
                print("error")
                return service_obj

        else:
            service_obj.login_token = str(random.randint(1000, 9999))
            service_obj.login_secret = da_vinci.encrypt(GenerateUUID.bytes())

            sent_message = await cls.send_sms_handler(service_obj)
            if sent_message:
                return service_obj
            else:
                print("error")
                return service_obj

    @classmethod
    async def send_sms_handler(cls, service_obj_cell):
        sent_message = await send_sms_worker(service_obj_cell)
        if sent_message:
            return sent_message
        else:
            # TODO: improve error handling
            print("error sending text")
            return None

    @classmethod
    async def send_email_handler(cls, service_obj):
        response = await send_auth_email(service_obj)
        if response["total_accepted_recipients"] == 1:
            return response
        else:
            # TODO: improve error handling
            print("error sending text")
            return None

    @classmethod
    async def get_client_user_client_uuid(cls, user_uuid: str):
        client_user = {
            "uuid": "06ad1e1f05a61ab1ac423d5a6fb969193305145100c888a069eaacbf",
            "user_uuid": user_uuid,
            "client_uuid": "ca723b34b08e4e319c8d2e6770815679c69aaf4a8e574f518b1e34",
            "manager_uuid": "06ad1e1f05a61ab1ac423d5a6fb969193305145100c888a069eaacbf",
            "title": "Domestique",
            "department": "Domestique",
            "employee_id": "123abc",
            "active": 1,
            "time_created": None,
            "time_updated": None,
            "time_hire": None,
            "time_start": None,
            "admin": 2,
        }
        return client_user["client_uuid"]

    @classmethod
    async def update_token_secret(cls, redeem_auth_model):
        updates = UserServiceUpdate(
            login_token=GenerateUUID.hex(),
            login_secret=GenerateUUID.hex()
        )

        response = await BaseCRUD.update(
            UserServiceModelDB,
            [
                UserServiceModelDB.login_token == redeem_auth_model.login_token,
                UserServiceModelDB.login_secret == redeem_auth_model.login_secret
            ],
            updates
        )
        return response
