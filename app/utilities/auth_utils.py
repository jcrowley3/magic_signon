from datetime import datetime
from typing import Optional
import jwt
from jwt import PyJWTError
from fastapi import Depends, HTTPException, Cookie
from pydantic.datetime_parse import timedelta  # pylint: disable=no-name-in-module
from starlette import status
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
import os
from pydantic import BaseModel  # pylint: disable=no-name-in-module

get_bearer_token = HTTPBearer(auto_error=False)
SECRET_KEY = os.environ["SECRET_KEY"]
RAILS_JWT_SECRET_KEY = os.environ.get("RAILS_JWT_SECRET_KEY")
ALGORITHM = os.environ["ALGORITHM"]
ACCESS_TOKEN_EXPIRE_MINUTES = 300

ENV: str = os.environ.get("ENV", "local")
JWT_ENFORCED: str = os.environ.get("JWT_ENFORCED", "false").lower()


def get_token_from_cookie(stagingJwtToken: Optional[str] = Cookie(None)):
    return stagingJwtToken


def authenticate_cron(cron_auth_token: str, cron_auth_scheme: str):
    if not cron_auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )

    if cron_auth_scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme"
        )

    expected_token = os.environ.get("CRON_TOKEN")
    if cron_auth_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    return True


class UnAuthedMessage(BaseModel):
    detail: str = "Bearer token missing or unknown"


class RejectedAuthMessage(BaseModel):
    detail: str = "Forbidden"


class Permissions:

    def __init__(self, level: str):
        self.level = level

    def __call__(self, auth: Optional[str] = Depends(get_token_from_cookie)):
        if JWT_ENFORCED == "false":
            return True
        else:
            if not auth:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=UnAuthedMessage().detail
                )
            if self.level == "rails":
                try:
                    verify_rails_jwt = jwt.decode(auth, RAILS_JWT_SECRET_KEY, algorithms=[ALGORITHM])
                    if verify_rails_jwt:
                        return True
                except:
                    pass
            try:
                verify = jwt.decode(auth, SECRET_KEY, algorithms=[ALGORITHM])
                if verify and int(self.level) <= verify["admin"]:
                    return verify["client_uuid"]
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=RejectedAuthMessage().detail
                    )
            except PyJWTError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=UnAuthedMessage().detail
                )


async def check_jwt_client_with_client(jwt_client, client_uuid):
    if JWT_ENFORCED == "false":
        return True
    else:
        if jwt_client == client_uuid:
            return True
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=UnAuthedMessage().detail
            )


def check_token(credentials):
    try:
        verify = jwt.decode(credentials, SECRET_KEY, algorithms=[ALGORITHM])
        if verify:
            return True
    except:
        pass
    try:
        verify_rails_jwt = jwt.decode(credentials, RAILS_JWT_SECRET_KEY, algorithms=[ALGORITHM])
        if verify_rails_jwt:
            return True
        else:
            return False
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=UnAuthedMessage().detail
        )


async def get_token(
        auth: Optional[str] = Depends(get_token_from_cookie),
        cron_auth: Optional[str] = Depends(get_bearer_token)
):
    if auth:
        return check_token(auth)
    if cron_auth:
        return authenticate_cron(cron_auth.credentials, cron_auth.scheme)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized"
    )


def create_access_token(data: dict, expires_delta: timedelta | None = None, cron_job: bool = False):
    secret_key = RAILS_JWT_SECRET_KEY if cron_job else SECRET_KEY
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


async def access_token_creation(redeem, cron_job: bool = False):
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=redeem, expires_delta=access_token_expires, cron_job=cron_job
    )
    return {"access_token": access_token, "token_type": "Bearer"}


class AdminSwap:
    def __call__(
            self,
            auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token)
    ):
        try:
            verify = jwt.decode(auth.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            if verify and 2 == verify["admin"]:
                return verify
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=RejectedAuthMessage().detail
                )
        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=UnAuthedMessage().detail
            )


async def swap_client_uuid_in_jwt(decoded_jwt, new_client_uuid):
    decoded_jwt["client_uuid"] = new_client_uuid
    encoded_jwt = jwt.encode(decoded_jwt, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
