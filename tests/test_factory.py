import bloggy


def test_index(client):
    response = client.get('/')
    assert response.status_code == 302
    assert '/blog/' == response.headers['location']


def test_handler():
    context = dict(httpMethod='GET',
                   path='/',
                   queryStringParameters=None)
    response = bloggy.handler(context, {})
    assert response['statusCode'] == '302'


def test_handler_404(client):
    response = client.get('/foo/')
    assert response.status_code == 404


def test_handler_500(client, mock_get_published_posts):
    mock_get_published_posts.side_effect = Exception()
    response = client.get('/blog/')
    assert response.status_code == 500
    assert b'Server Error' in response.data
