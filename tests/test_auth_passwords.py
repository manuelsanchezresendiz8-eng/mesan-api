from core.auth.passwords import hash_password, verify_password


def test_password_hash_is_salted_and_verifiable():
    first = hash_password("Clave-MESAN-segura-2026")
    second = hash_password("Clave-MESAN-segura-2026")

    assert first != second
    assert verify_password("Clave-MESAN-segura-2026", first)
    assert not verify_password("otra-clave-segura-2026", first)


def test_password_hash_rejects_short_password():
    try:
        hash_password("corta")
    except ValueError as exc:
        assert str(exc) == "PASSWORD_MIN_LENGTH_12"
    else:
        raise AssertionError("Expected minimum password length validation")


def test_password_verification_rejects_unbounded_iteration_count():
    assert not verify_password(
        "Clave-MESAN-segura-2026",
        "pbkdf2_sha256$999999999$MDEyMzQ1Njc4OWFiY2RlZg==$"
        "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
    )


def test_password_verification_rejects_malformed_or_oversized_hash():
    assert not verify_password("password", "x" * 257)
    assert not verify_password("password", "not-a-password-hash")
    assert not verify_password(None, "pbkdf2_sha256$310000$bad$bad")
