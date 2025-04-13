# tests/test_auth.py
import pytest
from datetime import datetime, timezone
import app.core.auth as auth  # Import the module so we can override its globals

# Import the functions to test
from app.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)


def test_password_functions():
    # Use a known password
    password = "supersecret"
    # Generate a hash of the password.
    hashed = get_password_hash(password)
    
    # Verify that the hashed value is a string.
    assert isinstance(hashed, str)
    
    # Check that verifying the correct password returns True.
    assert verify_password(password, hashed) is True
    
    # Check that a wrong password does not verify.
    assert verify_password("wrongpassword", hashed) is False


def test_create_and_decode_access_token():
    # Set the module-level variables to known test values.
    auth.SECRET_KEY = "testsecret"
    auth.ALGORITHM = "HS256"
    auth.ACCESS_TOKEN_EXPIRE_MINUTES = 30

    # Define payload data.
    data = {"sub": "user@example.com"}
    
    # Create the token.
    token = create_access_token(data)
    
    # Assert the token is a string.
    assert isinstance(token, str)
    
    # Decode the token.
    payload = decode_access_token(token)
    
    # Verify the payload is a dictionary, contains the data we sent,
    # and has an expiration field.
    assert isinstance(payload, dict)
    assert payload.get("sub") == "user@example.com"
    assert "exp" in payload
    
    # Ensure that the expiration timestamp is in the future.
    exp_timestamp = payload["exp"]
    current_ts = datetime.now(timezone.utc).timestamp()
    assert exp_timestamp > current_ts


def test_decode_invalid_access_token():
    # For decoding, we need the same secret and algorithm.
    auth.SECRET_KEY = "testsecret"
    auth.ALGORITHM = "HS256"
    
    # Create an invalid token string.
    invalid_token = "invalid.token.string"
    
    # Decoding an invalid token should return None.
    payload = decode_access_token(invalid_token)
    assert payload is None
