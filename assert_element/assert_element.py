import html.parser
import re

import bs4 as bs

BOOLEAN_ATTRIBUTES = {
    "allowfullscreen",
    "async",
    "autofocus",
    "autoplay",
    "checked",
    "controls",
    "default",
    "defer",
    "disabled",
    "formnovalidate",
    "hidden",
    "ismap",
    "itemscope",
    "loop",
    "multiple",
    "muted",
    "nomodule",
    "novalidate",
    "open",
    "playsinline",
    "readonly",
    "required",
    "reversed",
    "selected",
}

class MyHTMLFormatter(html.parser.HTMLParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = []

    def handle_starttag(self, tag, attrs):
        self.result.append(f"<{tag}")
        for attr in attrs:
            if attr[1] is None:
                self.result.append(f" {attr[0]}")
            else:
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
    """
    Sanitize HTML string for reliable comparison.

    Aggressively normalizes cosmetic whitespace differences (multiple spaces,
    tabs, newlines, attribute spacing) while preserving semantically meaningful
    structural differences. Focuses on HTML meaning rather than formatting.
    """
    # First, handle self-closing vs explicit closing tag normalization
    # Use BeautifulSoup for structural normalization
    soup = bs.BeautifulSoup(html_str, "html.parser")
    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if attr in BOOLEAN_ATTRIBUTES:
                tag[attr] = None

    # Collapse standard whitespace in text nodes but leave attribute values and
    # non-breaking spaces untouched so their semantics are preserved
    for text in soup.find_all(string=True):
        collapsed = re.sub(r"[ \t\r\n]+", " ", text)
        text.replace_with(collapsed)

    structure_normalized = str(soup)

    # Normalize line endings
    normalized = structure_normalized.replace("\r\n", "\n").replace("\r", "\n")

    # Return canonical HTML with cosmetic whitespace normalized
    return pretty_print_html(normalized.strip())


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
