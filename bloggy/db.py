import dataclasses
import datetime

import boto3
import boto3.dynamodb.types
import cattrs


class ConcurrentUpdateException(Exception):
    pass


class DuplicateKeyException(Exception):
    pass


_convertor = cattrs.Converter()
_convertor.register_unstructure_hook(datetime.datetime,
                                     lambda dt: dt.isoformat())
_convertor.register_structure_hook(
    datetime.datetime,
    lambda ts, _: datetime.datetime.fromisoformat(ts)
)


@dataclasses.dataclass(frozen=True)
class Image:
    src: str
    alt: str
    title: str


@dataclasses.dataclass
class Tag:
    name: str
    label: str
    version: int = 1


@dataclasses.dataclass
class Post:
    slug: str
    title: str
    body: str
    published: bool
    tags: list[Tag]
    main_image: Image
    created: datetime.datetime = datetime.datetime.now()
    version: int = 1


class Conn:
    pass


_table_name = 'Blog'
_conn = Conn()


def connect(use_local=False):
    ddb_args = use_local and {'endpoint_url': 'http://localhost:8000'} or {}
    dynamodb = boto3.resource('dynamodb', **ddb_args)

    _conn.table = dynamodb.Table(_table_name)

    client = boto3.client('dynamodb', **ddb_args)
    _conn.client = client


_serializer = boto3.dynamodb.types.TypeSerializer()
_deserializer = boto3.dynamodb.types.TypeDeserializer()


def _serialized(**kwargs):
    return {k: _serializer.serialize(v) for k, v in kwargs.items()}


def _post_item(post):
    return _serialized(
        pk=f'post#{post.slug}',
        sk='#post',
        data=post.created.isoformat(),
        version=post.version,
        post=_convertor.unstructure(post)
    )


def _published_post_item(post):
    return _serialized(
        pk=f'post#{post.slug}',
        sk='#post#published',
        data=post.created.isoformat(),
        version=post.version,
        post=_convertor.unstructure(post)
    )


def _published_post_tag_item(post, tag):
    return _serialized(
        pk=f'post#{post.slug}',
        sk=f'#post#published#tag#{tag.name}',
        data=post.created.isoformat(),
        version=post.version,
        post=_convertor.unstructure(post)
    )


def _tag_item(tag):
    return _serialized(
        pk=f'tag#{tag.name}',
        sk='#tag',
        data=tag.label,
        version=tag.version,
        tag=_convertor.unstructure(tag),
    )


def save_tag(tag):
    tag.version = 1
    transact_items = [dict(
        Put=dict(
            TableName=_table_name,
            ConditionExpression='attribute_not_exists(pk)',
            Item=_tag_item(tag)
        )
    )]

    try:
        _conn.client.transact_write_items(
            TransactItems=transact_items
        )
    except _conn.client.exceptions.TransactionCanceledException as e:
        reasons = [reason['Code'] for reason
                   in e.response['CancellationReasons']]
        if 'ConditionalCheckFailed' in reasons:
            raise DuplicateKeyException('Item already exists')
        raise e


def save_post(post):
    post.version = 1
    transact_items = [dict(
        Put=dict(
            TableName=_table_name,
            ConditionExpression='attribute_not_exists(pk)',
            Item=_post_item(post)
        )
    )]
    if post.published:
        transact_items.append(dict(
            Put=dict(
                TableName=_table_name,
                Item=_published_post_item(post)
            )
        ))
        for tag in post.tags:
            transact_items.append(dict(
                Put=dict(
                    TableName=_table_name,
                    Item=_published_post_tag_item(post, tag)
                )
            ))

    try:
        _conn.client.transact_write_items(
            TransactItems=transact_items
        )
    except _conn.client.exceptions.TransactionCanceledException as e:
        reasons = [reason['Code'] for reason
                   in e.response['CancellationReasons']]
        if 'ConditionalCheckFailed' in reasons:
            raise DuplicateKeyException('Item already exists')
        raise e


@dataclasses.dataclass
class PageableList:
    items: list
    paging_key: dict = None


def get_posts(include_unpublished=False, tag=None, limit=10,
              paging_key=None):
    sk = f'#post{"" if include_unpublished else "#published"}' \
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
        return None
    return _convertor.structure(response['Item']['post'], Post)


