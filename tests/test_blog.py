import datetime

import pytest

from bloggy import db
from . import factories


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
        db.save_post(post)
    return posts


def test_index_redirect(client):
    response = client.get('/blog')
    assert response.status_code == 308
    assert 'http://localhost/blog/' == response.headers['location']


def test_index(client, saved_posts):
    response = client.get('/blog/')
    assert response.status_code == 200
    assert b'Post 21!!' in response.data
    assert b'Post 19!!' not in response.data  # un-published
    assert b'Post 12!!' in response.data  # last one before paging
    assert b'Post 11!!' not in response.data

    paging_link = b'<a href="/blog/?pt=eyIyIjogeyJjcmVhdGVkIjogIjIwMjMtMDEt' \
        b'MTJUMDA6MDA6MDAiLCAic2x1ZyI6ICJwb3N0LTEyIn19&page=2"'
    assert paging_link in response.data


def test_filter_by_tag(client, saved_posts):
    response = client.get('/blog/?tag=even')
    assert response.status_code == 200
    assert b'Post 21!!' not in response.data
    assert b'Post 20!!' in response.data
    paging_link = b'<a href="/blog/?tag=even&pt=eyIyIjogeyJjcmVhdGVkIjogIjIw' \
        b'MjMtMDEtMDRUMDA6MDA6MDAiLCAic2x1ZyI6ICJwb3N0LTQifX0&page=2"'
    assert paging_link in response.data


def test_paginate_with_filter(client, saved_posts):
    response = client.get('/blog/?tag=even&pt=eyIyIjogeyJjcmVhdGVkIjogIjIw'
                          'MjMtMDEtMDRUMDA6MDA6MDAiLCAic2x1ZyI6ICJwb3N0LTQ'
                          'ifX0&page=2')
    assert response.status_code == 200
    assert b'Post 2!!' in response.data

    prev_link = b'<a href="/blog/?tag=even&pt=eyIyIjogeyJjcmVhdGVkIjogIjIw' \
        b'MjMtMDEtMDRUMDA6MDA6MDAiLCAic2x1ZyI6ICJwb3N0LTQifSwgIjMiOiBudWxs' \
        b'fQ&page=1"'
    assert prev_link in response.data


def test_prev_page_with_filter(client, saved_posts):
    response = client.get('/blog/?tag=even&pt=eyIyIjogeyJjcmVhdGVkIjogIjIw'
                          'MjMtMDEtMDRUMDA6MDA6MDAiLCAic2x1ZyI6ICJwb3N0LTQ'
                          'ifSwgIjMiOiBudWxsfQ&page=1')
    assert b'Post 2!!' not in response.data
    assert b'Post 20!!' in response.data
    assert response.status_code == 200


def test_paginate_no_filter(client, saved_posts):
    response = client.get('/blog/?pt=eyIyIjogeyJjcmVhdGVkIjogIjIwMjMtMDEtMTJUM'
                          'DA6MDA6MDAiLCAic2x1ZyI6ICJwb3N0LTEyIn19&page=2')
    assert response.status_code == 200
    assert b'Post 2!!' in response.data
    assert b'Post 21!!' not in response.data

    prev_link = b'<a href="/blog/?pt=eyIyIjogeyJjcmVhdGVkIjogIjIwMjMtMDEtMTJ' \
        b'UMDA6MDA6MDAiLCAic2x1ZyI6ICJwb3N0LTEyIn0sICIzIjogeyJjcmVhdGVkIjogI' \
        b'jIwMjMtMDEtMDFUMDA6MDA6MDAiLCAic2x1ZyI6ICJwb3N0LTEifX0&page=1"'
    assert prev_link in response.data


def test_prev_page_no_filter(client, saved_posts):
    prev_link = '/blog/?pt=eyIyIjogeyJjcmVhdGVkIjogIjIwMjMtMDEtMTJ' \
        'UMDA6MDA6MDAiLCAic2x1ZyI6ICJwb3N0LTEyIn0sICIzIjogeyJjcmVhdGVkIjogI' \
        'jIwMjMtMDEtMDFUMDA6MDA6MDAiLCAic2x1ZyI6ICJwb3N0LTEifX0&page=1'
    response = client.get(prev_link)
    assert b'Post 2!!' not in response.data
    assert b'Post 20!!' in response.data
    assert response.status_code == 200


def test_show_post(client, saved_posts):
    response = client.get('/blog/post-11/')
    assert response.status_code == 200
    assert b'Post 11' in response.data


def test_dodgy_pagination_token(client, saved_posts):
    response = client.get('/blog/?paging_token=xyz')
    assert response.status_code == 200
    assert b'Post 21!!' in response.data
