from enum import Enum
from pydantic import BaseModel  # pylint: disable=no-name-in-module


class EnumBaseModel(BaseModel):
    class Config:
        validate_assignment = True
        orm_mode = True


class BaseEnum(Enum):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_response

    @classmethod
    def validate_response(cls, value):
        # TODO: add check for GeomEnum cls
        if isinstance(value, str) and value in cls._member_map_:  # pylint: disable=no-member
            return value
        # TODO: check does not return correctly if value is from db, just 500s
        if value not in cls._value2member_map_:
            raise ValueError(f"{value} is not a valid {cls.__name__} value")
        return cls(value).name

    @classmethod
    def validate_request(cls, value):
        if isinstance(value, str) and value in cls._member_map_:  # pylint: disable=no-member
            return cls(value).value
        return value

    @classmethod
    def validate_paginate(cls, value):
        if hasattr(cls, "_validation_done"):
            # return cls(value).name
            return cls(value).name
        setattr(cls, "_validation_done", True)
        return cls(value).value


class BaseGeomEnum(Enum):

    @classmethod
    def from_value(cls, value: int):
        """Get a list of GeomEnum members from combined value."""
        members = [member for member in cls if member.value & value]

        if sum(member.value for member in members) != value:
            raise ValueError(f"{value} does not correspond to a valid combination of {cls.__name__} values.")

        return members

    @classmethod
    def to_value(cls, members: list["BaseGeomEnum"]) -> int:
        """Get combined value from a list of GeomEnum members."""
        return sum(member.value for member in members)

    def __and__(self, other):
        return self.value & other.value

    def __or__(self, other):
        return self.value | other.value

    # For pydantic support
    def __int__(self):
        return self.value

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, int):
            if cls.from_value(v):
                return v
        if isinstance(v, str):
            v = int(v)
            vals = cls.from_value(v)
            if vals:
                vals = [val.name for val in vals]
                return vals
        if isinstance(v, cls):
            return v
        raise ValueError(f"Cannot convert {v} to {cls}")


class Admin(BaseEnum):  # TODO: may be a GeomEnum at some point
    not_admin = 0
    client_admin = 1
    system_admin = 2


# class AwardType(BaseEnum):
class AwardType(BaseEnum):
    reward = 1
    recognition = 2


class BudgetType(BaseEnum):  # TODO: Verify, is listed as GeomEnum in Confluence docs
    static = 0
    passthru_nocap = 1
    passthru_cap = 2


class Cadence(BaseEnum):
    recurring = 1
    non_recurring = 2


class CadenceValue(BaseEnum):
    keydate = 1
    interval_year = 2
    interval_month = 3
    interval_week = 4
    interval_day = 5
    interval_hour = 6


class ChannelType(BaseGeomEnum):
    email = 1
    sms = 2
    p2p_slack = 4
    p2p_teams = 8
    web = 16


class EventType(BaseEnum):
    award = 1
    approval = 2
    notification = 3
    budget = 4


class MessageType(BaseEnum):
    welcome = 1
    auth = 2
    award = 3
    anniversary = 4
    birthday = 5
    redeem = 6
    message = 7
    reminder = 8
    survey = 9


class ProgramType(BaseEnum):
    milestone = 1
    nomination = 2
    incentive = 3
    spot = 4


class RuleType(BaseEnum):
    audience = 1
    award = 2
    approval = 3


class Status(BaseEnum):
    draft = 1
    published = 2
    disabled = 3


class ClientStatus(BaseEnum):
    inactive = 0
    active = 1


class SignonJobs(Enum):
    ADD_NEW_SERVICE = "ADD_NEW_SERVICE"
    ALT_GET_USER = "ALT_GET_USER"
    CREATE_USER = "CREATE_USER"
    GET_USER = "GET_USER"
    GET_USERS_BY_COMPANY_ID = "GET_USERS_BY_COMPANY_ID"
    CREATE_USER_ACCOUNT = "CREATE_USER_ACCOUNT"
    MIGRATE_USER = "MIGRATE_USER"
    MOCK_GET_SURVEY_RESPONSE = "MOCK_GET_SURVEY_RESPONSE"
    SEND_AUTH_CODE = "SEND_AUTH_CODE"
    UPDATE_USER_ACCOUNT = "UPDATE_USER_ACCOUNT"
    GET_USERS_FOR_REWARD_CREATION = "GET_USERS_FOR_REWARD_CREATION"
