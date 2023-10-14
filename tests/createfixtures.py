import os

import bloggy.db as db
import factories


os.environ['AWS_ACCESS_KEY_ID'] = 'foo'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'bar'
db.connect(use_local=True)

db.truncate()

for _ in range(100):
    post = factories.PostFactory()
    db.save_post(post)
