import os

import awsgi
import flask

from . import filters
from . import db


def create_app():
    app = flask.Flask(__name__, instance_relative_config=True)
    app.config.from_prefixed_env(prefix='BLOGGY')

    env = app.config.get('ENV', '')
    if env == 'dev':
        os.environ['AWS_ACCESS_KEY_ID'] = 'foo'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'bar'
        db.connect(use_local=True)
    else:
        db.connect()

    @app.route('/')
    def index():
        return flask.redirect('/blog/')

    @app.route('/ping/')
    def ping():
        return 'pong'

    @app.errorhandler(404)
    def page_not_found(e):
        return flask.render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return flask.render_template('500.html'), 500

    @app.template_filter('md_to_html')
    def md_to_html(text):
        return filters.md_to_html(text)

    @app.template_filter('first_para')
    def first_para(text):
        return filters.first_para(text)

    from . import blog
    app.register_blueprint(blog.bp)

    from . import admin
    app.register_blueprint(admin.bp)

    return app


_app = create_app()


def handler(event, context):
    return awsgi.response(_app, event, context)
