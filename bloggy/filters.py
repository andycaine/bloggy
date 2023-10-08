import bleach
import markdown
import markupsafe


def md_to_html(md):
    allowed_tags = ['p', 'a', 'strong', 'li', 'em', 'ol', 'ul', 'h1', 'h2',
                    'h3']
    return markupsafe.Markup(bleach.clean(markdown.markdown(md),
                                          tags=allowed_tags))


def first_para(html):
    return markupsafe.Markup(html[:html.find('</p>') + 4])
