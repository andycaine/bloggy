import flask

from . import exceptions


def get_object_or_404(getter, id):
    try:
        return getter(id)
    except exceptions.ObjectDoesNotExist:
        flask.abort(404)
