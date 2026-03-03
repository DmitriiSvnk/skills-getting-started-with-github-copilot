"""
Tests for Mergington High School API

Tests are structured using the AAA (Arrange-Act-Assert) pattern.
Each test clearly separates setup, execution, and verification phases.
"""

import pytest
from copy import deepcopy
from fastapi.testclient import TestClient
from src.app import app, activities


# Store original activities state for reset between tests
ORIGINAL_ACTIVITIES = deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """
    FIXTURE: Reset activities to original state before each test.
    This ensures test isolation and prevents test pollution.
    """
    activities.clear()
    activities.update(deepcopy(ORIGINAL_ACTIVITIES))
    yield


def test_root_redirects_to_static():
    """
    Test that the root endpoint redirects to the static index page.
    
    ARRANGE: Create a test client
    ACT: Make a GET request to the root endpoint
    ASSERT: Verify the response is a 307 redirect with correct Location header
    """
    # ARRANGE
    client = TestClient(app)
    
    # ACT
    response = client.get("/", follow_redirects=False)
    
    # ASSERT
    assert response.status_code == 307
    assert "static/index.html" in response.headers["Location"]


def test_get_all_activities():
    """
    Test retrieving all available activities.
    
    ARRANGE: Create a test client
    ACT: Make a GET request to /activities
    ASSERT: Verify response contains all activities with correct structure
    """
    # ARRANGE
    client = TestClient(app)
    
    # ACT
    response = client.get("/activities")
    
    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 9  # 9 activities in the original set
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert all(isinstance(v, dict) for v in data.values())
    assert all("description" in v and "schedule" in v and "participants" in v for v in data.values())


def test_signup_new_participant():
    """
    Test successfully signing up a new participant for an activity.
    
    ARRANGE: Create a test client and define a new participant email
    ACT: Make a POST request to sign up for Chess Club
    ASSERT: Verify success response and participant is added to the activity
    """
    # ARRANGE
    client = TestClient(app)
    new_email = "newstudent@mergington.edu"
    activity_name = "Chess Club"
    
    # ACT
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email}
    )
    
    # ASSERT
    assert response.status_code == 200
    assert new_email in activities[activity_name]["participants"]
    assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"


def test_signup_duplicate_participant():
    """
    Test that signing up an already-registered participant returns 400 error.
    
    ARRANGE: Create a test client and use an existing participant
    ACT: Make a POST request to sign up with an existing email
    ASSERT: Verify 400 error response with appropriate message
    """
    # ARRANGE
    client = TestClient(app)
    existing_email = "michael@mergington.edu"  # Already in Chess Club
    activity_name = "Chess Club"
    
    # ACT
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": existing_email}
    )
    
    # ASSERT
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_signup_nonexistent_activity():
    """
    Test that signing up for a non-existent activity returns 404 error.
    
    ARRANGE: Create a test client and define a non-existent activity name
    ACT: Make a POST request to sign up for the non-existent activity
    ASSERT: Verify 404 error response
    """
    # ARRANGE
    client = TestClient(app)
    test_email = "test@mergington.edu"
    fake_activity = "Nonexistent Activity"
    
    # ACT
    response = client.post(
        f"/activities/{fake_activity}/signup",
        params={"email": test_email}
    )
    
    # ASSERT
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_unregister_existing_participant():
    """
    Test successfully unregistering an existing participant from an activity.
    
    ARRANGE: Create a test client and identify an existing participant
    ACT: Make a DELETE request to unregister
    ASSERT: Verify success response and participant is removed from activity
    """
    # ARRANGE
    client = TestClient(app)
    existing_email = "michael@mergington.edu"  # In Chess Club
    activity_name = "Chess Club"
    initial_count = len(activities[activity_name]["participants"])
    
    # ACT
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": existing_email}
    )
    
    # ASSERT
    assert response.status_code == 200
    assert existing_email not in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == initial_count - 1
    assert response.json()["message"] == f"Unregistered {existing_email} from {activity_name}"


def test_unregister_nonexistent_participant():
    """
    Test that unregistering a participant not signed up returns 400 error.
    
    ARRANGE: Create a test client and define an email not in the activity
    ACT: Make a DELETE request to unregister for an activity they're not in
    ASSERT: Verify 400 error response with appropriate message
    """
    # ARRANGE
    client = TestClient(app)
    test_email = "notregistered@mergington.edu"
    activity_name = "Chess Club"
    
    # ACT
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": test_email}
    )
    
    # ASSERT
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"]


def test_unregister_nonexistent_activity():
    """
    Test that unregistering from a non-existent activity returns 404 error.
    
    ARRANGE: Create a test client and define a non-existent activity name
    ACT: Make a DELETE request to unregister from the non-existent activity
    ASSERT: Verify 404 error response
    """
    # ARRANGE
    client = TestClient(app)
    test_email = "test@mergington.edu"
    fake_activity = "Nonexistent Activity"
    
    # ACT
    response = client.delete(
        f"/activities/{fake_activity}/unregister",
        params={"email": test_email}
    )
    
    # ASSERT
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_activities_state_isolation():
    """
    Test that modifications in one test don't affect another via fixture reset.
    
    ARRANGE: Create a test client and add a participant
    ACT: Sign up a participant and verify they were added
    ASSERT: Verify activities are properly reset before this test runs
    """
    # ARRANGE
    client = TestClient(app)
    activity_name = "Programming Class"
    test_email = "isolation@mergington.edu"
    
    # Verify the fixture has reset the activities (original participants should be present)
    assert "emma@mergington.edu" in activities[activity_name]["participants"]
    
    # ACT
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": test_email}
    )
    
    # ASSERT
    assert response.status_code == 200
    assert test_email in activities[activity_name]["participants"]
