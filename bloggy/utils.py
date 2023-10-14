import base64
import json

import flask


def to_url_token(data: dict):
    """Create a URL-safe token for the given data."""
    if not data:
        return None
    s = json.dumps(data).encode('utf-8')
    return base64.urlsafe_b64encode(s).rstrip(b'=').decode('utf-8')


def from_url_token(token: dict, default=None):
    """Decode the given URL-safe token."""
    if not token:
        return default
    try:
        s = base64.urlsafe_b64decode(token + '=' * (-len(token) % 4))
        return json.loads(s)
    except Exception:
        return default


def abort_404():
    return flask.abort(404)
