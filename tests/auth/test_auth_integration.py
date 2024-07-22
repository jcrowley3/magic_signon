import pytest
from unittest.mock import patch

# @pytest.mark.skipif(run_sparkpost(), reason="Don't want to test emails")
def test_get_login_credentials(mock_sparkpost, test_app, user):
    user_service = user['services']['email'][0]
    request_body = {
        "service_type": user_service['service_type'],
        "service_user_id": user_service['service_user_id']
    }
    if mock_sparkpost:
        with patch("app.actions.auth_actions.AuthActions.send_email_handler") as mock_send_email_handler:
            mock_send_email_handler.return_value = True
            login_creds = test_app.post(f"/v1/auth", json=request_body)
            mock_send_email_handler.assert_called_once()
    else:
        login_creds = test_app.post(f"/v1/auth", json=request_body)

    assert login_creds.status_code == 200
    login_creds = login_creds.json()
    assert "login_secret" in login_creds
    assert "login_token" in login_creds
    assert login_creds['service_type'] == user_service['service_type']
    assert login_creds['service_user_id'] == user_service['service_user_id']

def test_redeem_token(mock_sparkpost, test_app, user):
    user_service = user['services']['email'][0]
    request_body = {
        "service_type": user_service['service_type'],
        "service_user_id": user_service['service_user_id']
    }

    if mock_sparkpost:
        with patch("app.actions.auth_actions.AuthActions.send_email_handler") as mock_send_email_handler:
            mock_send_email_handler.return_value = True
            login_creds = test_app.post(f"/v1/auth", json=request_body)
            mock_send_email_handler.assert_called_once()
    else:
        login_creds = test_app.post(f"/v1/auth", json=request_body)

    assert login_creds.status_code == 200
    login_creds = login_creds.json()
    del login_creds['service_type']
    del login_creds['service_user_id']

    redeem_response = test_app.put(f"/v1/auth/redeem", json=login_creds)
    assert redeem_response.status_code == 200

def test_fail_get_login_credentials_missing_data(test_app):
    request_body = {
        "service_type": "email"
    }
    login_creds = test_app.post(f"/v1/auth", json=request_body)
    assert login_creds.status_code == 422
    assert login_creds.json()['detail'][0]['msg'] == "field required"
    assert login_creds.json()['detail'][0]['loc'][1] == "service_user_id"

def test_fail_get_login_credentails_service_doesnt_exist(test_app):
    request_body = {
        "service_type": "email",
        "service_user_id": "doesnt.exist@email.com"
    }
    login_creds = test_app.post(f"/v1/auth", json=request_body)
    assert login_creds.status_code == 400
    assert login_creds.json()['detail'] == 'No Matching Service Found.'
    
def test_fail_redeem_missing_credentials(test_app):
    request_body = {
        "login_secret": "super_secret"
    }
    redeem_response = test_app.put(f"/v1/auth/redeem", json=request_body)
    assert redeem_response.status_code == 422
    assert redeem_response.json()['detail'][0]['msg'] == "field required"
    assert redeem_response.json()['detail'][0]['loc'][1] == "login_token"

def test_fail_redeem_credentials_dont_match(test_app):
    request_body = {
        "login_secret": "super_secret",
        "login_token": "secret_token"
    }
    redeem_response = test_app.put(f"/v1/auth/redeem", json=request_body)
    assert redeem_response.status_code == 400
    assert redeem_response.json()["detail"] == "Login Credentials Don't Match."
