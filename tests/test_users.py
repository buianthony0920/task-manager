import copy

import pytest

from app import app
from services.users import (
    USERS,
    get_notification_pref,
    get_user,
    list_users,
    set_notification_pref,
)
from utils.errors import NotFoundError, ValidationError


@pytest.fixture(autouse=True)
def reset_users():
    snapshot = copy.deepcopy(USERS)
    yield
    USERS.clear()
    USERS.update(snapshot)

def test_get_notification_pref_default():
    assert get_notification_pref(1) == {"user_id": 1, "notification_pref": "none"}

@pytest.mark.parametrize("pref", ["email", "sms"])
def test_set_notification_pref_valid(pref):
    result = set_notification_pref(1, pref)
    assert result == {"user_id": 1, "notification_pref": pref}
    assert get_notification_pref(1)["notification_pref"] == pref

@pytest.mark.parametrize("pref", ["fax", None])
def test_set_notification_pref_invalid(pref):
    with pytest.raises(ValidationError):
        set_notification_pref(1, pref)
    assert get_notification_pref(1)["notification_pref"] == "none"

def test_get_notification_pref_not_found():
    with pytest.raises(NotFoundError, match="User not found"):
        get_notification_pref(999)

def test_set_notification_pref_not_found():
    with pytest.raises(NotFoundError, match="User not found"):
        set_notification_pref(999, "email")

def test_list_users_includes_notification_pref():
    users = list_users()
    assert [u["id"] for u in users] == [1, 2]
    assert all(u["notification_pref"] == "none" for u in users)

def test_get_user_includes_notification_pref():
    assert get_user(1)["notification_pref"] == "none"

def test_get_users_route():
    response = app.test_client().get("/api/users")
    assert response.status_code == 200
    body = response.get_json()
    assert [u["id"] for u in body] == [1, 2]
    assert all("notification_pref" in u for u in body)

def test_get_notification_pref_route():
    response = app.test_client().get("/api/users/1/notifications")
    assert response.status_code == 200
    assert response.get_json() == {"user_id": 1, "notification_pref": "none"}

def test_patch_notification_pref_route_valid():
    client = app.test_client()
    response = client.patch("/api/users/1/notifications", json={"notification_pref": "email"})
    assert response.status_code == 200
    assert response.get_json() == {"user_id": 1, "notification_pref": "email"}
    saved = client.get("/api/users/1/notifications").get_json()
    assert saved["notification_pref"] == "email"

def test_patch_notification_pref_route_invalid():
    response = app.test_client().patch("/api/users/1/notifications",
                                       json={"notification_pref": "fax"})
    assert response.status_code == 422
    assert response.get_json() == {
        "error": "Invalid notification_pref: must be one of email, sms, none"
    }

def test_patch_notification_pref_route_not_found():
    response = app.test_client().patch("/api/users/999/notifications",
                                       json={"notification_pref": "email"})
    assert response.status_code == 404
    assert response.get_json() == {"error": "User not found"}
