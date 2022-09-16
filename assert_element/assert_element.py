import re

import bs4 as bs


def sanitize_html(html_str):
    """Sanitize HTML string"""
    return re.sub(r"[\n\r \t]+", " ", html_str).strip()


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
