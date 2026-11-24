from starlette.requests import Request

from core.rate_limiter import _get_client_ip


def make_request(peer_ip, headers=None):
    raw_headers = [
        (key.lower().encode("latin-1"), value.encode("latin-1"))
        for key, value in (headers or {}).items()
    ]
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": "/auth/login",
        "raw_path": b"/auth/login",
        "query_string": b"",
        "headers": raw_headers,
        "client": (peer_ip, 12345) if peer_ip else None,
        "server": ("testserver", 443),
    }
    return Request(scope)


def test_forwarded_for_cannot_override_connection_ip():
    request = make_request(
        "203.0.113.10",
        {"X-Forwarded-For": "198.51.100.77"},
    )
    assert _get_client_ip(request) == "203.0.113.10"


def test_forwarded_for_chain_is_ignored():
    request = make_request(
        "2001:db8::1",
        {"X-Forwarded-For": "198.51.100.77, 192.0.2.10"},
    )
    assert _get_client_ip(request) == "2001:db8::1"


def test_missing_or_invalid_peer_falls_back_to_unknown():
    assert _get_client_ip(make_request(None)) == "unknown"
    assert _get_client_ip(make_request("not-an-ip")) == "unknown"
