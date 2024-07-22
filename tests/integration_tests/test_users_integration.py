from fastapi.testclient import TestClient
import tests.testutil as utils


def test_get_all_users(test_app: TestClient):
    response = test_app.get("/v1/users")
    assert response.status_code == 200


def test_get_user(test_app: TestClient, user: dict):
    response = test_app.get(f"/v1/users/{user['uuid']}")
    assert response.status_code == 200


def test_create_user(user: dict):
    assert "uuid" in user
    assert user["first_name"] == utils.new_user["first_name"]


def test_update_user(test_app: TestClient, user: dict):
    response = test_app.put(f"/v1/users/{user['uuid']}", json=utils.update_user)
    assert response.status_code == 200
    assert response.json()["first_name"] == utils.update_user["first_name"]
    # assert response.json()["time_birthday"] == utils.update_user["time_birthday"]


def test_delete_user(test_app: TestClient, user: dict):
    response = test_app.delete(f"/v1/users/{user['uuid']}")
    assert response.status_code == 200
    assert response.json()["ok"] == True
    assert response.json()["Deleted"]["uuid"] == user["uuid"]