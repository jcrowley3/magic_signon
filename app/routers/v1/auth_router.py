import os
from fastapi import APIRouter, Response, Body
from app.schemas.user_schemas import UserRedeemResponse
from app.schemas.auth_schemas import CreateAuthModel, RedeemAuthModel, AuthResponseModel
from app.actions.auth_actions import AuthActions
from app.utilities.auth_utils import access_token_creation

router = APIRouter(tags=["Auth"])

ENV: str = os.environ.get("ENV", "local")
JWT_ENFORCED: str = os.environ.get("JWT_ENFORCED", "false").lower()


@router.post("/auth", response_model=AuthResponseModel)
async def post_auth(
    create_auth_model: CreateAuthModel = Body(...)
):
    return_model = await AuthActions.post_auth_handler(create_auth_model)
    if JWT_ENFORCED == "false":
        return return_model
    else:
        prod_return = AuthResponseModel(
            login_token=return_model.login_token,
            login_secret=return_model.login_secret,
            service_type=return_model.service_type,
            service_user_id=return_model.service_user_id
        )
        return prod_return


@router.put("/auth/redeem", response_model=UserRedeemResponse)
async def put_auth(
    response: Response,
    redeem_auth_model: RedeemAuthModel = Body(...)
):
    redeem_return = await AuthActions.redeem_auth_handler(redeem_auth_model)
    user_model = dict(UserRedeemResponse.from_orm(redeem_return))
    client_uuid = await AuthActions.get_client_user_client_uuid(user_model.get("user_uuid"))
    user_model["client_uuid"] = client_uuid
    bearer_token = await access_token_creation(user_model)
    response.headers["Bearer"] = bearer_token["access_token"]

    return redeem_return
