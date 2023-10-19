import flask

from flask import request

from . import db
from . import forms
from . import utils


bp = flask.Blueprint('blog_admin', __name__, url_prefix='/admin')


@bp.get('/posts/')
@utils.pageable('blog/admin/list.html')
def list(paging_key):
    pageable = db.get_all_posts(paging_key=paging_key)
    return dict(posts=pageable.items), pageable.paging_key


@bp.route('/posts/add/', methods=['GET', 'POST'])
def add_post():
    form = forms.NewPostForm(request.form)
    if request.method == 'POST' and form.validate():
        img = db.Image(src='', alt='', title='')
        post = db.Post(slug=form.slug.data, title=form.title.data,
                       body=form.body.data, tags=[], main_image=img,
                       published=form.published.data)
        try:
            db.save_post(post)
            flask.flash('Post created successfully', 'success')
            return flask.redirect(flask.url_for('blog_admin.view_post',
                                                slug=post.slug))
        except db.DuplicateKeyException:
            flask.flash('Slug already exists', 'error')
    return flask.render_template('blog/admin/add.html', form=form)


def _post_or_404(slug):
    return db.get_post(slug=slug, on_not_found=utils.abort_404)


@bp.route('/posts/<slug>/edit/', methods=['GET', 'POST'])
def edit_post(slug):
    post = _post_or_404(slug)
    form = forms.EditPostForm(request.form, post)
    if request.method == 'POST' and form.validate():
        form.populate_obj(post)
        try:
            db.update_post(post)
            flask.flash('Post updated successfully', 'success')
            return flask.redirect(flask.url_for('blog_admin.view_post',
                                                slug=slug))
        except db.ConcurrentUpdateException:
            flask.flash('Unable to update post. This post is out-of-date, '
                        'please refresh and try again', 'error')

    return flask.render_template('blog/admin/edit.html', form=form, post=post)


@bp.get('/posts/<slug>/')
def view_post(slug):
    post = _post_or_404(slug)
    return flask.render_template('blog/admin/view.html', post=post)


@bp.route('/posts/<slug>/', methods=['DELETE'])
def delete_post(slug):
    db.delete_post(slug=slug)
    flask.flash('Post deleted successfully', 'success')
    return flask.redirect(flask.url_for('blog_admin.list'), 303)
