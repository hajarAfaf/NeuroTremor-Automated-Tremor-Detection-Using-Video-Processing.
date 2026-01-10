import pytest
from unittest.mock import patch, MagicMock
from bson.objectid import ObjectId
import bcrypt

# Import the functions from the refactored mongodb_connector
from database.mongodb_connector import (
    connect_to_mongodb,
    add_patient,
    add_analysis,
    get_analyses,
    add_user,
    check_login,
    check_username_exists,
    get_all_patients,
    get_analysis_by_id,
)


# Fixture to mock the database collections for tests
@pytest.fixture
def mock_collections():
    mock_users_col = MagicMock()
    mock_patients_col = MagicMock()
    mock_analyses_col = MagicMock()
    return mock_users_col, mock_patients_col, mock_analyses_col


@patch("database.mongodb_connector.MongoClient")
def test_connect_to_mongodb_success(mock_mongo_client):
    # Mock the create_index methods on the mock collections that MongoClient would return
    mock_users_col_instance = MagicMock()
    mock_patients_col_instance = MagicMock()
    mock_analyses_col_instance = MagicMock()

    # Configure the mock MongoClient to return our mock collections
    mock_db = MagicMock()
    mock_db.__getitem__.side_effect = lambda name: {
        "users": mock_users_col_instance,
        "patients": mock_patients_col_instance,
        "analyses": mock_analyses_col_instance,
    }[name]
    mock_mongo_client.return_value.__getitem__.return_value = (
        mock_db  # This is the db object
    )

    users_col, patients_col, analyses_col = connect_to_mongodb()
    assert users_col is not None
    assert patients_col is not None
    assert analyses_col is not None
    mock_mongo_client.assert_called_once()
    mock_users_col_instance.create_index.assert_called_with("username", unique=True)
    mock_analyses_col_instance.create_index.assert_called_with("patient_id")


@patch("database.mongodb_connector.MongoClient")
def test_connect_to_mongodb_failure(mock_mongo_client):
    from pymongo.errors import ConnectionFailure

    mock_mongo_client.side_effect = ConnectionFailure("Connection failed")
    users_col, patients_col, analyses_col = connect_to_mongodb()
    assert users_col is None
    assert patients_col is None
    assert analyses_col is None
    mock_mongo_client.assert_called_once()


def test_check_username_exists(mock_collections):
    mock_users_col, _, _ = mock_collections
    # Test case: username exists
    mock_users_col.find_one.return_value = {"_id": ObjectId(), "username": "testuser"}
    assert check_username_exists(mock_users_col, "testuser") is True
    mock_users_col.find_one.assert_called_with({"username": "testuser"})

    # Test case: username does not exist
    mock_users_col.find_one.return_value = None
    assert check_username_exists(mock_users_col, "nonexistent") is False


def test_add_user(mock_collections):
    mock_users_col, _, _ = mock_collections
    from pymongo.errors import DuplicateKeyError

    # Test case: successful addition
    mock_users_col.insert_one.return_value.inserted_id = ObjectId(
        "60c72b2f9b1d8c001f8e4d1a"
    )
    inserted_id = add_user(mock_users_col, "newuser", "password123", "patient")
    assert inserted_id == ObjectId("60c72b2f9b1d8c001f8e4d1a")
    mock_users_col.insert_one.assert_called_once()
    assert bcrypt.checkpw(
        b"password123", mock_users_col.insert_one.call_args[0][0]["password"]
    )

    # Test case: duplicate username
    mock_users_col.insert_one.side_effect = DuplicateKeyError("Duplicate username")
    assert add_user(mock_users_col, "existinguser", "password123") is None


def test_check_login(mock_collections):
    mock_users_col, _, _ = mock_collections
    # Test case: successful login
    hashed_password = bcrypt.hashpw(b"correctpassword", bcrypt.gensalt())
    mock_users_col.find_one.return_value = {
        "_id": ObjectId("60c72b2f9b1d8c001f8e4d1b"),
        "username": "testuser",
        "password": hashed_password,
        "role": "patient",
    }
    user_data = check_login(mock_users_col, "testuser", "correctpassword")
    assert user_data is not None
    assert user_data["username"] == "testuser"
    assert user_data["role"] == "patient"
    assert user_data["_id"] == "60c72b2f9b1d8c001f8e4d1b"

    # Test case: incorrect password
    user_data = check_login(mock_users_col, "testuser", "wrongpassword")
    assert user_data is None

    # Test case: user not found
    mock_users_col.find_one.return_value = None
    user_data = check_login(mock_users_col, "nonexistent", "anypassword")
    assert user_data is None


