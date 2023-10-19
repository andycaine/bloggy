import datetime
import unittest.mock

import pytest

import bloggy
from . import factories


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
def mock_get_published_posts():
    with unittest.mock.patch('bloggy.db.get_published_posts') as mock:
        yield mock


@pytest.fixture()
def use_local_dynamodb(monkeypatch):
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'foo')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'bar')
    bloggy.db.connect(use_local=True)


@pytest.fixture()
def empty_blog_table(use_local_dynamodb):
    bloggy.db.truncate()


@pytest.fixture()
def saved_posts(empty_blog_table):
    posts = [
        factories.PostFactory(
            title=f'Post {i}!!',
            slug=f'post-{i}',
            tags=[
                factories.TagFactory(name='even', label='Even')
            ] if i % 2 == 0 else [
                factories.TagFactory(name='odd', label='Odd')
            ],
            published=False if i in [19, 5] else True,
            created=datetime.datetime(2023, 1, i)
        ) for i in range(1, 23)
    ]
    for post in posts:
        bloggy.db.save_post(post)
    return posts
