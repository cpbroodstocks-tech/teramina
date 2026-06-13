from unittest.mock import patch

from teramina.authentication.services.google_authentication_service import signed_token_using_firebase
from teramina.user.models.user_model import BetaAccessRequest, User


def test_firebase_login_without_seed_env_succeeds(monkeypatch):
    monkeypatch.delenv("SEEDER_FARM", raising=False)
    monkeypatch.delenv("SEEDER_POND", raising=False)
    monkeypatch.delenv("SEEDER_CYCLE", raising=False)

    with patch(
        "teramina.authentication.services.google_authentication_service.decode_token",
        return_value={
            "email": "new-user@teramina.io",
            "displayName": "New User",
            "photoURL": "",
        },
    ):
        status, response = signed_token_using_firebase("firebase-token")

    assert status == 200
    assert response.payload["token"]
    assert response.payload["refresh_token"]
    assert User.objects(email="new-user@teramina.io").first() is not None


def test_existing_firebase_user_is_checked_for_default_data():
    user = User(name="Existing Auth User", email="existing-auth-user@teramina.io").save()

    with (
        patch(
            "teramina.authentication.services.google_authentication_service.decode_token",
            return_value={
                "email": user.email,
                "displayName": user.name,
                "photoURL": "",
            },
        ),
        patch(
            "teramina.authentication.services.google_authentication_service.ensure_default_data_for_user"
        ) as ensure_default,
    ):
        status, _ = signed_token_using_firebase("firebase-token")

    assert status == 200
    ensure_default.assert_called_once_with(str(user.id))


def test_approved_beta_request_can_create_firebase_user():
    email = "approved-beta-user@example.com"
    BetaAccessRequest(email=email, status="approved").save()

    with patch(
        "teramina.authentication.services.google_authentication_service.decode_token",
        return_value={"email": email, "displayName": "Approved User", "photoURL": ""},
    ):
        status, response = signed_token_using_firebase("firebase-token")

    assert status == 200
    assert response.payload["token"]
    assert User.objects(email=email).first() is not None


def test_unapproved_beta_request_cannot_create_firebase_user():
    email = "pending-beta-user@example.com"
    BetaAccessRequest(email=email, status="pending").save()

    with patch(
        "teramina.authentication.services.google_authentication_service.decode_token",
        return_value={"email": email, "displayName": "Pending User", "photoURL": ""},
    ):
        status, response = signed_token_using_firebase("firebase-token")

    assert status == 400
    assert "not allowed" in response.message
    assert User.objects(email=email).first() is None