def test_get_all_patients(mock_collections):
    mock_users_col, _, _ = mock_collections
    mock_users_col.find.return_value = [
        {
            "_id": ObjectId("60c72b2f9b1d8c001f8e4d1c"),
            "username": "patient1",
            "role": "patient",
        },
        {
            "_id": ObjectId("60c72b2f9b1d8c001f8e4d1d"),
            "username": "patient2",
            "role": "patient",
        },
    ]
    patients = get_all_patients(mock_users_col)
    assert len(patients) == 2
    assert patients[0]["username"] == "patient1"
    mock_users_col.find.assert_called_with({"role": "patient"})


def test_add_patient(mock_collections):
    _, mock_patients_col, _ = mock_collections
    mock_patients_col.insert_one.return_value.inserted_id = ObjectId(
        "60c72b2f9b1d8c001f8e4d1e"
    )
    inserted_id = add_patient(mock_patients_col, "John Doe", 30, "M")
    assert inserted_id == ObjectId("60c72b2f9b1d8c001f8e4d1e")
    mock_patients_col.insert_one.assert_called_once()


def test_add_analysis(mock_collections):
    _, mock_patients_col, mock_analyses_col = mock_collections
    mock_analyses_col.insert_one.return_value.inserted_id = ObjectId(
        "60c72b2f9b1d8c001f8e4d1f"
    )
    patient_id = ObjectId("60c72b2f9b1d8c001f8e4d1e")
    analysis_data = {"some": "data"}

    inserted_id = add_analysis(
        mock_analyses_col, mock_patients_col, patient_id, analysis_data
    )
    assert inserted_id == ObjectId("60c72b2f9b1d8c001f8e4d1f")
    mock_analyses_col.insert_one.assert_called_once_with(analysis_data)
    mock_patients_col.update_one.assert_called_once_with(
        {"_id": patient_id}, {"$push": {"historique": inserted_id}}
    )


def test_get_analyses(mock_collections):
    mock_users_col, mock_patients_col, mock_analyses_col = mock_collections
    patient_id = ObjectId("60c72b2f9b1d8c001f8e4d1e")
    analysis_id1 = ObjectId("60c72b2f9b1d8c001f8e4d1f")
    analysis_id2 = ObjectId("60c72b2f9b1d8c001f8e4d20")

    mock_patients_col.find_one.return_value = {
        "_id": patient_id,
        "historique": [analysis_id1, analysis_id2],
    }

    mock_analyses_col.find.return_value.sort.return_value = [
        {"_id": analysis_id2, "result": {"date": "2026-01-10"}},
        {"_id": analysis_id1, "result": {"date": "2026-01-09"}},
    ]

    analyses = get_analyses(mock_patients_col, mock_analyses_col, patient_id)
    assert len(analyses) == 2
    assert analyses[0]["_id"] == analysis_id2
    mock_analyses_col.find.assert_called_once_with(
        {"_id": {"$in": [analysis_id1, analysis_id2]}}
    )
    mock_analyses_col.find.return_value.sort.assert_called_once_with("result.date", -1)


def test_get_analysis_by_id(mock_collections):
    mock_users_col, mock_patients_col, mock_analyses_col = mock_collections
    analysis_id = ObjectId("60c72b2f9b1d8c001f8e4d21")
    mock_analyses_col.find_one.return_value = {"_id": analysis_id, "data": "test"}

    analysis = get_analysis_by_id(mock_analyses_col, analysis_id)
    assert analysis["_id"] == analysis_id
    mock_analyses_col.find_one.assert_called_once_with({"_id": analysis_id})

    mock_analyses_col.find_one.return_value = None
    analysis = get_analysis_by_id(mock_analyses_col, ObjectId())
    assert analysis is None
