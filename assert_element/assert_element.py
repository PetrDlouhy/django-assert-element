import html.parser
import re

import bs4 as bs


class MyHTMLFormatter(html.parser.HTMLParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = []

    def handle_starttag(self, tag, attrs):
        self.result.append(f"<{tag}")
        for attr in attrs:
            self.result.append(f' {attr[0]}="{attr[1]}"')
        self.result.append(">")

    def handle_endtag(self, tag):
        self.result.append(f"</{tag}>")

    def handle_data(self, data):
        self.result.append(data)

    def prettify(self):
        return "\n".join(self.result)


def pretty_print_html(html_str):
    """Pretty print HTML string"""
    formatter = MyHTMLFormatter()
    formatter.feed(html_str)
    return formatter.prettify()


def sanitize_html(html_str):
    """Sanitize HTML string"""
    sanitized = re.sub(r"[\n\r \t]+", " ", html_str).strip()
    return pretty_print_html(sanitized)


class AssertElementMixin:
    def assertElementContains(  # noqa
        self,
        request,
        html_element="",
        element_text="",
    ):
        content = request.content if hasattr(request, "content") else request
        soup = bs.BeautifulSoup(content, "html.parser")
        element = soup.select(html_element)
        if len(element) == 0:
            raise Exception(f"No element found: {html_element}")
        if len(element) > 1:
            raise Exception(f"More than one element found: {html_element}")
        soup_1 = bs.BeautifulSoup(element_text, "html.parser")
        element_txt = sanitize_html(element[0].prettify())
        soup_1_txt = sanitize_html(soup_1.prettify())
        self.assertEqual(element_txt, soup_1_txt)
