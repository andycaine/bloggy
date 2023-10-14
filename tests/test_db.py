import datetime

import pytest

import bloggy.db as db
from . import factories


def test_save_then_get_post(empty_blog_table):
    tags = [
        db.Tag(name='tag1', label='Tag 1'),
        db.Tag(name='tag2', label='Tag 2')
    ]
    post = db.Post(slug='first-post',
                   title='First post',
                   body='This is my first post',
                   tags=tags,
                   main_image=db.Image(src='http://test.com/img.jpg',
                                       alt='Alt desc',
                                       title='Image title'),
                   published=True)
    db.save_post(post)
    saved = db.get_post(slug=post.slug,
                        on_not_found=pytest.fail)

    assert saved == post


def test_get_all_posts(empty_blog_table):
    db.save_post(
        factories.PostFactory(slug='post1',
                              created=datetime.datetime(2022, 1, 1))
    )
    db.save_post(
        factories.PostFactory(slug='post4',
                              created=datetime.datetime(2022, 1, 4))
    )
    db.save_post(
        factories.PostFactory(slug='post2',
                              created=datetime.datetime(2022, 1, 2))
    )
    db.save_post(
        factories.PostFactory(slug='post3',
                              created=datetime.datetime(2022, 1, 3))
    )

    response = db.get_all_posts()
    assert [p.slug for p in response.items] == ['post4', 'post3', 'post2',
                                                'post1']


def test_get_published_posts(empty_blog_table):
    db.save_post(
        factories.PostFactory(slug='post1',
                              published=True,
                              created=datetime.datetime(2022, 1, 1))
    )
    db.save_post(
        factories.PostFactory(slug='post4',
                              published=False,
                              created=datetime.datetime(2022, 1, 4))
    )
    db.save_post(
        factories.PostFactory(slug='post2',
                              published=False,
                              created=datetime.datetime(2022, 1, 2))
    )
    db.save_post(
        factories.PostFactory(slug='post3',
                              published=True,
                              created=datetime.datetime(2022, 1, 3))
    )

    response = db.get_published_posts()
    assert [p.slug for p in response.items] == ['post3', 'post1']


def raise_exception():
    raise Exception('Test exception')


def test_get_post_not_found(empty_blog_table):
    with pytest.raises(Exception, match=r'Test exception'):
        db.get_post(slug='not-found', on_not_found=raise_exception)


def test_get_published_posts_with_tag(empty_blog_table):
    tag1 = factories.TagFactory(name='tag1')
    tag2 = factories.TagFactory(name='tag2')
    db.save_post(
        factories.PostFactory(slug='post1',
                              published=True,
                              tags=[tag1],
                              created=datetime.datetime(2022, 1, 1))
    )
    db.save_post(
        factories.PostFactory(slug='post4',
                              published=True,
                              tags=[tag2],
                              created=datetime.datetime(2022, 1, 4))
    )
    db.save_post(
        factories.PostFactory(slug='post2',
                              published=True,
                              tags=[],
                              created=datetime.datetime(2022, 1, 2))
    )
    db.save_post(
        factories.PostFactory(slug='post3',
                              published=True,
                              tags=[tag1, tag2],
                              created=datetime.datetime(2022, 1, 3))
    )

    response = db.get_published_posts('tag1')
    assert [p.slug for p in response.items] == ['post3', 'post1']


def test_get_non_published_post(empty_blog_table):
    db.save_post(factories.PostFactory(slug='post1',
                                       published=False,))

    with pytest.raises(Exception, match=r'Test exception'):
        db.get_published_post('post1', on_not_found=raise_exception)


def test_pagination(empty_blog_table):
    for i in range(1, 7):
        db.save_post(factories.PostFactory(
            slug=f'post{i}',
            published=True,
            created=datetime.datetime(2022, 1, i)
        ))

    response = db.get_published_posts(limit=5)
    assert [p.slug for p in response.items] == ['post6', 'post5', 'post4',
                                                'post3', 'post2']
    assert response.paging_key

    response = db.get_published_posts(limit=5,
                                      paging_key=response.paging_key)
    assert not response.paging_key
    assert [p.slug for p in response.items] == ['post1']
