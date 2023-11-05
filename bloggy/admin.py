import flask

from flask import request

from . import db
from . import forms
from . import utils


bp = flask.Blueprint('blog_admin', __name__, url_prefix='/admin')


@bp.get('/posts/')
@utils.pageable('blog/admin/posts/list.html')
def list_posts(paging_key):
    pageable = db.get_all_posts(paging_key=paging_key)
    return dict(posts=pageable.items), pageable.paging_key


@bp.route('/posts/add/', methods=['GET', 'POST'])
def add_post():
    form = forms.NewPostForm(request.form)

    if request.method == 'POST' and form.validate():
        img = db.Image(src='', alt='', title='')
        tags = form.tags.data or []
        post = db.Post(slug=form.slug.data, title=form.title.data,
                       body=form.body.data, tags=tags,
                       main_image=img, published=form.published.data)

        try:
            db.save_post(post)
            flask.flash('Post created successfully', 'success')
            return flask.redirect(flask.url_for('blog_admin.view_post',
                                                slug=post.slug))
        except db.DuplicateKeyException:
            flask.flash('Slug already exists', 'error')
    return flask.render_template('blog/admin/posts/add.html', form=form)


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

    return flask.render_template('blog/admin/posts/edit.html',
                                 form=form,
                                 post=post)


@bp.get('/posts/<slug>/')
def view_post(slug):
    post = _post_or_404(slug)
    return flask.render_template('blog/admin/posts/view.html', post=post)


@bp.route('/posts/<slug>/', methods=['DELETE'])
def delete_post(slug):
    db.delete_post(slug=slug)
    flask.flash('Post deleted successfully', 'success')
    return flask.redirect(flask.url_for('blog_admin.list_posts'), 303)


@bp.get('/tags/')
@utils.pageable('blog/admin/tags/list.html')
def list_tags(paging_key):
    pageable = db.get_all_tags(paging_key=paging_key)
    return dict(tags=pageable.items), pageable.paging_key


@bp.route('/tags/add/', methods=['GET', 'POST'])
def add_tag():
    form = forms.NewTagForm(request.form)
    if request.method == 'POST' and form.validate():
        tag = db.Tag(name=form.name.data, label=form.label.data)
        try:
            db.save_tag(tag)
            flask.flash('Tag created successfully', 'success')
            return flask.redirect(flask.url_for('blog_admin.view_tag',
                                                name=tag.name))
        except db.DuplicateKeyException:
            flask.flash('Name already exists', 'error')
    return flask.render_template('blog/admin/tags/add.html', form=form)


def _tag_or_404(name):
    return db.get_tag(name=name, on_not_found=utils.abort_404)


@bp.route('/tags/<name>/edit/', methods=['GET', 'POST'])
def edit_tag(name):
    tag = _tag_or_404(name)
    form = forms.EditTagForm(request.form, tag)
    if request.method == 'POST' and form.validate():
        form.populate_obj(tag)
        try:
            db.update_tag(tag)
            flask.flash('Tag updated successfully', 'success')
            return flask.redirect(flask.url_for('blog_admin.view_tag',
                                                name=name))
        except db.ConcurrentUpdateException:
            flask.flash('Unable to update tag. This tag is out-of-date, '
                        'please refresh and try again', 'error')

    return flask.render_template('blog/admin/tags/edit.html',
                                 form=form,
                                 tag=tag)


@bp.get('/tags/<name>/')
def view_tag(name):
    tag = _tag_or_404(name)
    return flask.render_template('blog/admin/tags/view.html', tag=tag)


@bp.route('/tags/<name>/', methods=['DELETE'])
def delete_tag(name):
    db.delete_tag(name=name)
    flask.flash('Tag deleted successfully', 'success')
    return flask.redirect(flask.url_for('blog_admin.list_tags'), 303)
