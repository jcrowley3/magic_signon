import os
import random
import hashlib
import uuid
from time import time
from datetime import datetime, timezone
from dateutil import parser
from app.utilities import PositiveNumbers


class GenerateUUID:
    @staticmethod
    def hex():
        return uuid.uuid4().hex

    @staticmethod
    def bytes():
        return uuid.uuid4().bytes

    @staticmethod
    def int():
        return uuid.uuid4().int

    @staticmethod
    def default():
        return uuid.uuid4()


def _encodeutf8(item):
    return item.encode("utf-8")


def SHA224Hash(input_string=None):
    input = _encodeutf8(
        "".join([
            str(x) for x in [
                os.getpid(),
                random.Random().randint(0, 100000000),
                datetime.now(),
                input_string if input_string else "x"
            ]
        ])
    )
    return hashlib.sha224(input).hexdigest()


def new_9char():
    """Generate a new 9-character ID string.

    :returns: str: 9-character string
    """
    generator = PositiveNumbers.PositiveNumbers(size=9)
    uuid_time = int(str(time()).replace(".", "")[:16])
    char_9 = generator.encode(uuid_time)
    return char_9


def convert_date_to_int(date):
    if date is None or isinstance(date, int):
        return date

    elif isinstance(date, str):
        if date.isdigit():
            return int(date)

        # Attempt to parse the date string with timezone information
        try:
            date_obj = parser.parse(date)
            date_obj_utc = date_obj.astimezone(timezone.utc)
            return int(date_obj_utc.timestamp())
        except (ValueError, TypeError):
            pass

        # Fallback to predefined formats if the above parsing fails
        formats = ["%m/%d/%Y", "%Y/%m/%d", "%m/%d/%y", "%Y-%m-%d"]
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date, fmt)
                epoch_time = int(date_obj.replace(tzinfo=timezone.utc).timestamp())
                return epoch_time
            except ValueError:
                pass
    else:
        return None
    # raise ValueError(f"Invalid date format: {date}")


def convert_int_to_date_string(date_int):
    if date_int is None or isinstance(date_int, str):
        return date_int
    return datetime.fromtimestamp(date_int).strftime("%m/%d/%Y")
