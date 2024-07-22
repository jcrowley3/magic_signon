from typing import Optional
from app.utilities.enums import ChannelType, MessageType, Status
from app.models.base_models import BasePydantic


class MessageModel(BasePydantic):
    uuid: Optional[str]
    name: Optional[str]
    message_9char: Optional[str]
    body: Optional[str]
    channel: Optional[ChannelType]
    message_uuid: Optional[str]
    client_uuid: Optional[str]
    program_9char: Optional[str]
    segment_9char: Optional[str]
    message_type: Optional[MessageType]
    status: Optional[Status]
    time_created: Optional[int]
    time_updated: Optional[int]
