from enum import Enum
from typing import Optional
from pydantic import Field
from app.models.base_models import BasePydantic
from app.models.user_service_models import UserServiceModel


class ServiceType(str, Enum):
    email = "email"
    cell = "cell"
    slack = "slack"
    teams = "teams"
    web = "web"

    def __repr__(self) -> str:
        # return super().__repr__()
        return self.value


class UserServiceStatus(str, Enum):
    exists = "exists"
    created = "service created"
    updated = "service updated"


class UserServiceResponse(UserServiceModel):
    pass


class ServiceListResponse(BasePydantic):
    email: Optional[list[UserServiceModel]]
    cell: Optional[list[UserServiceModel]]


class UserServiceCreate(BasePydantic):
    company_id: Optional[int]
    service_type: ServiceType
    service_user_id: str
    auth_code: Optional[int]
    is_personal: Optional[bool]
    service_user_screenname: Optional[str]
    service_user_name: Optional[str]
    service_type: Optional[str]


class ServiceStatus(UserServiceModel):
    status: Optional[UserServiceStatus] = Field(
        default=None,
        description="This mapped_column can have the values 'exists' or 'admin created'."
    )


class UserServiceUpdate(BasePydantic):
    company_id: Optional[int]
    service_user_screenname: Optional[str]
    service_user_name: Optional[str]
    service_access_token: Optional[str]
    service_access_secret: Optional[str]
    service_refresh_token: Optional[str]
    service_user_id: Optional[str]
    login_secret: Optional[str]
    login_token: Optional[str]


class UserServiceBulkUpdate(UserServiceUpdate):
    uuid: str


class ServiceBulk(UserServiceUpdate):
    updates: list[UserServiceBulkUpdate]


class ServiceDelete(BasePydantic):
    service_uuid: str


class ServiceBulkDelete(BasePydantic):
    deletes: list[ServiceDelete]
