import dataclasses
import datetime

import boto3
import cattrs


_convertor = cattrs.Converter()
_convertor.register_unstructure_hook(datetime.datetime,
                                     lambda dt: dt.isoformat())
_convertor.register_structure_hook(
    datetime.datetime,
    lambda ts, _: datetime.datetime.fromisoformat(ts)
)


@dataclasses.dataclass
class Image:
    src: str
    alt: str
    title: str


@dataclasses.dataclass
class Tag:
    name: str
    label: str


@dataclasses.dataclass
class Post:
    slug: str
    title: str
    body: str
    published: bool
    tags: list[Tag]
    main_image: Image
    created: datetime.datetime = datetime.datetime.now()


class Conn:
    pass


_table_name = 'Blog'
_conn = Conn()


def connect(use_local=False):
    ddb_args = use_local and {'endpoint_url': 'http://localhost:8000'} or {}
    dynamodb = boto3.resource('dynamodb', **ddb_args)

    _conn.table = dynamodb.Table(_table_name)


def save_post(post):
    with _conn.table.batch_writer() as batch:
        batch.put_item(Item={
            'pk': f'post#{post.slug}',
            'sk': '#post',
            'data': post.created.isoformat(),
            'post': _convertor.unstructure(post),
        })
        if post.published:
            batch.put_item(Item={
                'pk': f'post#{post.slug}',
                'sk': '#post#published',
                'data': post.created.isoformat(),
                'post': _convertor.unstructure(post),
            })
            for tag in post.tags:
                batch.put_item(Item={
                    'pk': f'post#{post.slug}',
                    'sk': f'#post#published#tag#{tag.name}',
                    'data': post.created.isoformat(),
                    'post': _convertor.unstructure(post),
                })
        for tag in post.tags:
            batch.put_item(Item={
                'pk': f'tag#{tag.name}',
                'sk': '#tag',
                'data': tag.label,
                'tag': _convertor.unstructure(tag),
            })


def get_all_posts():
    response = _conn.table.query(
        IndexName='GSI',
        KeyConditionExpression='sk = :sk',
        ExpressionAttributeValues={
            ':sk': '#post'
        }
    )
    return [_convertor.structure(item['post'], Post)
            for item in response['Items']]


def get_all_published_posts(tag=None):
    sk = tag and f'#post#published#tag#{tag}' or '#post#published'
    response = _conn.table.query(
        IndexName='GSI',
        KeyConditionExpression='sk = :sk',
        ExpressionAttributeValues={
            ':sk': sk
        }
    )
    return [_convertor.structure(item['post'], Post)
            for item in response['Items']]


def get_post(slug, on_not_found):
    response = _conn.table.get_item(
        Key={
            'pk': f'post#{slug}',
            'sk': '#post'
        }
    )
    if 'Item' not in response:
        on_not_found()
    return _convertor.structure(response['Item']['post'], Post)


def get_published_post(slug, on_not_found):
    post = get_post(slug, on_not_found)
    if not post.published:
        on_not_found()
    else:
        return post


def _scan():
    response = _conn.table.scan()
    return response['Items']


def _delete_all(items):
    with _conn.table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={'pk': item['pk'], 'sk': item['sk']})


def truncate():
    _delete_all(_scan())
