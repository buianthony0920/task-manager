import pytest
from services.tasks import process_order, get_task, create_task
from utils.errors import NotFoundError, ValidationError

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
    with pytest.raises(Exception):
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
