from app.models.base_models import BasePydantic


class CreateAuthModel(BasePydantic):
    service_type: str
    service_user_id: str


class RedeemAuthModel(BasePydantic):
    login_secret: str
    login_token: str


class AuthResponseModel(BasePydantic):
    login_secret: str
    login_token: str
    service_type: str
    service_user_id: str
