from fastapi.testclient import TestClient
import tests.testutil as utils


def test_get_all_services(test_app: TestClient, service: dict):
	response = test_app.get(f"/v1/users/{service['user_uuid']}/services")
	assert response.status_code == 200
	assert response.json()['email'][0]['user_uuid'] == service['user_uuid']


def test_get_service(test_app: TestClient, service: dict):
	response = test_app.get(
		f"/v1/users/{service['user_uuid']}/services/{service['uuid']}"
	)
	assert response.status_code == 200
	assert response.json()['uuid'] == service['uuid']

def test_create_user_service(test_app: TestClient, user: dict):
	try:
		response = test_app.post(
		f"/v1/users/{user['uuid']}/services", json=utils.new_service
		)
		assert response.status_code == 200
		assert response.json()['user_uuid'] == user['uuid']
	finally:
		deleted_service = test_app.delete(f"/v1/users/{user['uuid']}/services/{response.json()['uuid']}")
		assert deleted_service.status_code == 200
	

def test_update_user_service(test_app: TestClient, service: dict):
	response = test_app.put(
		f"/v1/users/{service['user_uuid']}/services/{service['uuid']}",
		json=utils.update_service
	)
	assert response.status_code == 200
	assert response.json()['service_user_name'] == "testuser"

def test_delete_user_service(test_app: TestClient, service: dict):
	response = test_app.delete(
		f"/v1/users/{service['user_uuid']}/services/{service['uuid']}"
	)
	assert response.status_code == 200
	assert response.json()["ok"] == True