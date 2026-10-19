import pytest

from app import app
from services.tags import TAGS


@pytest.fixture(autouse=True)
def reset_tags():
    saved = dict(TAGS)
    yield
    TAGS.clear()
    TAGS.update(saved)


def test_create_tag_route_returns_201():
    client = app.test_client()
    resp = client.post("/api/tags", json={"name": "urgent"})
    assert resp.status_code == 201
    assert resp.get_json()["name"] == "urgent"
