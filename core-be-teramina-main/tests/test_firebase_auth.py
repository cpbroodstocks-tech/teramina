from unittest.mock import patch

from teramina.authentication.services.google_authentication_service import signed_token_using_firebase
from teramina.user.models.user_model import User


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