def get_tag(name, on_not_found):
    response = _conn.table.get_item(
        Key={
            'pk': f'tag#{name}',
            'sk': '#tag'
        }
    )
    if 'Item' not in response:
        on_not_found()
        return None
    return _convertor.structure(response['Item']['tag'], Tag)


def get_all_tags(limit=10, paging_key=None):
    query_args = dict(
        IndexName='GSI',
        KeyConditionExpression='sk = :sk',
        ExpressionAttributeValues={
            ':sk': '#tag'
        },
        Limit=limit
    )
    if paging_key:
        exc_start_key = dict(pk=f'tag#{paging_key["name"]}',
                             sk='#tag',
                             data=paging_key['created'])
        query_args['ExclusiveStartKey'] = exc_start_key

    response = _conn.table.query(**query_args)
    tags = [_convertor.structure(item['tag'], Tag)
            for item in response['Items']]

    paging_key = None
    if 'LastEvaluatedKey' in response:
        paging_key = dict(
            created=response['LastEvaluatedKey']['data'],
            name=response['LastEvaluatedKey']['pk'].split('#')[1]
        )

    return PageableList(items=tags, paging_key=paging_key)


def get_published_post(slug, on_not_found):
    post = get_post(slug, on_not_found)
    if not post.published:
        on_not_found()
    else:
        return post


def _get_post_tag_items(slug):
    response = _conn.table.query(
        KeyConditionExpression='pk = :pk and begins_with(sk, :sk_prefix)',
        ExpressionAttributeValues={
            ':pk': f'post#{slug}',
            ':sk_prefix': '#post#published#tag#'
        }
    )
    if 'LastEvaluatedKey' in response:
        raise ValueError('LastEvaluatedKey not yet supported')
    return response['Items']


def _get_tag_name(post_tag_item):
    return post_tag_item['sk'].split('#')[4]


def update_post(post):
    post.version += 1
    tag_items = _get_post_tag_items(post.slug)
    transact_items = []
    for item in tag_items:
        tag_names = [tag.name for tag in post.tags]
        # if the post is unpublished, or is not longer tagged with this
        # tag, delete it
        if not post.published or _get_tag_name(item) not in tag_names:
            transact_items.append(dict(
                Delete=dict(
                    TableName=_table_name,
                    Key=_serialized(pk=item['pk'], sk=item['sk'])
                )
            ))
    transact_items.append(dict(
        Put=dict(
            TableName=_table_name,
            Item=_post_item(post),
            ConditionExpression='version = :version',
            ExpressionAttributeValues={
                ':version': _serializer.serialize(post.version - 1)
            }
        ),
    ))
    if post.published:
        transact_items.append(dict(
            Put=dict(
                TableName=_table_name,
                Item=_published_post_item(post)
            )
        ))
        for tag in post.tags:
            transact_items.append(dict(
                Put=dict(
                    TableName=_table_name,
                    Item=_published_post_tag_item(post, tag)
                )
            ))
    try:
        _conn.client.transact_write_items(
            TransactItems=transact_items
        )
    except _conn.client.exceptions.TransactionCanceledException as e:
        reasons = [reason['Code'] for reason
                   in e.response['CancellationReasons']]
        if 'ConditionalCheckFailed' in reasons:
            raise ConcurrentUpdateException('Concurrent update exception')
        raise e


def update_tag(tag):
    tag.version += 1
    transact_items = []
    transact_items.append(dict(
        Put=dict(
            TableName=_table_name,
            Item=_tag_item(tag),
            ConditionExpression='version = :version',
            ExpressionAttributeValues={
                ':version': _serializer.serialize(tag.version - 1)
            }
        ),
    ))
    try:
        _conn.client.transact_write_items(
            TransactItems=transact_items
        )
    except _conn.client.exceptions.TransactionCanceledException as e:
        reasons = [reason['Code'] for reason
                   in e.response['CancellationReasons']]
        if 'ConditionalCheckFailed' in reasons:
            raise ConcurrentUpdateException('Concurrent update exception')
        raise e


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


def _get_items(pk):
    response = _conn.table.query(
        KeyConditionExpression='pk = :pk',
        ExpressionAttributeValues={
            ':pk': pk
        }
    )
    if 'LastEvaluatedKey' in response:
        raise ValueError('LastEvaluatedKey not yet supported')
    return response['Items']


def delete_post(slug):
    _delete_all(_get_items(pk=f'post#{slug}'))


def delete_tag(name):
    _delete_all(_get_items(pk=f'tag#{name}'))
