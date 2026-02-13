import html.parser
import re

import bs4 as bs
from django.test.html import HTMLParseError, parse_html


# Optional html5lib support for strict validation
try:
    import html5lib
    from html5lib.html5parser import ParseError as HTML5ParseError

    HAS_HTML5LIB = True
except ImportError:
    html5lib = None
    HTML5ParseError = None
    HAS_HTML5LIB = False


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
            if attr[1] in (None, True):
                self.result.append(f" {attr[0]}")
            else:
                self.result.append(f' {attr[0]}="{attr[1]}"')
        self.result.append(">")

    def handle_startendtag(self, tag, attrs):
        self.result.append(f"<{tag}")
        for attr in attrs:
            if attr[1] in (None, True):
                self.result.append(f" {attr[0]}")
            else:
                self.result.append(f' {attr[0]}="{attr[1]}"')
        self.result.append("/>")

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
            else:
                # Normalize whitespace in attribute values
                # Collapse multiple spaces/tabs/newlines to single space
                # and strip leading/trailing whitespace
                value = tag[attr]
                if isinstance(value, str):
                    normalized_value = re.sub(r"\s+", " ", value).strip()
                    tag[attr] = normalized_value
                elif isinstance(value, list):
                    # Handle attributes that can have multiple values (like class)
                    tag[attr] = [re.sub(r"\s+", " ", v).strip() for v in value]

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
    # Default HTML validation mode for all assertions in this test class
    # Can be overridden in subclasses or per-test
    # If None, falls back to Django setting ASSERT_ELEMENT_HTML_MODE (defaults to True)
    assert_element_html_mode = None

    def _get_html_validation_mode(self):
        """
        Get the HTML validation mode from the priority chain:
        1. Class attribute (if not None)
        2. Django setting ASSERT_ELEMENT_HTML_MODE (if exists)
        3. Default (True - standard validation)
        """
        # Check class attribute first
        if self.assert_element_html_mode is not None:
            return self.assert_element_html_mode

        # Check Django settings
        try:
            from django.conf import settings

            return getattr(settings, "ASSERT_ELEMENT_HTML_MODE", True)
        except (ImportError, AttributeError):
            # Django not available or settings not configured
            return True

    def assertElementContains(  # noqa
        self,
        request,
        html_element="",
        element_text="",
        html=None,
    ):
        """
        Assert that an element contains expected HTML content.

        Args:
            request: Django response object or HTML string
            html_element: CSS selector for the element to find
            element_text: Expected HTML content
            html: HTML validation mode (priority order):
                1. Explicit parameter value (if not None)
                2. Class attribute assert_element_html_mode (if not None)
                3. Django setting ASSERT_ELEMENT_HTML_MODE (if exists)
                4. Default: True (standard validation)

                Valid values:
                - True: Standard validation (Django's parse_html, forgiving like browsers)
                - 'strict': Strict HTML5 validation using html5lib (requires html5lib package)
                - False: No validation

        Raises:
            ImportError: If html='strict' but html5lib is not installed
            AssertionError: If HTML validation fails or content doesn't match
        """
        content = request.content if hasattr(request, "content") else request

        # Determine validation mode from priority chain
        if html is None:
            html = self._get_html_validation_mode()

        # Validate HTML correctness based on mode
        if html == "strict":
            self._validate_html_strict(content)
        elif html:
            self._validate_html_standard(content)
        # else: no validation

        soup = bs.BeautifulSoup(content, "html.parser")
        element = soup.select(html_element)
        if len(element) == 0:
            raise Exception(f"No element found: {html_element}")
        if len(element) > 1:
            elements_preview = []
            for elem in element[:5]:
                elem_str = " ".join(str(elem).split())[:100]
                elements_preview.append(elem_str)
            if len(element) > 5:
                elements_preview.append(f"... and {len(element) - 5} more")
            raise Exception(
                f"More than one element found ({len(element)}): {html_element}\n"
                f"Found elements:\n" + "\n".join(f"  {i + 1}. {e}" for i, e in enumerate(elements_preview))
            )
        soup_1 = bs.BeautifulSoup(element_text, "html.parser")
        element_txt = sanitize_html(element[0].prettify())
        soup_1_txt = sanitize_html(soup_1.prettify())
        self.assertEqual(element_txt, soup_1_txt)

    def _validate_html_standard(self, content):
        """Standard HTML validation using Django's parse_html (browser-like)."""
        content_str = content.decode() if isinstance(content, bytes) else content
        try:
            parse_html(content_str)
        except HTMLParseError as e:
            self.fail(f"Response content is not valid HTML: {e}")

    def _validate_html_strict(self, content):
        """
        Strict HTML5 validation using html5lib.

        Raises ImportError if html5lib is not installed.
        """
        if not HAS_HTML5LIB:
            raise ImportError(
                "html='strict' requires html5lib package. "
                "Install it with: pip install html5lib\n"
                "Or use html=True for standard validation."
            )

        content_str = content.decode() if isinstance(content, bytes) else content
        content_stripped = content_str.strip()

        # Ensure DOCTYPE for html5lib (only add if not present)
        if not content_stripped.startswith("<!DOCTYPE") and not content_stripped.upper().startswith("<!DOCTYPE"):
            content_str = "<!DOCTYPE html>" + content_str

        parser = html5lib.HTMLParser(strict=True)
        try:
            parser.parse(content_str)
        except HTML5ParseError as e:
            self.fail(f"Response content failed strict HTML5 validation: {e}")


class StrictAssertElementMixin(AssertElementMixin):
    """
    Convenience mixin that uses strict HTML5 validation by default.

    Equivalent to setting assert_element_html_mode = 'strict' on your test class.
    Requires html5lib to be installed: pip install html5lib

    Example:
        from assert_element import StrictAssertElementMixin
        from django.test import TestCase

        class MyTests(StrictAssertElementMixin, TestCase):
            def test_something(self):
                # Uses strict validation by default
                self.assertElementContains(response, 'div', '<div>...</div>')

                # Can still override per-assertion
                self.assertElementContains(response, 'p', '<p>...</p>', html=True)
    """

    assert_element_html_mode = "strict"
