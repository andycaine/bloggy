import flask

import bloggy.db as db
import bloggy.utils as utils


bp = flask.Blueprint('blog', __name__, url_prefix='/blog')


@bp.get('/')
def list():
    tag = flask.request.args.get('tag', None)
    paging_tokens = flask.request.args.get('pt', None)
    try:
        page = int(flask.request.args.get('page', 1))
    except ValueError:
        page = 1

    paging_keys = utils.from_url_token(paging_tokens, {})
    paging_key = None
    if paging_keys and page > 1 and str(page) in paging_keys:
        paging_key = paging_keys[str(page)]

    # if paging_key is None, make sure page = 1
    if paging_key is None:
        page = 1

    pageable = db.get_published_posts(
        tag=tag,
        paging_key=paging_key
    )
    paging_keys[page + 1] = pageable.paging_key
    new_paging_tokens = utils.to_url_token(paging_keys)

    return flask.render_template(
        'blog/list.html',
        posts=pageable.items,
        prev=page - 1 if page > 0 else None,
        next=page + 1 if pageable.paging_key else None,
        paging_tokens=new_paging_tokens
    )


@bp.get('/<slug>/')
def show_post(slug):
    post = db.get_published_post(slug=slug, on_not_found=utils.abort_404)
    return flask.render_template('blog/post.html', post=post)
