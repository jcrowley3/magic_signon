from pydantic import BaseModel  # pylint: disable=no-name-in-module
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


"""
Why is this here?

SQLAlchemy: Cannot use 'DeclarativeBase'
directly as a declarative base class.
Create a Base by creating a subclass of it.
"""


class Base(DeclarativeBase, MappedAsDataclass):
    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class BasePydantic(BaseModel):
    class Config:
        orm_mode = True
        validate_assignment = True


class S3FieldsModel(BaseModel):
    key: str
    AWSAccessKeyId: str
    x_amz_security_token: str
    policy: str
    signature: str


class S3ResponseModel(BaseModel):
    url: str
    fields: S3FieldsModel


class DeleteWarning(BasePydantic):
    message: str
