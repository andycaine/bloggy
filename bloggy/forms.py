import wtforms

from . import db


url_component_regexp = wtforms.validators.Regexp(
    r'^[a-zA-Z0-9_\-]+$',
    message='Only lowercase alphanumeric characters, underscores and dashes '
            'are allowed'
)

basic_string_regexp = wtforms.validators.Regexp(
    r'^[a-zA-Z0-9_ \-]+$',
    message='Only alphanumeric characters, underscores, spaces and '
            'dashes are allowed')


class EditPostForm(wtforms.Form):
    title = wtforms.StringField('Title', validators=[
        wtforms.validators.DataRequired(),
        wtforms.validators.Length(max=255),
        basic_string_regexp
    ])
    main_image = wtforms.FileField('Main image')
    body = wtforms.TextAreaField('Body', validators=[
        wtforms.validators.DataRequired()
    ])
    published = wtforms.BooleanField('Published', default=False)
    version = wtforms.IntegerField(
        'Version', default=1, widget=wtforms.widgets.HiddenInput(),
        validators=[
            wtforms.validators.DataRequired(),
            wtforms.validators.NumberRange(min=1)
        ]
    )


def unique_post_check(form, field):
    def no_op():
        pass
    post = db.get_post(slug=field.data, on_not_found=no_op)
    if post is not None:
        raise wtforms.validators.ValidationError('Slug already exists')


class NewPostForm(EditPostForm):
    slug = wtforms.StringField('Slug', validators=[
        wtforms.validators.DataRequired(),
        wtforms.validators.Length(max=255),
        url_component_regexp,
        unique_post_check
    ])
