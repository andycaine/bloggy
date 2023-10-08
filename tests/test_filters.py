import bloggy.filters as filters


def test_md_to_html_empty_string():
    assert '' == filters.md_to_html('')


def test_md_to_html_converts_md_to_html():
    assert '<h1>Title</h1>\n<p>Body</p>' == filters.md_to_html('#Title\nBody')


def test_md_to_html_md_with_html():
    html = '<h1>Title</h1>\n<p>Body</p>'
    assert html == filters.md_to_html(html)


def test_md_to_html_md_with_unsafe_html():
    html = '<script>alert("XSS")</script>'
    expected = '&lt;script&gt;alert("XSS")&lt;/script&gt;'
    assert expected == filters.md_to_html(html)


def test_first_para_returns_first_para():
    html = '<p>First para</p><p>Second para</p>'
    assert '<p>First para</p>' == filters.first_para(html)


def test_first_para_empty_string():
    assert '' == filters.first_para('')
