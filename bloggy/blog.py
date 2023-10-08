import flask

import bloggy.db as db


bp = flask.Blueprint('blog', __name__, url_prefix='/blog')


@bp.get('/')
def list():
    tag = flask.request.args.get('tag', None)
    posts = db.get_all_published_posts(tag)
    return flask.render_template('blog/list.html', posts=posts)


@bp.get('/<slug>/')
def show_post(slug):
    post = db.get_published_post(slug, lambda: flask.abort(404))
    return flask.render_template('blog/post.html', post=post)
