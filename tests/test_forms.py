import pytest
from unittest.mock import patch
from forms import LoginForm, RegistrationForm
from app import app  # Import the Flask app instance


# Fixture to push an application context for form tests
@pytest.fixture(
    autouse=True
)  # autouse=True means this fixture runs for all tests in this file
def app_context():
    with app.app_context():
        yield


# We will now patch database.mongodb_connector.check_username_exists directly
# and ensure it's used by the forms.
# No need for a separate fixture for this if we patch it directly in tests.


def test_login_form_valid_data():
    form = LoginForm(username="testuser", password="password123")
    assert form.validate() is True


def test_login_form_missing_username():
    form = LoginForm(username="", password="password123")
    assert form.validate() is False
    assert "This field is required." in form.username.errors


def test_login_form_missing_password():
    form = LoginForm(username="testuser", password="")
    assert form.validate() is False
    assert "This field is required." in form.password.errors


@patch("database.mongodb_connector.check_username_exists")
def test_registration_form_valid_data(mock_check_username_exists):
    mock_check_username_exists.return_value = False  # Username does not exist
    form = RegistrationForm(
        username="newuser",
        password="StrongPassword1!",
        confirm_password="StrongPassword1!",
        role="patient",
    )
    assert form.validate() is True


@patch("database.mongodb_connector.check_username_exists")
def test_registration_form_username_too_short(mock_check_username_exists):
    mock_check_username_exists.return_value = False
    form = RegistrationForm(
        username="a",
        password="StrongPassword1!",
        confirm_password="StrongPassword1!",
        role="patient",
    )
    assert form.validate() is False
    assert "Field must be between 2 and 20 characters long." in form.username.errors


@patch("database.mongodb_connector.check_username_exists")
def test_registration_form_username_already_exists(mock_check_username_exists):
    mock_check_username_exists.return_value = True  # Username already exists
    form = RegistrationForm(
        username="existinguser",
        password="StrongPassword1!",
        confirm_password="StrongPassword1!",
        role="patient",
    )
    assert form.validate() is False
    assert (
        "Ce nom d'utilisateur est déjà pris. Veuillez en choisir un autre."
        in form.username.errors
    )


@patch("database.mongodb_connector.check_username_exists")
def test_registration_form_password_too_short(mock_check_username_exists):
    mock_check_username_exists.return_value = False
    form = RegistrationForm(
        username="newuser",
        password="Short1!",
        confirm_password="Short1!",
        role="patient",
    )
    assert form.validate() is False
    assert (
        "Le mot de passe doit contenir au moins 8 caractères, une majuscule, une minuscule, un chiffre et un caractère spécial."
        in form.password.errors
    )


@patch("database.mongodb_connector.check_username_exists")
def test_registration_form_password_no_uppercase(mock_check_username_exists):
    mock_check_username_exists.return_value = False
    form = RegistrationForm(
        username="newuser",
        password="strongpassword1!",
        confirm_password="strongpassword1!",
        role="patient",
    )
    assert form.validate() is False
    assert (
        "Le mot de passe doit contenir au moins 8 caractères, une majuscule, une minuscule, un chiffre et un caractère spécial."
        in form.password.errors
    )


@patch("database.mongodb_connector.check_username_exists")
def test_registration_form_password_mismatch(mock_check_username_exists):
    mock_check_username_exists.return_value = False
    form = RegistrationForm(
        username="newuser",
        password="StrongPassword1!",
        confirm_password="Mismatch1!",
        role="patient",
    )
    assert form.validate() is False
    assert "Les mots de passe doivent correspondre." in form.confirm_password.errors


@patch("database.mongodb_connector.check_username_exists")
def test_registration_form_invalid_role(mock_check_username_exists):
    mock_check_username_exists.return_value = False
    form = RegistrationForm(
        username="newuser",
        password="StrongPassword1!",
        confirm_password="StrongPassword1!",
        role="invalid_role",
    )
    assert form.validate() is False
    assert "Not a valid choice." in form.role.errors
