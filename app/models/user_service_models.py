from enum import Enum
from typing import Optional
from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base_models import Base, BasePydantic


class UserServiceStatus(str, Enum):
    exists = "exists"
    created = "service created"
    updated = "service updated"


class UserServiceModelDB(Base):
    __tablename__ = "user_service"

    uuid: Mapped[str] = mapped_column(String(56), default=None, primary_key=True)
    user_uuid: Mapped[Optional[str]] = mapped_column(String(56), default=None, nullable=True)
    client_uuid: Mapped[str] = mapped_column(String(56), default=None, index=True, nullable=True)
    company_id: Mapped[int] = mapped_column(Integer(), default=None, nullable=True)
    is_personal: Mapped[bool] = mapped_column(Boolean, default=None, nullable=True)
    service_type: Mapped[Optional[str]] = mapped_column(String(56), default=None, nullable=True)
    service_user_id: Mapped[Optional[str]] = mapped_column(String(255), default=None, nullable=True)
    service_user_screenname: Mapped[Optional[str]] = mapped_column(String(255), default=None, nullable=True)
    service_user_name: Mapped[Optional[str]] = mapped_column(String(255), default=None, nullable=True)
    service_access_token: Mapped[Optional[str]] = mapped_column(String(255), default=None, nullable=True)
    service_access_secret: Mapped[Optional[str]] = mapped_column(String(255), default=None, nullable=True)
    service_refresh_token: Mapped[Optional[str]] = mapped_column(String(255), default=None, nullable=True)
    time_created: Mapped[Optional[int]] = mapped_column(Integer(), default=None, nullable=True)
    time_updated: Mapped[Optional[int]] = mapped_column(Integer(), default=None, nullable=True)
    login_secret: Mapped[Optional[str]] = mapped_column(String(255), default=None, nullable=True)
    login_token: Mapped[Optional[str]] = mapped_column(String(56), default=None, nullable=True)


class UserServiceModel(BasePydantic):
    uuid: Optional[str]
    user_uuid: Optional[str]
    client_uuid: Optional[str]
    company_id: Optional[int]
    is_personal: Optional[bool]
    service_type: Optional[str]
    service_user_id: Optional[str]
    service_user_screenname: Optional[str]
    service_user_name: Optional[str]
    service_access_token: Optional[str]
    service_access_secret: Optional[str]
    service_refresh_token: Optional[str]
    time_created: Optional[int]
    time_updated: Optional[int]
    login_secret: Optional[str]
    login_token: Optional[str]
