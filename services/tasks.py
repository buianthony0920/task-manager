import re
from datetime import date

from utils.errors import NotFoundError, ValidationError

TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Buy groceries",  "done": False, "user_id": 1, "priority": 3, "due_date": None},
    2: {"id": 2, "title": "Write report",   "done": False, "user_id": 1, "priority": 3, "due_date": None},
    3: {"id": 3, "title": "Call dentist",   "done": True,  "user_id": 2, "priority": 3, "due_date": None},
}

def _validate_priority(priority: int) -> None:
    """Check that a priority value is allowed.

    Args:
        priority: The priority to check, 1 (urgent) to 5 (low).

    Raises:
        ValidationError: If priority is not an integer from 1 to 5.
    """
    if not isinstance(priority, int) or isinstance(priority, bool) or not 1 <= priority <= 5:
        raise ValidationError("priority", "must be an integer from 1 to 5")

def _validate_due_date(due_date: str | None) -> None:
    """Check that a due date value is allowed.

    Args:
        due_date: The due date to check, an ISO date string "YYYY-MM-DD" or None.

    Raises:
        ValidationError: If due_date is not None or a real date in YYYY-MM-DD form.
    """
    if due_date is None:
        return
    if not isinstance(due_date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", due_date,
                                                         re.ASCII):
        raise ValidationError("due_date", "must be a date in YYYY-MM-DD format or null")
    try:
        date.fromisoformat(due_date)
    except ValueError:
        raise ValidationError("due_date", "must be a date in YYYY-MM-DD format or null") from None

def process_order(task_id: int) -> dict:
    """Mark a task as done.

    Args:
        task_id: The unique identifier for the task.

    Returns:
        The updated task record as a dictionary.

    Raises:
        NotFoundError: If no task exists with the given ID.
    """
    if task_id not in TASKS:
        raise NotFoundError("Task")
    task = TASKS[task_id]
    task["done"] = True
    return task

def get_task(task_id: int) -> dict:
    """Retrieve a task by ID.

    Args:
        task_id: The unique identifier for the task.

    Returns:
        The task record as a dictionary.

    Raises:
        NotFoundError: If no task exists with the given ID.
    """
    if task_id not in TASKS:
        raise NotFoundError("Task")
    return TASKS[task_id]

def create_task(title: str, user_id: int, priority: int = 3,
                due_date: str | None = None) -> dict:
    """Create a new task.

    Args:
        title: The task's title.
        user_id: The ID of the user who owns the task.
        priority: 1 (urgent) to 5 (low). Defaults to 3.
        due_date: An ISO date string "YYYY-MM-DD", or None. Defaults to None.

    Returns:
        The newly created task record.

    Raises:
        ValidationError: If title is empty, user_id is not a positive integer,
            priority is not an integer from 1 to 5, or due_date is not a
            YYYY-MM-DD date or None.
    """
    if not isinstance(title, str) or not title.strip():
        raise ValidationError("title", "cannot be empty")
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id < 1:
        raise ValidationError("user_id", "must be a positive integer")
    _validate_priority(priority)
    _validate_due_date(due_date)
    new_id = max(TASKS.keys()) + 1
    TASKS[new_id] = {"id": new_id, "title": title, "done": False, "user_id": user_id,
                     "priority": priority, "due_date": due_date}
    return TASKS[new_id]

def list_tasks(priority: int | str | None = None) -> list[dict]:
    """List tasks, optionally filtered by priority.

    Args:
        priority: Only return tasks with this priority, 1 (urgent) to 5 (low).
            A digit string such as "2" (from a query string) is accepted.
            None returns every task.

    Returns:
        The matching task records as a list of dictionaries.

    Raises:
        ValidationError: If priority is not an integer from 1 to 5.
    """
    if priority is None:
        return list(TASKS.values())
    if isinstance(priority, str):
        if not (priority.isascii() and priority.isdigit()):
            raise ValidationError("priority", "must be an integer from 1 to 5")
        priority = int(priority)
    _validate_priority(priority)
    return [t for t in TASKS.values() if t["priority"] == priority]

def update_task(task_id: int, priority: int, due_date: str | None = None) -> dict:
    """Update a task's priority and, optionally, its due date.

    Args:
        task_id: The unique identifier for the task.
        priority: The new priority, 1 (urgent) to 5 (low).
        due_date: The new due date as "YYYY-MM-DD". None leaves the
            current due date unchanged.

    Returns:
        The updated task record as a dictionary.

    Raises:
        NotFoundError: If no task exists with the given ID.
        ValidationError: If priority is missing or not an integer from 1 to 5,
            or due_date is not a YYYY-MM-DD date or None.
    """
    if task_id not in TASKS:
        raise NotFoundError("Task")
    if priority is None:
        raise ValidationError("priority", "is required")
    _validate_priority(priority)
    _validate_due_date(due_date)
    TASKS[task_id]["priority"] = priority
    if due_date is not None:
        TASKS[task_id]["due_date"] = due_date
    return TASKS[task_id]
