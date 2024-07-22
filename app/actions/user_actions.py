import random
from time import time
from fastapi import HTTPException
from app.database.base_crud import BaseCRUD
from app.libraries.sparkpost import send_add_service_code_email
from app.actions.helper_actions import HelperActions
from app.actions.user_service_actions import UserServiceActions
from app.models.user_models import UserModelDB
from app.schemas.user_schemas import UserExpanded, UserCreate, UserUpdate, UserMigrate
from app.schemas.user_service_schemas import UserServiceCreate, ServiceStatus
from app.models.user_service_models import UserServiceModelDB


class UserActions:

    @classmethod
    async def get_user_by_uuid(cls, user_uuid):
        return await BaseCRUD.get_one_where(UserModelDB, [UserModelDB.uuid == user_uuid])

    @classmethod
    async def get_user_by_service_id(cls, service_id):
        return await BaseCRUD.check_if_exists(
            UserModelDB,
            [
                UserServiceModelDB.service_user_id == service_id,
                UserServiceModelDB.user_uuid == UserModelDB.uuid

            ]
        )

    @staticmethod
    async def get_user_by_auth_code(user_uuid, auth_code):
        return await BaseCRUD.get_one_where(
            UserModelDB,
            [
                UserModelDB.uuid == user_uuid,
                UserModelDB.auth_code == auth_code
            ]
        )

    # TODO: magic_login, refactor to remove user_account references
    # @staticmethod
    # async def get_user_data_by_company_id(company_id: int, hired_on_cap: int = None):
    #     conditions = [
    #         # UserAccountModelDB.company_id == company_id,
    #         # UserAccountModelDB.user_uuid == UserModelDB.uuid,
    #         UserModelDB.uuid == UserServiceModelDB.user_uuid,
    #         UserServiceModelDB.user_uuid == UserAccountModelDB.user_uuid
    #     ]
    #     # if hired_on_cap:
    #         # condition = UserAccountModelDB.hired_on > hired_on_cap
    #         # conditions.append(condition)
    #     return await BaseCRUD.get_all_where(
    #         [
    #             UserModelDB.first_name,
    #             UserModelDB.last_name,
    #             UserModelDB.time_birthday,
    #             # UserAccountModelDB.uuid.label("user_account_uuid"),
    #             # UserAccountModelDB.hired_on,
    #             # UserAccountModelDB.segment_metadata,
    #             # UserAccountModelDB.employee_id,
    #             # UserAccountModelDB.account_id,
    #             # UserAccountModelDB.account_gid,
    #             UserServiceModelDB.service_user_id.label("email")
    #         ],
    #         conditions,
    #         pagination=False,
    #         # join_model=[UserAccountModelDB, UserServiceModelDB],
    #         join_condition=[UserAccountModelDB.user_uuid == UserModelDB.uuid, UserServiceModelDB.user_uuid == UserModelDB.uuid]
    #     )

    # TODO: refactor to use alt to company_id
    # @classmethod
    # async def get_segmented_users(cls, company_id: int, segmented_by: dict):
    #     users = await cls.get_all_user_data_by_company_id(company_id)
    #     segmented_users = []
    #     for user, user_account, user_service in users:
    #         user_account_dict = user_account.to_dict()
    #         segment_metadata = user_account_dict["segment_metadata"]
    #         all_match = True
    #         for key, value in segmented_by.items():
    #             if segment_metadata.get(key) != value:
    #                 all_match = False
    #                 break
    #         if all_match:
    #             segmented_users.append((user, user_account, user_service))

    #     return segmented_users

    @classmethod
    async def check_auth_code(cls, user_uuid, auth_code):
        if auth_code < 1000:
            raise HTTPException(detail="Invalid Authorization Code Format", status_code=400)
        user = await cls.get_user_by_auth_code(user_uuid, auth_code)
        if not user:
            raise HTTPException(detail="Authorization Code is Incorrect", status_code=400)
        # nullify auth_code for user
        await cls.update_user(user_uuid, UserUpdate(auth_code=random.randint(1000, 9999)))
        return user

    @classmethod
    async def get_all_users(cls, query_params: dict, paginate: bool = True):
        return await BaseCRUD.get_all(UserModelDB, query_params, paginate)

    @classmethod
    async def get_user(cls, user_uuid, expand_services=False):
        user = await cls.get_user_by_uuid(user_uuid)
        if expand_services:
            return await cls.expand_services(user)
        return user

    @staticmethod
    async def expand_services(user_obj, service=None):
        user_expand = UserExpanded.from_orm(user_obj)
        if service:
            user_expand.services = service
        else:
            user_expand.services = await UserServiceActions.get_all_services(user_obj.uuid)
        return user_expand

    @staticmethod
    async def get_service_id(new_user_obj: dict, service_id=None):
        """Get the service ID from the specified user object
        :param new_user_obj: The user object to get the service ID from
        :return: A namedtuple containing the service type and service ID, or None if it couldn't be found
        """
        if (service_id := await HelperActions.get_email_from_header(new_user_obj, service_id)):
            return service_id
        elif (service_id := await HelperActions.get_cell_from_header(new_user_obj, service_id)):
            return service_id
        else:
            return None

    @classmethod
    async def handle_user_job(cls, job_data: dict):
        user_data = job_data.get("body").get("user")
        new_user = UserCreate(**user_data)
        user = await cls.create_user(new_user)
        return user

    @classmethod
    async def create_user(cls, users, expand_services: bool = False):
        if isinstance(users, list):
            for i, user_obj in enumerate(users):
                users[i] = await cls.create_user_and_service(user_obj)
                if expand_services:
                    users[i] = await cls.expand_services(users[i])
        else:
            users = await cls.create_user_and_service(users)
            if expand_services:
                users = await cls.expand_services(users)

        return users

    @classmethod
    async def create_user_and_service(cls, new_user_data, service=None):
        if hasattr(new_user_data, "dict"):
            new_user_data: dict = new_user_data.dict(exclude_none=True)
        service_id = await cls.get_service_id(new_user_data, service)
        service_to_check = UserServiceCreate(service_type=service_id.type, service_user_id=service_id.value)

        existing_service = await UserServiceActions.check_existing(service_to_check)
        if not isinstance(existing_service, UserServiceCreate):
            user = await cls.get_user_by_service_id(existing_service.service_user_id)
            return user

        if not service_id:
            raise Exception("service_id required")
        first_name = await HelperActions.get_fname_from_header(new_user_data)
        last_name = await HelperActions.get_lname_from_header(new_user_data)
        birthday = new_user_data.get("time_birthday")

        lat, lon = None, None
        user_uuid = new_user_data.get("user_uuid", None)

        new_user_obj = UserModelDB(
            uuid=user_uuid,
            first_name=first_name,
            last_name=last_name,
            latitude=lat,
            longitude=lon,
            time_ping=int(time()),
            admin=await HelperActions.get_admin(new_user_data),
            time_birthday=birthday
        )
        user_db = await BaseCRUD.create(new_user_obj)
        if new_user_data.get("company_id"):
            client_uuid, company_id, is_personal = None, new_user_data.get("company_id"), False
        elif new_user_data.get("client_uuid"):
            client_uuid, company_id, is_personal = new_user_data.get("client_uuid"), None, False
        else:
            client_uuid, company_id, is_personal = None, None, True
        new_service = await UserServiceActions.create_service_for_new_user(user_db, service_id, client_uuid, company_id, is_personal)
        if not new_service:
            raise Exception("Service Creation Failed")
        return user_db

    @classmethod
    async def send_auth_code(cls, user_uuid, service_obj: UserServiceCreate, is_job: bool = False):
        auth_code = random.randint(1000, 9999)
        updated_user = await UserActions.update_user(user_uuid, UserUpdate(auth_code=auth_code))

        if updated_user.auth_code != auth_code and not is_job:
            return {"Message": "There was an error updating the users information with the authorization code"}
        elif updated_user.auth_code != auth_code and is_job:
            return False

        email = await send_add_service_code_email(service_obj, auth_code)

        if email.get("total_rejected_recipients") > 0 and not is_job:
            return {"Message": "Authentication code failed to send."}
        elif email.get("total_rejected_recipients") > 0 and is_job:
            return False

        return {"Message": "Authroziation code successfully sent."}

    @classmethod
    async def confirm_code_add_service(cls, user_uuid, service_obj: UserServiceCreate, is_job: bool = False):
        if isinstance(service_obj, ServiceStatus) and not is_job:
            raise HTTPException(status_code=403, detail="The provided service already exists")
        elif isinstance(service_obj, ServiceStatus) and is_job:
            return "exists"
        authenticated_user = await cls.check_auth_code(user_uuid, service_obj.auth_code)
        new_service = await UserServiceActions.create_user_service(authenticated_user, service_obj)
        return new_service

    @classmethod
    async def confirm_code_migrate_user(cls, user_uuid, service_obj: UserServiceCreate):
        authenticated_user = await cls.check_auth_code(user_uuid, service_obj.auth_code)
        user_to_migrate = await cls.get_user_by_service_id(service_obj.service_user_id)
        if user_uuid == user_to_migrate.uuid:
            return False
        if not user_to_migrate:
            return False
        models_to_update = [UserServiceModelDB]
        conditions = [
            [UserServiceModelDB.user_uuid == user_to_migrate.uuid]
        ]
        migration_response = await BaseCRUD.migrate(models_to_update, conditions, UserMigrate(user_uuid=authenticated_user.uuid))
        return {"migration_successful": migration_response}

    @classmethod
    async def update_user(cls, user_uuid, updates):
        return await BaseCRUD.update(UserModelDB, [UserModelDB.uuid == user_uuid], updates)

    @classmethod
    async def delete_user(cls, user_uuid):
        return await BaseCRUD.delete_one(UserModelDB, [UserModelDB.uuid == user_uuid])

    @classmethod
    async def delete_test_user(cls, user_uuid):
        services = await UserServiceActions.get_all_services(user_uuid)
        for key, value in services.items():
            for item in value:
                await BaseCRUD.delete_one(UserServiceModelDB, [UserServiceModelDB.uuid == item.uuid])
