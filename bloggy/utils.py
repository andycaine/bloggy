import base64
import functools
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


def pageable(template):
    def decorator(fn):
        @functools.wraps(fn)
        def decorated_fn(*args, **kwargs):
            paging_tokens = flask.request.args.get('pt', None)
            try:
                page = int(flask.request.args.get('page', 1))
            except ValueError:
                page = 1
            paging_keys = from_url_token(paging_tokens, {})
            paging_key = None
            if paging_keys and page > 1 and str(page) in paging_keys:
                paging_key = paging_keys[str(page)]

            # if paging_key is None, make sure page = 1
            if paging_key is None:
                page = 1

            kwargs['paging_key'] = paging_key
            ctx, next_paging_key = fn(*args, **kwargs)

            if next_paging_key:
                paging_keys[page + 1] = next_paging_key

            new_paging_tokens = to_url_token(paging_keys)

            ctx['prev'] = page - 1 if page > 0 else None
            ctx['next'] = page + 1 if next_paging_key else None
            ctx['paging_tokens'] = new_paging_tokens
            return flask.render_template(template, **ctx)
        return decorated_fn
    return decorator
