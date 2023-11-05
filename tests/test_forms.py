import dataclasses

import wtforms
from werkzeug.datastructures import MultiDict

from bloggy import forms


@dataclasses.dataclass
class Tag:
    name: str
    label: str


@dataclasses.dataclass
class Obj:
    tags: list[Tag]
    tag: Tag = None


def test_select_multiple_objects_field():
    foo = Tag('foo', 'Foo')
    bar = Tag('bar', 'Bar')
    tags = [foo, bar]

    def fetch_tags():
        return tags

    class F(wtforms.Form):
        tags = forms.SelectMultipleObjectsField(
            "Tags",
            fetch_objects_fn=fetch_tags,
            option_value_attr='name',
            option_text_attr='label'
        )

    obj = Obj(tags=[bar])
    form = F(MultiDict([]), obj=obj)

    assert form.tags.choices == [('foo', 'Foo'), ('bar', 'Bar')]
    assert form.tags() == '<select id="tags" multiple name="tags">' \
        '<option value="foo">Foo</option>' \
        '<option selected value="bar">Bar</option>' \
        '</select>'

    post_data = MultiDict([('tags', 'bar'), ('tags', 'foo')])
    form = F(post_data, obj)
    valid = form.validate()
    assert form.errors == {}
    assert valid

    form.populate_obj(obj)
    assert obj.tags == [bar, foo]
