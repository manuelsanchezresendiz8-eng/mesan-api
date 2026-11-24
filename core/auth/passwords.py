"""Password hashing for MESAN Omega authentication (stdlib only)."""
import base64
import hashlib
import hmac
import os

_ITERATIONS = 310_000
_MIN_VERIFY_ITERATIONS = 100_000
_MAX_VERIFY_ITERATIONS = 1_000_000
_ALGORITHM = "pbkdf2_sha256"
_SALT_BYTES = 16
_DIGEST_BYTES = 32


def hash_password(password: str) -> str:
    if not isinstance(password, str) or len(password) < 12:
        raise ValueError("PASSWORD_MIN_LENGTH_12")
    salt = os.urandom(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return "$".join((
        _ALGORITHM,
        str(_ITERATIONS),
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    ))


def verify_password(password: str, encoded: str) -> bool:
    """Verify only bounded, well-formed hashes to prevent CPU-amplification."""
    if not isinstance(password, str) or not isinstance(encoded, str) or len(encoded) > 256:
        return False
    try:
        algorithm, iterations_text, salt_b64, digest_b64 = encoded.split("$", 3)
        if algorithm != _ALGORITHM:
            return False
        iterations = int(iterations_text)
        if not _MIN_VERIFY_ITERATIONS <= iterations <= _MAX_VERIFY_ITERATIONS:
            return False
        salt = base64.b64decode(salt_b64.encode("ascii"), altchars=b"-_", validate=True)
        expected = base64.b64decode(digest_b64.encode("ascii"), altchars=b"-_", validate=True)
        if len(salt) != _SALT_BYTES or len(expected) != _DIGEST_BYTES:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, iterations
        )
        return hmac.compare_digest(actual, expected)
    except (AttributeError, TypeError, ValueError):
        return False
