from typing import Optional
from pydantic import validator
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base_models import Base, BasePydantic
from app.utilities.enums import Admin


class UserModelDB(Base):
    __tablename__ = "user"

    uuid: Mapped[str] = mapped_column(String(56), default=None, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(255), default=None, nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), default=None, nullable=True)
    latitude: Mapped[int] = mapped_column(Integer(), default=None, nullable=True)
    longitude: Mapped[int] = mapped_column(Integer(), default=None, nullable=True)
    time_created: Mapped[int] = mapped_column(Integer(), default=None, nullable=True)
    time_updated: Mapped[int] = mapped_column(Integer(), default=None, nullable=True)
    time_ping: Mapped[int] = mapped_column(Integer(), default=None, nullable=True)
    time_birthday: Mapped[int] = mapped_column(Integer(), default=None, nullable=True)
    admin: Mapped[int] = mapped_column(Integer(), default=0, nullable=True)
    auth_code: Mapped[int] = mapped_column(Integer(), default=0, nullable=True)


class UserModel(BasePydantic):
    uuid: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    latitude: Optional[int]
    longitude: Optional[int]
    time_created: Optional[int]
    time_updated: Optional[int]
    time_ping: Optional[int]
    time_birthday: Optional[int]
    admin: Optional[Admin]
    auth_code: Optional[int]

    @validator("admin", pre=False)
    def validate_admin_type(cls, v, field):  # pylint: disable=no-self-argument,no-self-use
        return field.type_[v].value
