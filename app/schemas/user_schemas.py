from typing import Optional
from pydantic import validator
from app.utilities.enums import Admin
from app.models.base_models import BasePydantic
from app.models.user_models import UserModel


class UserResponse(UserModel):
    pass


class UserRedeemResponse(UserModel):

    @validator("admin", pre=False)
    def validate_type(cls, v, field):  # pylint: disable=no-self-argument,no-self-use
        if isinstance(v, int):
            return v
        return field.type_[v].value


class UserServiceInput(BasePydantic):
    email_address: Optional[str]
    email: Optional[str]
    work_email: Optional[str]
    personal_email: Optional[str]
    cell: Optional[int|str]
    cell_phone: Optional[int|str]
    cell_number: Optional[int|str]


class UserCreate(UserServiceInput):
    user_uuid: Optional[str]
    client_uuid: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    latitude: Optional[int]
    longitude: Optional[int]
    time_birthday: Optional[int|str]
    admin: Optional[Admin]
    location: Optional[str]

    @validator("admin", pre=False)
    def validate_type(cls, v, field):  # pylint: disable=no-self-argument,no-self-use
        return field.type_[v].value


class UserUpdate(BasePydantic):
    first_name: Optional[str]
    last_name: Optional[str]
    latitude: Optional[int]
    longitude: Optional[int]
    time_birthday: Optional[int]
    admin: Optional[Admin]
    auth_code: Optional[int]

    @validator("admin", pre=False)
    def validate_type(cls, v, field):  # pylint: disable=no-self-argument,no-self-use
        return field.type_[v].value


class UserMigrate(BasePydantic):
    user_uuid: str


class UserAlt(BasePydantic):
    service_user_id: str


class UserExpanded(UserModel):
    time_birthday: Optional[int|str]
    services: Optional[dict]


class UserDelete(BasePydantic):
    ok: bool
    Deleted: UserModel | None
