import urllib.parse

import bloggy.utils as utils


def test_url_tokenisation():
    data = dict(foo='bar', baz='qux')
    token = utils.to_url_token(data)
    assert utils.from_url_token(token) == data
    assert urllib.parse.quote(token) == token


def test_url_tokenisation_with_none():
    assert utils.from_url_token(None) is None
    assert utils.to_url_token(None) is None


def test_from_url_token_with_invalid_token():
    assert utils.from_url_token('invalid-token') is None
