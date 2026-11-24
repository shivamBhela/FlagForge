import pytest
from app.core.crypto import encrypt_secret, decrypt_secret
from app.core.ssrf import validate_target_url, SSRFValidationError


def test_encryption_roundtrip():
    secret = "secret-flagsmith-management-token-xyz-12345"
    encrypted = encrypt_secret(secret)
    assert encrypted != secret
    assert len(encrypted) > 20

    decrypted = decrypt_secret(encrypted)
    assert decrypted == secret

    # Empty string handling
    assert encrypt_secret("") == ""
    assert decrypt_secret("") == ""


def test_ssrf_blocks_private_and_metadata():
    # Loopback
    with pytest.raises(SSRFValidationError):
        validate_target_url("http://127.0.0.1:8000/api/v1")

    with pytest.raises(SSRFValidationError):
        validate_target_url("http://localhost:8000/api/v1")

    # AWS/GCP/Azure Metadata IP
    with pytest.raises(SSRFValidationError):
        validate_target_url("http://169.254.169.254/latest/meta-data/")

    # Disallowed scheme
    with pytest.raises(SSRFValidationError):
        validate_target_url("ftp://ftp.example.com/file")

    with pytest.raises(SSRFValidationError):
        validate_target_url("file:///etc/passwd")


def test_ssrf_permits_public_flagsmith():
    # Public Flagsmith endpoints should pass validation
    valid_url = validate_target_url("https://edge.api.flagsmith.com/api/v1")
    assert valid_url == "https://edge.api.flagsmith.com/api/v1"

    valid_cloud = validate_target_url("https://api.flagsmith.com/api/v1")
    assert valid_cloud == "https://api.flagsmith.com/api/v1"
