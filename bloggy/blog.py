import flask

import bloggy.db as db
import bloggy.utils as utils


bp = flask.Blueprint('blog', __name__, url_prefix='/blog')


@bp.get('/')
@utils.pageable('blog/list.html')
def list(paging_key):
    tag = flask.request.args.get('tag', None)
    pageable = db.get_published_posts(tag=tag, paging_key=paging_key)
    return dict(posts=pageable.items), pageable.paging_key


@bp.get('/<slug>/')
def show_post(slug):
    post = db.get_published_post(slug=slug, on_not_found=utils.abort_404)
    return flask.render_template('blog/post.html', post=post)
