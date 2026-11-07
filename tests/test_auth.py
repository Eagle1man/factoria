from __future__ import annotations

import pytest
from factoria.auth.rbac import Principal
from factoria.auth.security import create_token, decode_token, hash_password, verify_password


def test_password_hash_roundtrip():
    stored = hash_password("s3cret")
    assert stored.startswith("scrypt$")
    assert verify_password("s3cret", stored) is True
    assert verify_password("wrong", stored) is False


def test_hash_has_unique_salt():
    assert hash_password("same") != hash_password("same")


def test_token_roundtrip():
    token, expires_in = create_token("user-1", "technologist", ttl_min=5)
    payload = decode_token(token)
    assert payload["sub"] == "user-1"
    assert payload["role"] == "technologist"
    assert expires_in == 300


def test_expired_token_rejected():
    token, _ = create_token("user-1", "technologist", ttl_min=-1)
    with pytest.raises(Exception):
        decode_token(token)


def test_tampered_token_rejected():
    token, _ = create_token("user-1", "technologist")
    with pytest.raises(Exception):
        decode_token(token + "x")


@pytest.mark.parametrize(
    ("role", "permission", "expected"),
    [
        ("technologist", "read", True),
        ("auditor", "audit_read", True),
        ("production_specialist", "audit_read", False),
        ("employee", "operator", False),
        ("production_specialist", "operator", True),
        ("unknown", "read", False),
    ],
)
def test_permissions(role, permission, expected):
    assert Principal(user_id="u", role=role).can(permission) is expected
