import wtforms

from . import db


class SelectMultipleField(wtforms.SelectMultipleField):
    """Tweak the behaviour of wtforms.SelectMultipleField so that is behaves
    more like wtforms.SelectField (as documented).

    In particular, this implementation:
    - works with choices specified as strings to be coerced
    - doesn't require that coerced values are hashable
    - doesn't attempt to coerce None values
    - doesn't override obj data when formdata isn't provided for a field
    """

    def pre_validate(self, form):
        if not self.validate_choice or not self.data:
            return

        if self.choices is None:
            raise TypeError(self.gettext("Choices cannot be None."))

        acceptable = [self.coerce(c[0]) for c in self.iter_choices()]
        if any(d not in acceptable for d in self.data):
            raise wtforms.ValidationError('Not a valid choice')

    def process_data(self, value):
        try:
            self.data = list(self.coerce(v) if v is not None else v
                             for v in value)
        except (ValueError, TypeError):
            self.data = None

    def process_formdata(self, valuelist):
        if not valuelist:
            return
        super().process_formdata(valuelist)


class SelectMultipleObjectsField(SelectMultipleField):

    def __init__(self, label=None, validators=None, fetch_objects_fn=None,
                 option_value_attr=None, option_text_attr=None, **kwargs):
        super().__init__(label, validators, **kwargs)
        self.fetch_objects_fn = fetch_objects_fn
        self.option_value_attr = option_value_attr
        self.option_text_attr = option_text_attr

    def process(self, formdata, *args, **kwargs):
        objects = self.fetch_objects_fn()
        self.choices = [(
            getattr(o, self.option_value_attr),
            getattr(o, self.option_text_attr)
        ) for o in objects]
        mapping = {getattr(o, self.option_value_attr): o for o in objects}

        def coerce_to_obj(s):
            if isinstance(s, str):
                return mapping[s]
            # if it's not a string, assume it's already an object and just
            # return it
            return s

        self.coerce = coerce_to_obj
        super().process(formdata, *args, **kwargs)


url_component_regexp = wtforms.validators.Regexp(
    r'^[a-zA-Z0-9_\-]+$',
    message='Only lowercase alphanumeric characters, underscores and dashes '
            'are allowed'
)

basic_string_regexp = wtforms.validators.Regexp(
    r'^[a-zA-Z0-9_ \-]+$',
    message='Only alphanumeric characters, underscores, spaces and '
            'dashes are allowed')


def _fetch_tags():
    return db.get_all_tags(limit=100).items


class EditPostForm(wtforms.Form):
    title = wtforms.StringField('Title', validators=[
        wtforms.validators.DataRequired(),
        wtforms.validators.Length(max=255),
        basic_string_regexp
    ])
    main_image = wtforms.FileField('Main image')
    body = wtforms.TextAreaField('Body', validators=[
        wtforms.validators.DataRequired(),
        wtforms.validators.Length(max=128*1024)
        # TODO: some sort of basic html / md validator
    ])
    tags = SelectMultipleObjectsField('Tags',
                                      fetch_objects_fn=_fetch_tags,
                                      option_value_attr='name',
                                      option_text_attr='label')
    published = wtforms.BooleanField('Published', default=False)
    version = wtforms.IntegerField(
        'Version', default=1, widget=wtforms.widgets.HiddenInput(),
        validators=[
            wtforms.validators.DataRequired(),
            wtforms.validators.NumberRange(min=1)
        ]
    )


def no_op():
    pass


def unique_post_check(form, field):
    post = db.get_post(slug=field.data, on_not_found=no_op)
    if post is not None:
        raise wtforms.validators.ValidationError('Slug already exists')


def unique_tag_check(form, field):
    tag = db.get_tag(name=field.data, on_not_found=no_op)
    if tag is not None:
        raise wtforms.validators.ValidationError('Tag already exists')


class NewPostForm(EditPostForm):
    slug = wtforms.StringField('Slug', validators=[
        wtforms.validators.DataRequired(),
        wtforms.validators.Length(max=255),
        url_component_regexp,
        unique_post_check
    ])


class EditTagForm(wtforms.Form):
    label = wtforms.StringField('Title', validators=[
        wtforms.validators.DataRequired(),
        wtforms.validators.Length(max=255),
        basic_string_regexp
    ])
    version = wtforms.IntegerField(
        'Version', default=1, widget=wtforms.widgets.HiddenInput(),
        validators=[
            wtforms.validators.DataRequired(),
            wtforms.validators.NumberRange(min=1)
        ]
    )


class NewTagForm(EditTagForm):
    name = wtforms.StringField('Name', validators=[
        wtforms.validators.DataRequired(),
        wtforms.validators.Length(max=255),
        url_component_regexp,
        unique_tag_check
    ])
