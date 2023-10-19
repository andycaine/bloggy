import bloggy
from . import factories


def test_list_posts(client, saved_posts):
    response = client.get('/admin/posts/')
    assert response.status_code == 200
    assert b'Post 21!!' in response.data
    assert b'Post 19!!' in response.data  # un-published
    assert b'Post 13!!' in response.data  # last one before paging
    assert b'Post 11!!' not in response.data

    paging_link = b'<a href="/admin/posts/?pt=eyIyIjogeyJjcmVhdGVkIjogIjIwMj' \
        b'MtMDEtMTNUMDA6MDA6MDAiLCAic2x1ZyI6ICJwb3N0LTEzIn19&page=2"'
    assert paging_link in response.data


def test_get_post(client, saved_posts):
    response = client.get('/admin/posts/post-11/')
    assert response.status_code == 200
    assert b'Post 11!!' in response.data


def test_delete_post(client, saved_posts):
    response = client.delete('/admin/posts/post-11/')
    assert response.status_code == 303
    assert response.headers['Location'] == '/admin/posts/'

    response = client.get('/admin/posts/post-11/')
    assert response.status_code == 404


def test_update_post_invalid(client, empty_blog_table):
    post = factories.PostFactory(slug='post-xyz')
    bloggy.db.save_post(post)
    response = client.post('/admin/posts/post-xyz/edit/', data={
        'title': 'asdf!!',
        'body': 'This is a post'
    })
    assert response.status_code == 200
    assert b'Only alphanumeric characters, underscores, spaces and dashes ' \
        b'are allowed' in response.data


def test_update_post_valid_post(client, empty_blog_table):
    post = factories.PostFactory(
        slug='post-xyz',
        published=False,
        title='Post XYZ',
        body='This is post xyz'
    )
    bloggy.db.save_post(post)
    response = client.get('/blog/post-xyz/')
    assert response.status_code == 404

    response = client.get('/admin/posts/post-xyz/edit/')
    assert response.status_code == 200
    assert b'Edit Post: Post XYZ' in response.data

    response = client.post('/admin/posts/post-xyz/edit/', data={
        'title': 'Post ZZZ',
        'body': 'This is post ZZZ',
        'published': 'on'
    })
    assert response.status_code == 302
    assert response.headers['Location'] == '/admin/posts/post-xyz/'

    response = client.get('/blog/post-xyz/')
    assert response.status_code == 200
    assert b'Post ZZZ' in response.data


def test_update_concurrent_edits(client, empty_blog_table):
    post = factories.PostFactory(
        slug='post-xyz',
        title='Post XYZ'
    )
    bloggy.db.save_post(post)

    response = client.post('/admin/posts/post-xyz/edit/', data={
        'title': 'Post ZZZ',
        'version': '1',
        'body': 'This is post ZZZ'
    })
    assert response.status_code == 302
    assert response.headers['Location'] == '/admin/posts/post-xyz/'

    response = client.post('/admin/posts/post-xyz/edit/', data={
        'title': 'Post XXX',
        'version': '1',
        'body': 'This is post XXX'
    })
    assert response.status_code == 200
    assert b'Unable to update post' in response.data


def test_add_post(client, empty_blog_table):
    response = client.get('/admin/posts/add/')
    assert response.status_code == 200
    assert b'New Post' in response.data

    response = client.post('/admin/posts/add/', data={
        'title': 'Post XYZ',
        'slug': 'post-xyz',
        'body': 'This is post XYZ'
    })
    assert response.status_code == 302
    assert response.headers['Location'] == '/admin/posts/post-xyz/'

    response = client.get('/admin/posts/post-xyz/')
    assert response.status_code == 200
    assert b'Post XYZ' in response.data
    assert b'This is post XYZ' in response.data


def test_add_post_duplicate_slug(client, empty_blog_table):
    post = factories.PostFactory(slug='post-xyz')
    bloggy.db.save_post(post)

    response = client.post('/admin/posts/add/', data={
        'title': 'Post XYZ',
        'slug': 'post-xyz',
        'body': 'This is post XYZ'
    })
    assert response.status_code == 200
    assert b'Slug already exists' in response.data
