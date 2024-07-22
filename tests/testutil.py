from collections import namedtuple
from app.utilities.utils import GenerateUUID

company_gid = str(GenerateUUID.default())
account_gid = str(GenerateUUID.default())

new_user_account = {
    "account_id": 20,
    "first_name": "Billy",
    "last_name": "Bob",
    "email_address": "Billy.Bob@thornton.com",
    "phone_number": "+1234567890",
    "company_id": 10,
    "company_gid": company_gid,
    "account_gid": account_gid,
    "employee_id": 1234,
    "manager_id": [28],
    "latitude": None,
    "longitude": None,
    "time_birthday": "1988-12-22T05:51:59.444336-08:00",
    "hired_on": "2022-12-22T05:51:59.444336-08:00",
    "deactivated_at": None
}

updated_account = {
    "account_id": 20,
    "first_name": "John",
    "last_name": "Doe",
    "email_address": "Billy.Bob@thornton.com",
    "manager_id": [28],
    "employee_id": 1234,
    "company_id": 10,
    "company_gid": company_gid,
    "account_gid": account_gid,

}

new_user_account_with_plus_sign = {
    "account_id": 10,
    "first_name": "Jimmy",
    "last_name": "Joe",
    "email_address": "Jimmy.Joe+spam+watch@thornton.com",
    "phone_number": "+1234567810",
    "company_id": 50
}

uuid_names = [
    "user_uuid",
    "first_client_uuid",
    "second_client_uuid",
    "client_user_uuid",
    "program_uuid",
    "award_uuid"
]
Test_IDs = namedtuple("Test_ID", uuid_names)
test_uuids = Test_IDs(*[GenerateUUID.hex() for _ in uuid_names])

new_user = {
    "uuid": test_uuids.user_uuid,
    "client_uuid": test_uuids.first_client_uuid,
    "first_name": "Test",
    "last_name": "User",
    "work_email": "test.user@sparkpostbox.com",
    "cell_number": "(579)741-2145",
    "hire_date": "1/1/2015",
    "continuous_service_date": "1/1/2015",
    "employee_id": 1139,
    "manager_id": 200405,
    "cost_center_id": 21121,
    "worker_type": "Employee",
    "department": "Engineering",
    "manager": "Jim W",
    "location": "Seattle",
    "business_title": "magic_signon Engineer",
    "department_leader": 200405,
    "admin": 2
}

new_user_2 = {
    "uuid": test_uuids.user_uuid,
    "client_uuid": test_uuids.first_client_uuid,
    "first_name": "Test_2",
    "last_name": "User_2",
    "work_email": "test.user2@sparkpostbox.com",
    "cell_number": "(579)741-2142",
    "hire_date": "1/1/2015",
    "continuous_service_date": "1/1/2015",
    "employee_id": 1139,
    "manager_id": 200405,
    "cost_center_id": 21121,
    "worker_type": "Employee",
    "department": "Engineering",
    "manager": "Jim W",
    "location": "Seattle",
    "business_title": "magic_signon Engineer",
    "department_leader": 200405,
    "admin": 2
}

migrate_service = {
    "service_type": "email",
    "service_user_id": "test.user@sparkpostbox.com",
    "auth_code": None
}

update_user = {
    "first_name": "Test_Update",
    "last_name": "User_Update",
    "latidude": 33812263,
    "longitude": -117920126,
    # "time_birdthday": 1420070400,
    "admin": 1
}

new_service = {
    "service_type": "email",
    "service_user_id": "test.user2@sparkpostbox.com"
}

update_service = {
    "service_access_token": "test",
    "service_access_secret": "test",
    "service_refresh_token": "test"
}

single_client = {
    "uuid": test_uuids.first_client_uuid,
    "name": "test",
    "description": "test",
    "status": 0
}

list_of_clients = [
    {
        "uuid": test_uuids.first_client_uuid,
        "name": "client one",
        "description": "first client",
        "status": 0
    },
    {
        "uuid": test_uuids.second_client_uuid,
        "name": "client two",
        "description": "second client",
        "status": 0
    }
]
new_client_user = {
    "uuid": test_uuids.client_user_uuid,
    "client_uuid": test_uuids.first_client_uuid,
    "email_address": "test.user123@testclient.com",
    "first_name": "Test",
    "last_name": "User",
    "admin": 1
}

update_client_user = {
    "title": "test",
    "department": "test"
}
