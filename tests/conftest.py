import os
import pytest
from fastapi.testclient import TestClient
import tests.testutil as util

os.environ["TEST_MODE"] = "True"

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def mock_sparkpost():
    return True


def err_msg(response):
    return f"Response[{response.status_code}]: {response.text} "


def delete_user(test_app: TestClient, user_uuid: str, service_uuid: str):
    try:
        service_response = test_app.delete(f"/v1/users/{user_uuid}/services/{service_uuid}")
        user_response = test_app.delete(f"/v1/users/{user_uuid}")
        assert service_response.status_code == 200
        assert user_response.status_code == 200
        return
    except:
        if service_response.status_code == 200:
            assert service_response.status_code == 200
            assert user_response.status_code == 404
        elif user_response.status_code == 200:
            assert service_response.status_code == 404
            assert user_response.status_code == 200


@pytest.fixture(scope="module")
def test_app():
    client = TestClient(app)
    yield client


@pytest.fixture(scope="function")
def user(test_app: TestClient):
    try:
        user = test_app.post("/v1/users?expand_services=true", json=util.new_user).json()
        yield user
    except:
        raise Exception("User Creation Failed")
    finally:
        if user is not None:
            delete_user(test_app, user["uuid"], user["services"]["email"][0]["uuid"])


@pytest.fixture(scope="function")
def service(user):
    yield user["services"]["email"][0]
