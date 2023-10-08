import unittest.mock

import pytest

import bloggy


@pytest.fixture
def app():
    app = bloggy.create_app()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_get_post():
    with unittest.mock.patch('bloggy.db.get_post') as mock:
        yield mock


@pytest.fixture
def mock_get_published_post():
    with unittest.mock.patch('bloggy.db.get_published_post') as mock:
        yield mock


@pytest.fixture
def mock_get_all_published_posts():
    with unittest.mock.patch('bloggy.db.get_all_published_posts') as mock:
        yield mock
