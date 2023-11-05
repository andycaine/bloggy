import os

import bloggy.db as db
import factories


os.environ['AWS_ACCESS_KEY_ID'] = 'foo'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'bar'
db.connect(use_local=True)

db.truncate()

tags = []
for _ in range(5):
    tag = factories.TagFactory()
    tags.append(tag)
    db.save_tag(tag)


for _ in range(100):
    post = factories.PostFactory(tags=tags)
    db.save_post(post)
