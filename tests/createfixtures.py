import json
import os

import bloggy.db as db

os.environ['AWS_ACCESS_KEY_ID'] = 'foo'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'bar'
db.connect(use_local=True)

db.truncate()

with open('posts.json', 'r') as f:
    posts = json.load(f)
    for unstructured in posts:
        post = db._convertor.structure(unstructured, db.Post)
        db.save_post(post)
