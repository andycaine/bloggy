from . import factories


def test_index_redirect(client):
    response = client.get('/blog')
    assert response.status_code == 308
    assert 'http://localhost/blog/' == response.headers['location']


def test_index(client, mock_get_all_published_posts):
    mock_get_all_published_posts.return_value = [
        factories.PostFactory(title='Puffins in Pembrokeshire'),
        factories.PostFactory(title='SaundersFEST 2023'),
    ]

    response = client.get('/blog/')
    assert response.status_code == 200
    assert b'Puffins in Pembrokeshire' in response.data
    assert b'SaundersFEST 2023' in response.data
    assert mock_get_all_published_posts.called_once_with(None)


def test_filter_by_tag(client, mock_get_all_published_posts):
    mock_get_all_published_posts.return_value = [
        factories.PostFactory(title='Puffins in Pembrokeshire'),
        factories.PostFactory(title='SaundersFEST 2023'),
    ]

    response = client.get('/blog/?tag=flask')
    assert response.status_code == 200
    assert b'Puffins in Pembrokeshire' in response.data
    assert b'SaundersFEST 2023' in response.data
    assert mock_get_all_published_posts.called_once_with('flask')


def test_show_post(client, mock_get_published_post):
    mock_get_published_post.return_value = factories.PostFactory(
        title='Puffins in Pembrokeshire'
    )
    response = client.get('/blog/puffins-in-pembrokeshire/')
    assert response.status_code == 200
    assert b'Puffins in Pembrokeshire' in response.data
    assert mock_get_published_post.called_once_with('puffins-in-pembrokeshire')
