import copy

import pytest

from app import app
from services.tasks import (
    TASKS,
    create_task,
    get_task,
    list_tasks,
    process_order,
    update_task,
)
from utils.errors import NotFoundError, ValidationError


@pytest.fixture(autouse=True)
def reset_tasks():
    snapshot = copy.deepcopy(TASKS)
    yield
    TASKS.clear()
    TASKS.update(snapshot)

def test_process_order_valid():
    result = process_order(1)
    assert result["done"] is True

def test_process_order_invalid():
    with pytest.raises(NotFoundError):
        process_order(999)

def test_get_task_valid():
    result = get_task(2)
    assert result["title"] == "Write report"

def test_get_task_invalid():
    with pytest.raises(NotFoundError, match="Task not found"):
        get_task(999)

def test_get_task_not_found():
    with pytest.raises(NotFoundError):
        get_task(999)

def test_create_task_valid():
    result = create_task("Plan sprint", 1)
    assert result["title"] == "Plan sprint"
    assert result["user_id"] == 1
    assert result["done"] is False

@pytest.mark.parametrize("title", ["", "   "])
def test_create_task_empty_title(title):
    with pytest.raises(ValidationError):
        create_task(title, 1)

@pytest.mark.parametrize("user_id", [0, -1, "1", True])
def test_create_task_invalid_user_id(user_id):
    with pytest.raises(ValidationError):
        create_task("Plan sprint", user_id)

def test_create_task_default_priority():
    assert create_task("Plan sprint", 1)["priority"] == 3

def test_create_task_with_priority():
    assert create_task("Plan sprint", 1, 1)["priority"] == 1

@pytest.mark.parametrize("priority", [0, 6, "3", True, None])
def test_create_task_invalid_priority(priority):
    with pytest.raises(ValidationError):
        create_task("Plan sprint", 1, priority)

def test_update_task_priority():
    result = update_task(1, 5)
    assert result["priority"] == 5
    assert get_task(1)["priority"] == 5

@pytest.mark.parametrize("priority", [0, 6, "high", True, None])
def test_update_task_invalid_priority(priority):
    with pytest.raises(ValidationError):
        update_task(1, priority)

def test_update_task_not_found():
    with pytest.raises(NotFoundError):
        update_task(999, 2)

def test_list_tasks_no_filter():
    assert [t["id"] for t in list_tasks()] == [1, 2, 3]

def test_list_tasks_filter_matches_only():
    update_task(2, 1)
    assert [t["id"] for t in list_tasks(1)] == [2]

def test_list_tasks_filter_no_match():
    assert list_tasks(5) == []

def test_list_tasks_filter_digit_string():
    update_task(2, 1)
    assert [t["id"] for t in list_tasks("1")] == [2]

@pytest.mark.parametrize("priority", ["abc", "", "2.5", "-1", "0", 6])
def test_list_tasks_invalid_filter(priority):
    with pytest.raises(ValidationError):
        list_tasks(priority)

def test_get_tasks_route_filters():
    client = app.test_client()
    client.patch("/api/tasks/2", json={"priority": 1})
    response = client.get("/api/tasks?priority=1")
    assert response.status_code == 200
    assert [t["id"] for t in response.get_json()] == [2]

def test_get_tasks_route_invalid_filter():
    response = app.test_client().get("/api/tasks?priority=abc")
    assert response.status_code == 422

def test_post_task_route_default_priority():
    response = app.test_client().post("/api/tasks", json={"title": "Plan sprint", "user_id": 1})
    assert response.status_code == 201
    assert response.get_json()["priority"] == 3

def test_post_task_route_missing_title():
    response = app.test_client().post("/api/tasks", json={"user_id": 1})
    assert response.status_code == 422
    assert response.get_json()["error"] == "Invalid title: cannot be empty"

def test_post_task_route_missing_user_id():
    response = app.test_client().post("/api/tasks", json={"title": "Plan sprint"})
    assert response.status_code == 422
    assert response.get_json()["error"] == "Invalid user_id: must be a positive integer"

def test_post_task_route_no_body():
    response = app.test_client().post("/api/tasks")
    assert response.status_code == 422

def test_patch_task_route_missing_priority():
    response = app.test_client().patch("/api/tasks/1", json={})
    assert response.status_code == 422
    assert response.get_json()["error"] == "Invalid priority: is required"

def test_patch_task_route_updates_priority():
    client = app.test_client()
    response = client.patch("/api/tasks/1", json={"priority": 2})
    assert response.status_code == 200
    body = response.get_json()
    assert body["id"] == 1
    assert body["priority"] == 2
    saved = client.get("/api/tasks/1").get_json()
    assert saved["priority"] == 2

def test_patch_task_route_not_found():
    response = app.test_client().patch("/api/tasks/999", json={"priority": 2})
    assert response.status_code == 404

def test_get_task_route_not_found():
    response = app.test_client().get("/api/tasks/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Task not found"}

def test_existing_task_default_due_date():
    assert get_task(2)["due_date"] is None

def test_create_task_with_due_date():
    task = create_task("Pay rent", 1, 3, "2026-11-01")
    assert task["due_date"] == "2026-11-01"
    assert TASKS[task["id"]]["due_date"] == "2026-11-01"

def test_update_task_due_date():
    assert update_task(1, 3, "2026-12-25")["due_date"] == "2026-12-25"

@pytest.mark.parametrize("due_date", ["2026-13-01", "2026-02-30", "26-01-01",
                                      "20260101", "tomorrow", "", 20260101, True])
def test_create_task_invalid_due_date(due_date):
    with pytest.raises(ValidationError):
        create_task("Pay rent", 1, 3, due_date)

def test_update_task_invalid_due_date():
    with pytest.raises(ValidationError):
        update_task(1, 3, "2026-02-30")

def test_post_task_route_invalid_due_date():
    response = app.test_client().post(
        "/api/tasks", json={"title": "Pay rent", "user_id": 1, "due_date": "not-a-date"})
    assert response.status_code == 422
    assert response.get_json()["error"] == (
        "Invalid due_date: must be a date in YYYY-MM-DD format or null")

def test_post_task_route_with_due_date():
    response = app.test_client().post(
        "/api/tasks", json={"title": "Pay rent", "user_id": 1, "due_date": "2026-11-01"})
    assert response.status_code == 201
    assert response.get_json()["due_date"] == "2026-11-01"
