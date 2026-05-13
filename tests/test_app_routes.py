"""
Tests for Flask route login flow, validation, and error handling.
"""
import sys

import pytest

sys.path.append("./")

# pylint: disable=import-error, wrong-import-position
from app import app
from modules.profile import User
from modules.workouts import Exercise, Routine


@pytest.fixture
def client(tmp_path, monkeypatch):
    """
    Create an isolated Flask test client with a sample user.
    """
    monkeypatch.chdir(tmp_path)

    sample_user = User("testuser")
    routine = Routine("Push")
    routine.add_exercise(Exercise("Bench", 2))
    sample_user.add_routine(routine)
    sample_user.to_json()
    sample_user.export_routines()

    app.config.update(TESTING=True, SECRET_KEY="test-secret")
    return app.test_client()


def login(client):
    """
    Store testuser in the browser session.
    """
    with client.session_transaction() as sess:
        sess["username"] = "testuser"


def test_protected_pages_redirect_without_login(client):
    """
    Protected pages send anonymous users back to login.
    """
    for path in ["/home", "/profile", "/plan", "/calendar"]:
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"] == "/"


def test_auth_logs_user_in(client):
    """
    Login stores the username in session and redirects to home.
    """
    response = client.post(
        "/auth", data={"username": "testuser"}, follow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/home"
    assert client.get("/home").status_code == 200


def test_missing_routine_redirects_instead_of_crashing(client):
    """
    Unknown routine names redirect instead of raising KeyError.
    """
    login(client)

    response = client.get("/logs/Monday/Unknown")

    assert response.status_code == 302
    assert response.headers["Location"] == "/logs/Monday"


def test_invalid_exercise_sets_redirects(client):
    """
    Exercise sets must be a positive integer.
    """
    login(client)

    response = client.get(
        "/submit-exercise/Push",
        query_string={"exercise-name": "Fly", "sets": "zero"},
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/add-exercise/Push"


def test_invalid_workout_day_redirects(client):
    """
    Workout days must match the Weekday enum.
    """
    login(client)

    response = client.post("/submit-days", data={"day": "NOT_A_DAY"})

    assert response.status_code == 302
    assert response.headers["Location"] == "/select-days"


def test_404_redirects_to_login(client):
    """
    Unknown URLs are handled by the app.
    """
    response = client.get("/page-that-does-not-exist")

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_frontend_demo_redirects_to_main_app(client):
    """
    The old React demo route no longer opens the mock prototype.
    """
    login(client)

    response = client.get("/frontend-demo")

    assert response.status_code == 302
    assert response.headers["Location"] == "/home"
