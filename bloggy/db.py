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


@dataclasses.dataclass
class PageableList:
    items: list
    paging_key: dict = None


def get_posts(include_unpublished=False, tag=None, limit=10,
              paging_key=None):
    sk = f'#post{"" if include_unpublished else "#published"}'\
        f'{f"#tag#{tag}" if tag else ""}'

    query_args = dict(
        IndexName='GSI',
        KeyConditionExpression='sk = :sk',
        ExpressionAttributeValues={
            ':sk': sk
        },
        Limit=limit,
        ScanIndexForward=False
    )

    if paging_key:
        exc_start_key = dict(pk=f'post#{paging_key["slug"]}',
                             sk=sk,
                             data=paging_key['created'])
        query_args['ExclusiveStartKey'] = exc_start_key

    response = _conn.table.query(**query_args)
    posts = [_convertor.structure(item['post'], Post)
             for item in response['Items']]

    paging_key = None
    if 'LastEvaluatedKey' in response:
        paging_key = dict(
            created=response['LastEvaluatedKey']['data'],
            slug=response['LastEvaluatedKey']['pk'].split('#')[1]
        )

    return PageableList(items=posts,
                        paging_key=paging_key)


def get_all_posts(limit=10, paging_key=None):
    return get_posts(include_unpublished=True, limit=limit,
                     paging_key=paging_key)


def get_published_posts(tag=None, limit=10, paging_key=None):
    return get_posts(include_unpublished=False, tag=tag, limit=limit,
                     paging_key=paging_key)


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


def _scan(esk=None):
    scan_args = {}
    if esk:
        scan_args['ExclusiveStartKey'] = esk

    response = _conn.table.scan(**scan_args)
    for item in response['Items']:
        yield item

    if 'LastEvaluatedKey' in response:
        yield from _scan(response['LastEvaluatedKey'])


def _delete_all(items):
    with _conn.table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={'pk': item['pk'], 'sk': item['sk']})


def truncate():
    _delete_all(_scan())
