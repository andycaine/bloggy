import datetime

import pytest

import bloggy.db as db
from . import factories


def post_or_fail(slug):
    return db.get_post(slug=slug, on_not_found=pytest.fail)


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
    saved = post_or_fail(slug=post.slug)

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


def test_update_post(empty_blog_table):
    post = factories.PostFactory()
    db.save_post(post)

    post.title = 'New title'
    db.update_post(post)

    updated = post_or_fail(slug=post.slug)
    assert updated.title == 'New title'


def test_retag_post(empty_blog_table):
    tag1 = factories.TagFactory(name='tag1')
    tag2 = factories.TagFactory(name='tag2')
    post = factories.PostFactory(
        tags=[tag1, tag2],
        published=True
    )

    db.save_post(post)

    tag3 = factories.TagFactory(name='tag3')
    post.tags.remove(tag1)
    post.tags.append(tag3)

    db.update_post(post)

    updated = post_or_fail(slug=post.slug)
    assert updated.tags == [tag2, tag3]

    assert db.get_posts(tag=tag1).items == []
    assert db.get_posts(tag='tag3').items == [updated]


def test_publish_post(empty_blog_table):
    tag1 = factories.TagFactory(name='tag1')
    post = factories.PostFactory(
        tags=[tag1],
        published=False
    )

    db.save_post(post)

    post.published = True

    db.update_post(post)

    assert db.get_posts(tag='tag1').items == [post]


def test_unpublish_post(empty_blog_table):
    tag1 = factories.TagFactory(name='tag1')
    post = factories.PostFactory(
        tags=[tag1],
        published=True
    )

    db.save_post(post)

    post.published = False

    db.update_post(post)

    assert db.get_posts(tag='tag1').items == []


def test_delete_post(empty_blog_table):
    post = factories.PostFactory()
    db.save_post(post)

    db.delete_post(post.slug)

    with pytest.raises(Exception, match=r'Test exception'):
        db.get_post(slug=post.slug, on_not_found=raise_exception)


def test_duplicate_slug(empty_blog_table):
    db.save_post(factories.PostFactory(slug='post1'))

    with pytest.raises(db.DuplicateKeyException,
                       match=r'Item already exists'):
        db.save_post(factories.PostFactory(slug='post1'))


def test_concurrent_updates(empty_blog_table):
    post = factories.PostFactory(title='Initial title')
    db.save_post(post)

    stale = db.get_post(slug=post.slug, on_not_found=pytest.fail)

    post.title = 'New title'
    db.update_post(post)

    stale.title = 'Another title'
    with pytest.raises(db.ConcurrentUpdateException,
                       match=r'Concurrent update exception'):
        db.update_post(stale)

    updated = post_or_fail(slug=post.slug)
    assert updated.title == 'New title'
