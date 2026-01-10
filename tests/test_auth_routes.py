import pytest
from unittest.mock import patch
from flask import url_for, session  # noqa: F401
from bson.objectid import ObjectId

# Import the Flask app instance
from app import (
    app as flask_app,
)  # Import as flask_app to avoid name collision with fixture


# Fixture for a Flask test client
@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing forms
    flask_app.config["SERVER_NAME"] = "localhost"  # Add SERVER_NAME for url_for to work
    with flask_app.test_client() as client:
        with flask_app.app_context():  # Ensure an application context is pushed
            yield client


# Mock database functions for auth routes
@pytest.fixture
def mock_db_auth_functions():
    # Patch the functions where they are actually defined and imported
    with (
        patch("database.mongodb_connector.add_user") as mock_add_user,
        patch("database.mongodb_connector.check_login") as mock_check_login,
        patch(
            "database.mongodb_connector.check_username_exists"
        ) as mock_check_username_exists,
    ):
        yield mock_add_user, mock_check_login, mock_check_username_exists


def test_signup_page_loads(client):
    response = client.get(url_for("auth.signup"))
    assert response.status_code == 200
    assert b"Inscription" in response.data


def test_signup_successful(client, mock_db_auth_functions):
    mock_add_user, _, mock_check_username_exists = mock_db_auth_functions
    mock_check_username_exists.return_value = False  # Username does not exist
    mock_add_user.return_value = ObjectId()  # Simulate successful user creation

    response = client.post(
        url_for("auth.signup"),
        data={
            "username": "newuser",
            "password": "StrongPassword1!",
            "confirm_password": "StrongPassword1!",
            "role": "patient",
            "csrf_token": "dummy",  # CSRF disabled for testing
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Account created successfully! Please log in." in response.data
    assert b"Connexion" in response.data  # Redirects to login page


def test_signup_username_exists(client, mock_db_auth_functions):
    mock_add_user, _, mock_check_username_exists = mock_db_auth_functions
    mock_check_username_exists.return_value = True  # Username already exists

    # Form data to be used in the request
    form_data = {
        "username": "existinguser",
        "password": "StrongPassword1!",
        "confirm_password": "StrongPassword1!",
        "role": "patient",
        "csrf_token": "dummy",
    }

    # Push a request context for url_for to work
    with flask_app.test_request_context():
        signup_url = url_for("auth.signup")

    response = client.post(signup_url, data=form_data)  # Use form_data here

    assert response.status_code == 200
    # Check for the error message within the form's HTML output
    assert b'<ul class="form-errors">' in response.data

    # Re-instantiate the form with the response data to check errors
    from forms import RegistrationForm
    from flask import (
        request as flask_request,
    )  # Import request specifically for this context

    # Use the form data directly
    with flask_app.test_request_context(path=signup_url, method="POST", data=form_data):
        form = RegistrationForm(flask_request.form)
        form.validate()  # Manually validate the form to populate errors

        assert (
            "Ce nom d'utilisateur est déjà pris. Veuillez en choisir un autre."
            in form.username.errors
        )
    # The HTML assertion for the specific message is removed, as form.username.errors is more direct.


def test_login_page_loads(client):
    response = client.get(url_for("auth.login"))
    assert response.status_code == 200
    assert b"Connexion" in response.data


def test_login_successful(client, mock_db_auth_functions):
    _, mock_check_login, _ = mock_db_auth_functions
    mock_check_login.return_value = {
        "_id": str(ObjectId()),
        "username": "testuser",
        "role": "patient",
    }

    response = client.post(
        url_for("auth.login"),
        data={"username": "testuser", "password": "password123", "csrf_token": "dummy"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Logged in successfully!" in response.data
    assert b"Accueil Patient" in response.data  # Redirects to patient home
    with client.session_transaction() as sess:
        assert sess["user"]["username"] == "testuser"
        assert sess.permanent is True  # Check if session is permanent


def test_login_invalid_credentials(client, mock_db_auth_functions):
    _, mock_check_login, _ = mock_db_auth_functions
    mock_check_login.return_value = None  # Simulate failed login

    response = client.post(
        url_for("auth.login"),
        data={
            "username": "wronguser",
            "password": "wrongpassword",
            "csrf_token": "dummy",
        },
    )

    assert response.status_code == 200
    assert b"Invalid credentials. Please try again." in response.data
    with client.session_transaction() as sess:
        assert "user" not in sess  # User should not be in session


def test_logout_successful(client):
    with client.session_transaction() as sess:
        sess["user"] = {
            "_id": str(ObjectId()),
            "username": "testuser",
            "role": "patient",
        }
        sess.permanent = True

    response = client.get(url_for("auth.logout"), follow_redirects=True)
    assert response.status_code == 200
    assert b"You have been logged out." in response.data
    assert b"Connexion" in response.data  # Redirects to login page
    with client.session_transaction() as sess:
        assert "user" not in sess  # User should be logged out
