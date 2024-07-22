import csv
import codecs
import json

from collections import namedtuple
from fastapi import UploadFile, File


class HelperActions:
    default_email_types = {"Primary Work Email", "primary_work_email", "work_email", "personal_email", "email_address", "email"}
    default_cell_types = {"Primary Cell Number", "primary_cell_number", "cell_number", "cell", "cell_phone"}

    @staticmethod
    async def make_username(first, last):
        first = first.lower()
        last = last.lower()
        return f"{first}{last}"

    @staticmethod
    async def process_csv(csv_file: UploadFile = File(...)):
        csv_reader = csv.DictReader(codecs.iterdecode(csv_file.file, "utf-8"))
        csv_items = []
        for row in csv_reader:
            csv_items.append(json.loads(json.dumps(row)))
        return csv_items

    @staticmethod
    async def check_if_dict(obj):
        if hasattr(obj, "dict"):
            obj = obj.dict()
        return obj

    ServiceType = namedtuple("ServiceType", ["type", "value"])

    @classmethod
    async def get_email_from_header(cls, data: dict, type=None):
        data = await cls.check_if_dict(data)
        email_types: set = cls.default_email_types
        if type and type not in email_types:
            return None
        elif type and type in email_types:
            email_types = {type}
        email_type = list(email_types.intersection(data))
        if bool(email_type):
            return cls.ServiceType(type="email", value=data.get(email_type[0]))
        else:
            return None

    @classmethod
    async def get_cell_from_header(cls, data: dict, type=None):
        data = await cls.check_if_dict(data)
        cell_types: set = cls.default_cell_types
        if type and type not in cell_types:
            return None
        elif type and type in cell_types:
            cell_types = {type}
        cell_type = list(cell_types.intersection(data))
        if bool(cell_type):
            cell_value = data.get(cell_type[0])
            if isinstance(cell_value, int):
                cell_value = str(cell_value)
            else:
                cell_value = cell_value.replace("-", "").replace("(", "").replace(")", "").strip()
            return cls.ServiceType(type="cell", value=cell_value)
        else:
            return None

    @classmethod
    async def get_fname_from_header(cls, data: dict):
        data = await cls.check_if_dict(data)
        name_types = ["Legal First Name", "legal_first_name", "firstname", "first_name"]
        name_type = list(set(name_types).intersection(data))
        if bool(name_type):
            return data.get(name_type[0])
        else:
            raise Exception

    @classmethod
    async def get_lname_from_header(cls, data: dict):
        data = await cls.check_if_dict(data)
        name_types = ["Legal Last Name", "legal_last_name", "lastname", "last_name"]
        name_type = list(set(name_types).intersection(data))
        if bool(name_type):
            return data.get(name_type[0])
        else:
            raise Exception

    @classmethod
    async def get_manager_uuid(cls, data: dict):
        data = await cls.check_if_dict(data)
        name_types = ["manager_uuid", "Manager ID", "Manager UUID", "manager_id"]
        name_type = list(set(name_types).intersection(data))
        if bool(name_type):
            return data.get(name_type[0])
        else:
            return
            # raise Exception

    @classmethod
    async def get_employee_id(cls, data: dict):
        data = await cls.check_if_dict(data)
        name_types = ["employee id", "employee_id", "Employee ID"]
        name_type = list(set(name_types).intersection(data))
        if bool(name_type):
            return data.get(name_type[0])
        else:
            return
            # raise Exception

    @classmethod
    async def get_title(cls, data: dict):
        data = await cls.check_if_dict(data)
        name_types = ["title", "business title", "Business Title", "Title"]
        name_type = list(set(name_types).intersection(data))
        if bool(name_type):
            return data.get(name_type[0])
        else:
            return
            # raise Exception

    @classmethod
    async def get_department(cls, data: dict):
        data = await cls.check_if_dict(data)
        name_types = ["department", "Department"]
        name_type = list(set(name_types).intersection(data))
        if bool(name_type):
            return data.get(name_type[0])
        else:
            return
            # raise Exception

    @classmethod
    async def get_active(cls, data: dict):
        data = await cls.check_if_dict(data)
        name_types = ["active", "Active"]
        name_type = list(set(name_types).intersection(data))
        if bool(name_type):
            return data.get(name_type[0])
        else:
            return
            # raise Exception

    @classmethod
    async def get_admin(cls, data: dict):
        data = await cls.check_if_dict(data)
        name_types = ["admin", "Admin"]
        name_type = list(set(name_types).intersection(data))
        if bool(name_type):
            return data.get(name_type[0])
        else:
            return 1
            # raise Exception
