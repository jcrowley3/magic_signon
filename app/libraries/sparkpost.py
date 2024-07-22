import os
from fastapi import HTTPException
from app.models.user_service_models import UserServiceModelDB
from app.schemas.user_service_schemas import UserServiceCreate
from app.schemas.message_schemas import MessageModel
from app.models.user_models import UserModel
from app.actions.message_template_actions import MessageTemplateActions
from sparkpost import SparkPost
from sparkpost.exceptions import SparkPostAPIException


SPARKPOST_KEY = os.environ["SPARKPOST_KEY"]
sp = SparkPost(SPARKPOST_KEY)

# The BASE_URL is where the user will be sent to when they click the link in the email sent to them
BASE_URL = os.getenv("BASE_URL", "https://www.google.com/")
REDEEM_URL = f"{BASE_URL}auth/verify-email-token?token="


async def send_auth_email(user_service: UserServiceModelDB):
    response = sp.transmissions.send(
        use_sandbox=False,
        recipients=[user_service.service_user_id],
        html=await MessageTemplateActions.create_auth_email(REDEEM_URL + user_service.login_token),
        from_email="jcrowley317@gmail.com",
        subject="magic_signon Login Token"
    )
    return response


async def send_add_service_code_email(user_service: UserServiceCreate, auth_code):
    try:
        response = sp.transmissions.send(
            use_sandbox=False,
            recipients=[user_service.service_user_id],
            html=await MessageTemplateActions.create_auth_code_add_service_email(auth_code),
            from_email="jcrowley317@gmail.com",
            subject="magic_signon Authorization Code to Add Service",
        )
        return response
    except SparkPostAPIException as e:
        raise HTTPException(status_code=e.status, detail=e.errors)




async def send_message_email(message_details: dict, recipient: UserModel, recipient_email: str):
    response = sp.transmissions.send(
        use_sandbox=False,
        recipients=[recipient_email],
        html=await get_email_body(message_details, recipient),
        from_email="jcrowley317@gmail.com",
        subject="magic_signon Message",
    )
    return response


async def get_email_body(message: MessageModel, recipient: str,):
    return await {
        # 1: MessageTemplateActions.create_welcome_email,
        2: MessageTemplateActions.create_auth_email,
        # 3: MessageTemplateActions.create_award_email,
        # 4: MessageTemplateActions.create_anniversary_email,
        # 5: MessageTemplateActions.create_birthday_email,
        # 6: MessageTemplateActions.create_redeem_email,
        # 7: MessageTemplateActions.create_message_email,
        # 8: MessageTemplateActions.create_reminder_email,
        # 9: MessageTemplateActions.create_survey_email
    }[message["message"].message_type](message, recipient)
