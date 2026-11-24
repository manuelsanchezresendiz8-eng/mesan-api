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
