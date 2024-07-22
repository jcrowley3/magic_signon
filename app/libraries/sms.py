import os
from app.schemas.message_schemas import MessageModel
from app.actions.message_template_actions import MessageTemplateActions
from app.models.user_service_models import UserServiceModelDB
from twilio.rest import Client


ACCOUNT_TOKEN = os.environ["ACCOUNT_TOKEN"]
ACCOUNT_SID = os.environ["ACCOUNT_SID"]
TWILIO_FROM = os.environ["TWILIO_FROM"]
TwilioClient = Client(ACCOUNT_SID, ACCOUNT_TOKEN)


async def send_sms_worker(user_service: UserServiceModelDB):
    message = TwilioClient.messages.create(
        to="+1" + user_service.service_user_id,
        from_=TWILIO_FROM,
        body=user_service.login_token
    )

    return message.sid


async def send_message_text(message: dict, recipient: dict, service_id: str):
    message = TwilioClient.messages.create(
        to="+1" + service_id,
        from_=TWILIO_FROM,
        body=await get_text_message_body(message, recipient)
    )
    return {
            "recipient": f"{await MessageTemplateActions.get_recipient_first_name(recipient)} {await MessageTemplateActions.get_recipient_last_name(recipient)}",
            "user_uuid": recipient["user"].uuid,
            "message.sid": message.sid
        }


async def get_text_message_body(message: MessageModel, recipient: str):
    return await {
        # TODO: create template for auth text message to send
    }[message["message"].message_type](message, recipient)
