import factory

import bloggy.db as db


class TagFactory(factory.Factory):
    class Meta:
        model = db.Tag

    name = factory.Sequence(lambda n: 'tag-%d' % n)
    label = factory.Sequence(lambda n: 'Tag %d' % n)


class ImageFactory(factory.Factory):
    class Meta:
        model = db.Image

    src = factory.Faker('image_url')
    alt = factory.Faker('sentence', nb_words=5)
    title = factory.Faker('sentence', nb_words=5)


class PostFactory(factory.Factory):
    class Meta:
        model = db.Post

    slug = factory.Sequence(lambda n: 'post-%d' % n)
    title = factory.Sequence(lambda n: 'Post %d' % n)
    body = factory.Faker('sentence', nb_words=100)
    published = factory.Faker('pybool')
    created = factory.Faker('date_time')
    main_image = factory.SubFactory(ImageFactory)
    tags = [TagFactory(), TagFactory(), TagFactory()]
