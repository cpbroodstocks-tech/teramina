# pylint: disable=redefined-outer-name
"""Unit tests for AuthBearer JWT authentication."""

import os
from datetime import datetime, timezone, timedelta

import jwt
import pytest

# conftest.py handles Django + mongomock setup

from teramina.authentication.auth_bearer import AuthBearer
from teramina.user.models.user_model import User

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "test-jwt-secret")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_token(user_id, email="test@farm.io", name="Farmer",
                exp_delta=timedelta(minutes=120), secret=None):
    payload = {
        "exp": datetime.now(timezone.utc) + exp_delta,
        "iat": datetime.now(timezone.utc),
        "data": {"id": str(user_id), "email": email, "name": name},
    }
    return jwt.encode(payload, secret or JWT_SECRET, algorithm="HS256")


def _make_expired_token(user_id):
    return _make_token(user_id, exp_delta=timedelta(seconds=-1))


@pytest.fixture(autouse=True)
def clean_users():
    User.drop_collection()
    yield
    User.drop_collection()


@pytest.fixture()
def user():
    u = User(name="Farmer", email="test@farm.io")
    u.save()
    return u


@pytest.fixture()
def bearer():
    return AuthBearer()


@pytest.fixture()
def mock_request():
    from unittest.mock import MagicMock
    return MagicMock()


# ---------------------------------------------------------------------------
# authenticate()
# ---------------------------------------------------------------------------

class TestAuthenticate:
    def test_valid_token_returns_token(self, bearer, mock_request, user):
        token = _make_token(user.id)
        result = bearer.authenticate(mock_request, token)
        assert result == token

    def test_expired_token_returns_false(self, bearer, mock_request, user):
        token = _make_expired_token(user.id)
        result = bearer.authenticate(mock_request, token)
        assert result is False

    def test_wrong_secret_returns_false(self, bearer, mock_request, user):
        token = _make_token(user.id, secret="wrong-secret")
        result = bearer.authenticate(mock_request, token)
        assert result is False

    def test_malformed_token_returns_false(self, bearer, mock_request):
        result = bearer.authenticate(mock_request, "not.a.valid.token")
        assert result is False

    def test_user_not_found_returns_none(self, bearer, mock_request):
        # Token with a valid-looking but non-existent user ID
        token = _make_token("507f1f77bcf86cd799439099")
        result = bearer.authenticate(mock_request, token)
        assert result is None

    def test_empty_token_returns_false(self, bearer, mock_request):
        result = bearer.authenticate(mock_request, "")
        assert result is False


# ---------------------------------------------------------------------------
# authenticate_with_refresh_token()
# ---------------------------------------------------------------------------

class TestAuthenticateWithRefreshToken:
    def test_valid_refresh_returns_new_token_pair(self, bearer, mock_request, user):
        token = _make_token(user.id, exp_delta=timedelta(days=7))
        result = bearer.authenticate_with_refresh_token(mock_request, token)
        assert isinstance(result, dict)
        assert "token" in result
        assert "refresh_token" in result

    def test_new_access_token_is_decodable(self, bearer, mock_request, user):
        token = _make_token(user.id, exp_delta=timedelta(days=7))
        result = bearer.authenticate_with_refresh_token(mock_request, token)
        decoded = jwt.decode(result["token"], JWT_SECRET, algorithms=["HS256"])
        assert decoded["data"]["id"] == str(user.id)

    def test_new_access_token_expires_in_120min(self, bearer, mock_request, user):
        token = _make_token(user.id, exp_delta=timedelta(days=7))
        result = bearer.authenticate_with_refresh_token(mock_request, token)
        decoded = jwt.decode(result["token"], JWT_SECRET, algorithms=["HS256"])
        exp = decoded["exp"]
        iat = decoded["iat"]
        assert 119 * 60 <= (exp - iat) <= 121 * 60

    def test_expired_refresh_returns_false(self, bearer, mock_request, user):
        token = _make_expired_token(user.id)
        result = bearer.authenticate_with_refresh_token(mock_request, token)
        assert result is False

    def test_user_not_found_returns_false(self, bearer, mock_request):
        token = _make_token("507f1f77bcf86cd799439099", exp_delta=timedelta(days=7))
        result = bearer.authenticate_with_refresh_token(mock_request, token)
        assert result is False

    def test_malformed_token_returns_false(self, bearer, mock_request):
        result = bearer.authenticate_with_refresh_token(mock_request, "garbage")
        assert result is False


# ---------------------------------------------------------------------------
# authenticate_returned_email()
# ---------------------------------------------------------------------------

class TestAuthenticateReturnedEmail:
    def test_valid_token_returns_email_and_id(self, bearer, mock_request, user):
        token = _make_token(user.id)
        result = bearer.authenticate_returned_email(mock_request, token)
        assert result == (user.email, str(user.id))

    def test_expired_token_returns_false(self, bearer, mock_request, user):
        token = _make_expired_token(user.id)
        result = bearer.authenticate_returned_email(mock_request, token)
        assert result is False

    def test_user_not_found_returns_none(self, bearer, mock_request):
        token = _make_token("507f1f77bcf86cd799439099")
        result = bearer.authenticate_returned_email(mock_request, token)
        assert result is None

    def test_malformed_token_returns_false(self, bearer, mock_request):
        result = bearer.authenticate_returned_email(mock_request, "garbage")
        assert result is False
