import os
import sys
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["APP_ENV"] = "development"
os.environ["APP_VERSION"] = "42"
os.environ["GIT_SHA"] = "abc1234"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import app as guestbook  # noqa: E402


def client():
    guestbook.app.config["TESTING"] = True
    return guestbook.app.test_client()


def test_health_reports_database_ok():
    response = client().get("/health")
    assert response.status_code == 200
    assert response.get_json()["db"] == "ok"


def test_version_reports_build_info():
    data = client().get("/version").get_json()
    assert data["version"] == "42"
    assert data["git_sha"] == "abc1234"


def test_sign_and_list_entry():
    c = client()
    c.post("/sign", data={"name": "Asha", "message": "Hello pipeline"})
    page = c.get("/").get_data(as_text=True)
    assert "Asha" in page and "Hello pipeline" in page


def test_rejects_empty_input():
    c = client()
    response = c.post("/sign", data={"name": "", "message": "x"})
    assert response.status_code == 302
    assert "x</div>" not in c.get("/").get_data(as_text=True)


def test_html_is_escaped():
    c = client()
    c.post("/sign", data={"name": "Bob", "message": "<script>alert(1)</script>"})
    page = c.get("/").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


def test_metrics_count_requests():
    c = client()
    c.get("/")
    text = c.get("/metrics").get_data(as_text=True)
    assert "guestbook_requests_total" in text
    assert 'endpoint="index"' in text
    assert 'guestbook_build_info{version="42",git_sha="abc1234"} 1' in text
