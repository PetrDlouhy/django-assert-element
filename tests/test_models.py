#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for assert_element package.

This module contains comprehensive tests for the assert_element functionality,
including integration tests for assertElementContains and detailed analysis
of HTML whitespace sanitization behavior.
"""

import unittest

from django.test import TestCase

from assert_element import HAS_HTML5LIB, AssertElementMixin, StrictAssertElementMixin
from assert_element.assert_element import sanitize_html


class AssertElementIntegrationTests(AssertElementMixin, TestCase):
    def test_something(self):
        response = self.client.get("admin")
        self.assertElementContains(
            response,
            "title",
            "<title>Not Found</title>",
        )

    def test_spaces_dont_matter(self):
        """Test that sanitization works on blank spaces"""
        response = self.client.get("admin")
        self.assertElementContains(
            response,
            "title",
            "<title>Not \r\n\t      Found</title>",
        )

    def test_direct_content(self):
        """Test that first attribute can be directly content"""
        self.assertElementContains(
            "<title>Not  Found</title>",
            "title",
            "<title>Not Found</title>",
        )

    def test_element_not_found(self):
        """Element not found raises Exception"""
        with self.assertRaisesRegex(Exception, "No element found: title"):
            self.assertElementContains(
                "",
                "title",
                "<title>Not Found</title>",
            )

    def test_element_differs(self):
        """Element content differs, assertRaisesRegex with detailed diff."""

        expected_message_regex = "-  Myy div \n\\?    - *\n\\+  My div"

        with self.assertRaisesRegex(AssertionError, expected_message_regex):
            self.assertElementContains(
                '<html><div id="my-div">Myy div</div></html>',
                'div[id="my-div"]',
                '<div id="my-div">My div</div>',
            )

    def test_multiple_elements_found(self):
        """Multiple elements found are raising Exception"""
        with self.assertRaisesRegex(Exception, r"More than one element found \(\d+\): title"):
            self.assertElementContains(
                "<title>Not Found</title><title>Not Found</title>",
                "title",
                "<title>Not Found</title>",
            )

    def test_html_validation_with_wrong_closing_tag(self):
        """
        Invalid HTML with wrong closing tag should fail when html=True.

        Django's parse_html catches structural errors like mismatched closing tags,
        similar to assertContains(html=True).
        """
        invalid_html = "<html><body><div>Test</span></div></body></html>"

        with self.assertRaisesRegex(AssertionError, "Response content is not valid HTML"):
            self.assertElementContains(
                invalid_html,
                "div",
                "<div>Test</div>",
                html=True,
            )

    def test_html_validation_with_unexpected_closing_tag(self):
        """Invalid HTML with unexpected closing tag should fail when html=True"""
        invalid_html = "<html><body></div></body></html>"

        with self.assertRaisesRegex(AssertionError, "Response content is not valid HTML"):
            self.assertElementContains(
                invalid_html,
                "body",
                "<body></body>",
                html=True,
            )

    def test_html_validation_disabled(self):
        """
        Invalid HTML should pass when html=False.

        When validation is disabled, we can work with malformed HTML
        that BeautifulSoup can still parse.
        """
        invalid_html = "<html><body><div>Test</span></div></body></html>"

        # Should not raise - HTML validation is disabled
        # BeautifulSoup will parse it but parse_html won't validate it
        self.assertElementContains(
            invalid_html,
            "div",
            "<div>Test</div>",
            html=False,
        )

    def test_html_validation_with_valid_html(self):
        """Valid HTML should pass validation"""
        valid_html = "<html><body><div><p>Test</p></div></body></html>"

        # Should not raise - HTML is valid
        self.assertElementContains(
            valid_html,
            "p",
            "<p>Test</p>",
            html=True,
        )

    def test_html_validation_default_enabled(self):
        """
        HTML validation should be enabled by default.

        Without explicit html=False, validation should catch structural HTML errors.
        """
        invalid_html = "<html><body><div>Test</span></div></body></html>"

        # Without html parameter, validation should be enabled by default
        with self.assertRaisesRegex(AssertionError, "Response content is not valid HTML"):
            self.assertElementContains(
                invalid_html,
                "div",
                "<div>Test</div>",
            )

    def test_html_validation_auto_closed_tags_allowed(self):
        """
        Auto-closed tags should be allowed (browser-like behavior).

        Django's parse_html is forgiving like browsers - it auto-closes
        unclosed tags. This is intentional to match assertContains behavior.
        """
        # Unclosed <p> tag - browser and Django will auto-close it
        html_with_unclosed = "<html><body><div><p>Test</div></body></html>"

        # Should not raise - auto-closing is allowed
        self.assertElementContains(
            html_with_unclosed,
            "p",
            "<p>Test</p>",
            html=True,
        )


class SanitizeHtmlTests(TestCase):
    """
    Tests for sanitize_html function behavior.

    The sanitize_html function normalizes HTML whitespace to enable reliable
    HTML comparisons in assertElementContains. However, overly aggressive
    normalization can cause false positives where genuinely different HTML
    is treated as identical.

    These tests document current behavior and identify problematic cases
    where whitespace differences should be preserved but aren't.
    """

    def setUp(self):
        self.sanitize_html = sanitize_html

    def test_whitespace_before_closing_tag_normalization(self):
        """
        Test whitespace handling before closing tags.

        Verifies that cosmetic whitespace differences (like extra spaces/newlines
        before closing tags) are properly normalized, as these don't affect
        HTML rendering or semantic meaning.
        """
        html_with_space = '<img alt="Test" src="test.jpg">\n \n</img>'
        html_without_space = '<img alt="Test" src="test.jpg">\n</img>'

        self.assertNotEqual(html_with_space, html_without_space)

        sanitized_with = self.sanitize_html(html_with_space)
        sanitized_without = self.sanitize_html(html_without_space)

        # These should be normalized to the same result since the whitespace
        # difference is cosmetic and doesn't affect HTML meaning
        self.assertEqual(
            sanitized_with,
            sanitized_without,
            "Cosmetic whitespace differences should be normalized away",
        )

    def test_whitespace_normalization_comprehensive(self):
        """
        Test that sanitize_html preserves semantically meaningful HTML differences.

        Focuses only on whitespace differences that actually change HTML meaning
        or rendering, ignoring cosmetic variations that browsers treat identically.
        This prevents false positive test failures while catching real issues.
        """
        test_cases = [
            # Cases where whitespace/sanitization differences could have semantic meaning:
            # 1. Whitespace between inline elements affects rendering
            (
                "Whitespace affecting inline layout",
                "<span>word1</span><span>word2</span>",  # renders as "word1word2"
                "<span>word1</span> <span>word2</span>",
            ),  # renders as "word1 word2"
            # 2. Leading/trailing whitespace in content
            ("Content whitespace padding", "<p>content</p>", "<p> content </p>"),
            # 3. Whitespace affecting CSS class parsing
            (
                "CSS class whitespace sensitivity",
                '<div class="btn primary">text</div>',  # two classes: "btn" and "primary"
                '<div class="btn-primary">text</div>',
            ),  # one class: "btn-primary"
            # 4. Note: Trailing whitespace in attributes is now normalized away
            # to prevent false test failures from formatting differences.
            # If you need to test for trailing spaces in form values, test the
            # actual form submission behavior instead of HTML markup.
            # 5. Empty content vs whitespace-only content
            (
                "Empty vs whitespace-only content",
                "<div></div>",  # truly empty
                "<div> </div>",
            ),  # contains whitespace
            # Most other whitespace differences are cosmetic and should be normalized:
            # - Multiple spaces/newlines (browser collapses them)
            # - Tabs vs spaces (browser treats identically)
            # - Self-closing vs explicit tags (functionally identical)
            # - Attribute spacing around = signs (irrelevant to HTML meaning)
        ]

        issues_found = []
        preserved_differences = []

        for description, html1, html2 in test_cases:
            with self.subTest(description=description):
                self.assertNotEqual(html1, html2)

                sanitized1 = self.sanitize_html(html1)
                sanitized2 = self.sanitize_html(html2)

                if sanitized1 == sanitized2:
                    issues_found.append((description, html1, html2, sanitized1))
                else:
                    preserved_differences.append((description, html1, html2))

        # Document findings for developers
        if issues_found:
            issue_details = "\n".join(
                [
                    f"  {desc}: {repr(h1)} == {repr(h2)} -> {repr(sanitized)}"
                    for desc, h1, h2, sanitized in issues_found
                ]
            )
            print(f"\nFound {len(issues_found)} whitespace normalization issues:")
            print(issue_details)

        if preserved_differences:
            print(f"\nCorrectly preserved {len(preserved_differences)} differences:")
            for desc, h1, h2 in preserved_differences:
                print(f"  {desc}: {repr(h1)} != {repr(h2)}")

        # FAIL the test if significant normalization issues are found
        # These represent cases where sanitize_html incorrectly treats
        # genuinely different HTML as identical, which can cause false positive test matches
        self.assertEqual(
            len(issues_found),
            0,
            f"Found {len(issues_found)} critical whitespace normalization issues that need fixing:\n"
            f"{issue_details if issues_found else ''}\n\n"
            f"These issues can cause assertElementContains to incorrectly pass when HTML differs.",
        )

    def test_sanitization_edge_cases(self):
        """
        Test edge cases in HTML whitespace sanitization.

        This test documents how sanitize_html handles various edge cases
        including empty elements, mixed whitespace characters, and attribute
        formatting. Understanding this behavior helps developers write
        more reliable HTML assertions.
        """
        edge_cases = [
            ("Empty with space", "<div> </div>"),
            ("Empty with newline", "<div>\n</div>"),
            ("Empty with tab", "<div>\t</div>"),
            ("Mixed whitespace chars", "<p>text\n\r\t text</p>"),
            ("Multiple spaces", "<p>text   text</p>"),
            ("Attribute spacing", '<img  alt="test"  src="file.jpg"  />'),
            ("Compact attributes", '<img alt="test" src="file.jpg"/>'),
            ("Attribute value spaces", '<div title="hello world">content</div>'),
            ("Attribute value multi-spaces", '<div title="hello  world">content</div>'),
        ]

        results = []
        for description, html in edge_cases:
            sanitized = self.sanitize_html(html)
            results.append((description, html, sanitized))

            # Basic sanity check that sanitization doesn't break HTML structure
            self.assertIsInstance(sanitized, str)
            self.assertGreater(len(sanitized), 0)

        # Document results for future reference
        print(f"\nSanitization behavior for {len(edge_cases)} edge cases:")
        for desc, original, sanitized in results:
            print(f"  {desc}:")
            print(f"    Input:  {repr(original)}")
            print(f"    Output: {repr(sanitized)}")

    def test_attribute_value_whitespace_preservation(self):
        """
        Test that whitespace in HTML attribute values is handled correctly.

        Whitespace within attribute values should generally be preserved
        as it can be semantically meaningful (e.g., CSS class names,
        alt text with multiple words).
        """
        test_cases = [
            (
                '<div class="btn primary">text</div>',
                '<div class="btn  primary">text</div>',
            ),
            (
                '<img alt="My Image" src="test.jpg">',
                '<img alt="My  Image" src="test.jpg">',
            ),
            ('<input value="hello world">', '<input value="hello  world">'),
        ]

        for html1, html2 in test_cases:
            with self.subTest(html1=html1, html2=html2):
                sanitized1 = self.sanitize_html(html1)
                sanitized2 = self.sanitize_html(html2)

                # Document whether attribute whitespace is preserved
                if sanitized1 == sanitized2:
                    print(f"Attribute whitespace normalized: {repr(html1)} == {repr(html2)}")
                else:
                    print(f"Attribute whitespace preserved: {repr(html1)} != {repr(html2)}")

    def test_boolean_attribute_normalization(self):
        """Boolean attributes should normalize consistently."""
        variants = [
            "<input disabled>",
            '<input disabled="">',
            '<input disabled="disabled">',
        ]

        sanitized = {self.sanitize_html(html) for html in variants}

        # All representations should collapse to a single canonical form
        self.assertEqual(len(sanitized), 1, sanitized)

    def test_self_closing_tag_normalization(self):
        """Self-closing tags should retain their form after sanitization."""
        cases = [
            [
                '<img src="file.jpg">',
                '<img src="file.jpg"/>',
            ],
            [
                "<br>",
                "<br/>",
            ],
            [
                '<input type="text">',
                '<input type="text"/>',
            ],
        ]

        for variants in cases:
            with self.subTest(variants=variants):
                sanitized = {self.sanitize_html(html) for html in variants}
                self.assertEqual(len(sanitized), 1, sanitized)
                canonical = sanitized.pop()
                self.assertTrue(canonical.strip().endswith("/>"), canonical)

    def test_semantically_meaningful_whitespace_differences(self):
        """
        Test cases where whitespace differences actually matter for HTML semantics.

        These represent edge cases where whitespace can affect rendering or meaning,
        and the sanitization should ideally preserve the differences.
        """
        semantic_whitespace_cases = [
            # 1. Whitespace preservation in text content boundaries
            (
                "Text content boundaries",
                "<p>start</p><p>end</p>",  # "startend" when concatenated
                "<p>start</p> <p>end</p>",
            ),  # "start end" with space
            # 2. Whitespace within text content
            (
                "Internal text whitespace",
                "<span>hello world</span>",  # normal space
                "<span>hello\u00a0world</span>",
            ),  # non-breaking space
            # 3. Attribute value whitespace significance
            (
                "Attribute value internal whitespace",
                '<div title="hello world">text</div>',
                '<div title="hello\tworld">text</div>',
            ),  # tab in attribute value
            # 4. Whitespace affecting element content interpretation
            (
                "Content interpretation",
                "<code>var x=1;</code>",  # no spaces around =
                "<code>var x = 1;</code>",
            ),  # spaces around = (different code)
            # 5. Pre-formatted whitespace simulation
            (
                "Whitespace-sensitive content simulation",
                "<div>line1\nline2</div>",
                "<div>line1\n\nline2</div>",
            ),  # different line spacing
        ]

        print("\nTesting semantically meaningful whitespace differences:")
        semantic_differences_preserved = 0

        for description, html1, html2 in semantic_whitespace_cases:
            with self.subTest(description=description):
                sanitized1 = self.sanitize_html(html1)
                sanitized2 = self.sanitize_html(html2)

                if sanitized1 != sanitized2:
                    semantic_differences_preserved += 1
                    print(f"✓ {description}: Difference preserved")
                else:
                    print(f"✗ {description}: Difference normalized away")
                    print(f"    {repr(html1)} == {repr(html2)}")
                    print(f"    Both -> {repr(sanitized1)}")

        print(
            f"\nPreserved {semantic_differences_preserved}/"
            f"{len(semantic_whitespace_cases)} semantic whitespace differences"
        )

        # This test is informational - it documents current behavior
        # rather than enforcing specific requirements

    def test_multiline_attribute_normalization(self):
        """
        Test that multi-line attribute values are normalized consistently.

        This is a regression test for issues found when multi-line attributes
        (like srcset, data-srcset) are formatted differently but should be
        treated as equivalent.
        """
        # Case 1: data-srcset with multi-line formatting vs single line
        multiline_srcset = """<img
            data-srcset="
                /media/image1.jpg 320w,
                /media/image2.jpg 640w,
                /media/image3.jpg 768w
            "
            src="test.jpg"
        />"""

        singleline_srcset = """<img
            data-srcset=" /media/image1.jpg 320w, /media/image2.jpg 640w, /media/image3.jpg 768w "
            src="test.jpg"
        />"""

        sanitized_multi = self.sanitize_html(multiline_srcset)
        sanitized_single = self.sanitize_html(singleline_srcset)

        self.assertEqual(
            sanitized_multi,
            sanitized_single,
            "Multi-line and single-line srcset should normalize to the same value",
        )

    def test_style_attribute_extra_spaces(self):
        """
        Test that extra spaces in style attributes are normalized.

        Regression test for style attributes with inconsistent spacing.
        """
        style_one_space = '<img style="outline:none; -ms-interpolation-mode:bicubic" />'
        style_two_spaces = '<img style="outline:none;  -ms-interpolation-mode:bicubic" />'

        sanitized_one = self.sanitize_html(style_one_space)
        sanitized_two = self.sanitize_html(style_two_spaces)

        self.assertEqual(
            sanitized_one,
            sanitized_two,
            "Style attributes with different spacing should normalize to the same value",
        )

    def test_title_attribute_multiline_html(self):
        """
        Test that title attributes containing HTML with different formatting normalize consistently.

        Regression test for title attributes that contain HTML (like in Bootstrap tooltips).
        """
        multiline_title = """<span
            title="Quality
                <br/><small class='few-ratings'>
                    Average from
                    <b>only</b>
                    2 ratings
                </small>"
        >5.0</span>"""

        compact_title = """<span
            title="Quality <br/><small class='few-ratings'> Average from <b>only</b> 2 ratings </small>"
        >5.0</span>"""

        sanitized_multi = self.sanitize_html(multiline_title)
        sanitized_compact = self.sanitize_html(compact_title)

        self.assertEqual(
            sanitized_multi,
            sanitized_compact,
            "Title attributes with different HTML formatting should normalize to the same value",
        )

    def test_srcset_with_trailing_spaces(self):
        """
        Test that srcset attributes with trailing spaces/newlines normalize correctly.

        Regression test for srcset attributes that have trailing whitespace.
        """
        srcset_with_trailing = """<source
            srcset="/media/image1.jpg 1024w,
                /media/image2.jpg 512w,
                /media/image3.jpg 256w
            "
            type="image/webp"
        />"""

        srcset_compact = """<source
            srcset=" /media/image1.jpg 1024w, /media/image2.jpg 512w, /media/image3.jpg 256w "
            type="image/webp"
        />"""

        sanitized_trailing = self.sanitize_html(srcset_with_trailing)
        sanitized_compact = self.sanitize_html(srcset_compact)

        self.assertEqual(
            sanitized_trailing,
            sanitized_compact,
            "Srcset attributes with trailing whitespace should normalize consistently",
        )

    def test_real_world_blenderkit_cases(self):
        """
        Test actual cases from BlenderKit that failed in 0.6.0.

        These represent real-world HTML differences that should be tolerated.
        """
        # Case 1: Double space after semicolon in style attribute
        style1 = '<img style="outline:none; -ms-interpolation-mode:bicubic" />'
        style2 = '<img style="outline:none;  -ms-interpolation-mode:bicubic" />'
        self.assertEqual(
            self.sanitize_html(style1),
            self.sanitize_html(style2),
            "Style attributes with different spacing should normalize",
        )

        # Case 2: Multi-line srcset with various indentation
        srcset1 = """<source srcset="
            /img1.jpg 2048w,
                                 /img2.jpg 1024w,
                                /img3.jpg 512w,
                                /img4.jpg 256w"
        />"""

        srcset2 = '<source srcset=" /img1.jpg 2048w, /img2.jpg 1024w, /img3.jpg 512w, /img4.jpg 256w" />'

        self.assertEqual(
            self.sanitize_html(srcset1),
            self.sanitize_html(srcset2),
            "Srcset with irregular indentation should normalize",
        )

        # Case 3: Title attribute with embedded HTML and whitespace
        title1 = """<span title="Quality
                                          <br/><small>
                                              Text
                                          </small>">X</span>"""

        title2 = '<span title="Quality <br/><small> Text </small>">X</span>'

        self.assertEqual(
            self.sanitize_html(title1),
            self.sanitize_html(title2),
            "Title with embedded HTML should normalize whitespace",
        )

    def test_attribute_value_edge_cases(self):
        """Test edge cases in attribute value normalization."""
        # Leading/trailing spaces should be stripped
        html1 = '<div data-value=" test "></div>'
        html2 = '<div data-value="test"></div>'
        self.assertEqual(self.sanitize_html(html1), self.sanitize_html(html2))

        # Multiple internal spaces should collapse to one
        html1 = '<div title="hello    world"></div>'
        html2 = '<div title="hello world"></div>'
        self.assertEqual(self.sanitize_html(html1), self.sanitize_html(html2))

        # Mixed whitespace (spaces, tabs, newlines) should normalize
        html1 = '<div data-text="line1\n\t\tline2"></div>'
        html2 = '<div data-text="line1 line2"></div>'
        self.assertEqual(self.sanitize_html(html1), self.sanitize_html(html2))

    def test_comprehensive_integration(self):
        """
        Integration test with complex real-world HTML.

        Tests that a complex element with multiple attributes and formatting
        differences normalizes correctly.
        """
        html_formatted = """
        <img
            alt="Asset thumbnail"
            class="card-img-top lazy bg-lighter"
            data-sizes="(min-width: 1200px) 640px, (min-width: 992px) 320px"
            data-src="/media/images/test.jpg"
            data-srcset="
                /media/images/test.fill-320x180.jpg 320w,
                /media/images/test.fill-640x360.jpg 640w,
                /media/images/test.fill-768x432.jpg 768w,
                /media/images/test.fill-1024x576.jpg 1024w
            "
            height="40"
            src="/media/images/test.jpg"
            title="Test image"
            width="72"
        />
        """

        html_compact = (
            '<img alt="Asset thumbnail" class="card-img-top lazy bg-lighter" '
            'data-sizes="(min-width: 1200px) 640px, (min-width: 992px) 320px" '
            'data-src="/media/images/test.jpg" '
            'data-srcset=" /media/images/test.fill-320x180.jpg 320w, '
            "/media/images/test.fill-640x360.jpg 640w, "
            "/media/images/test.fill-768x432.jpg 768w, "
            '/media/images/test.fill-1024x576.jpg 1024w " '
            'height="40" src="/media/images/test.jpg" '
            'title="Test image" width="72" />'
        )

        self.assertEqual(
            self.sanitize_html(html_formatted),
            self.sanitize_html(html_compact),
            "Complex HTML with multi-line attributes should normalize",
        )

    def test_attribute_order_independence(self):
        """
        Test that attribute order doesn't matter (already handled by BeautifulSoup).

        Documenting expected behavior for attribute ordering.
        """
        html1 = '<img src="test.jpg" alt="Test" width="100" />'
        html2 = '<img width="100" alt="Test" src="test.jpg" />'

        # BeautifulSoup may reorder, but both should normalize consistently
        sanitized1 = self.sanitize_html(html1)
        sanitized2 = self.sanitize_html(html2)

        # Both should be valid HTML with same attributes
        # Note: order might differ, but that's OK - documenting current behavior
        self.assertIsInstance(sanitized1, str)
        self.assertIsInstance(sanitized2, str)

    def test_quote_style_normalization(self):
        """
        Test that single vs double quotes in attributes are handled.

        BeautifulSoup normalizes these, documenting the behavior.
        """
        # Parser handles this automatically
        html_double = '<div class="test">content</div>'
        html_single = "<div class='test'>content</div>"

        # Both parse correctly
        sanitized_double = self.sanitize_html(html_double)
        sanitized_single = self.sanitize_html(html_single)

        # Should normalize to same result
        self.assertEqual(
            sanitized_double,
            sanitized_single,
            "Quote style should not affect comparison",
        )


class AssertElementStrictValidationTests(AssertElementMixin, TestCase):
    """Tests for strict HTML5 validation using html5lib (optional dependency)."""

    def test_strict_mode_requires_html5lib(self):
        """Test that strict mode fails gracefully without html5lib."""
        if HAS_HTML5LIB:
            self.skipTest("html5lib is installed, cannot test missing dependency")

        with self.assertRaisesRegex(ImportError, "html='strict' requires html5lib"):
            self.assertElementContains(
                "<!DOCTYPE html><html><body><div>Test</div></body></html>",
                "div",
                "<div>Test</div>",
                html="strict",
            )

    @unittest.skipUnless(HAS_HTML5LIB, "html5lib not installed")
    def test_strict_mode_valid_html(self):
        """Strict mode should pass valid HTML5."""
        html = "<!DOCTYPE html><html><body><div><p>Test</p></div></body></html>"

        self.assertElementContains(
            html,
            "p",
            "<p>Test</p>",
            html="strict",
        )

    @unittest.skipUnless(HAS_HTML5LIB, "html5lib not installed")
    def test_strict_mode_wrong_closing_tag(self):
        """Strict mode should catch wrong closing tags."""
        html = "<!DOCTYPE html><html><body><div>Test</span></div></body></html>"

        with self.assertRaisesRegex(AssertionError, "Response content failed strict HTML5 validation"):
            self.assertElementContains(
                html,
                "div",
                "<div>Test</div>",
                html="strict",
            )

    @unittest.skipUnless(HAS_HTML5LIB, "html5lib not installed")
    def test_strict_mode_adds_doctype(self):
        """Strict mode should auto-add DOCTYPE if missing."""
        # html5lib requires DOCTYPE, we add it automatically
        html = "<html><body><div>Test</div></body></html>"

        # Should not raise - DOCTYPE added automatically
        self.assertElementContains(
            html,
            "div",
            "<div>Test</div>",
            html="strict",
        )

    @unittest.skipUnless(HAS_HTML5LIB, "html5lib not installed")
    def test_strict_mode_with_complex_html(self):
        """Strict mode should work with complex valid HTML5."""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <div class="container">
        <h1>Welcome</h1>
        <p>This is a test page.</p>
    </div>
</body>
</html>"""

        self.assertElementContains(
            html,
            "h1",
            "<h1>Welcome</h1>",
            html="strict",
        )

    def test_standard_mode_still_works(self):
        """Standard mode (html=True) should still work as before."""
        html = "<html><body><div>Test</div></body></html>"

        self.assertElementContains(
            html,
            "div",
            "<div>Test</div>",
            html=True,  # Standard mode
        )

    def test_no_validation_mode(self):
        """html=False should disable validation completely."""
        # Invalid HTML but BeautifulSoup can parse it
        html = "<html><body><div>Test</span></div></body></html>"

        self.assertElementContains(
            html,
            "div",
            "<div>Test</div>",
            html=False,  # No validation
        )

    @unittest.skipUnless(HAS_HTML5LIB, "html5lib not installed")
    def test_strict_mode_unexpected_closing_tag(self):
        """Strict mode should catch unexpected closing tags."""
        html = "<!DOCTYPE html><html><body></div></body></html>"

        with self.assertRaisesRegex(AssertionError, "Response content failed strict HTML5 validation"):
            self.assertElementContains(
                html,
                "body",
                "<body></body>",
                html="strict",
            )

    @unittest.skipUnless(HAS_HTML5LIB, "html5lib not installed")
    def test_strict_mode_with_bytes_content(self):
        """Strict mode should handle byte content correctly."""
        html_bytes = b"<!DOCTYPE html><html><body><div>Test</div></body></html>"

        self.assertElementContains(
            html_bytes,
            "div",
            "<div>Test</div>",
            html="strict",
        )

    def test_standard_mode_with_bytes_content(self):
        """Standard mode should handle byte content correctly."""
        html_bytes = b"<html><body><div>Test</div></body></html>"

        self.assertElementContains(
            html_bytes,
            "div",
            "<div>Test</div>",
            html=True,
        )


class AssertElementDefaultModeTests(TestCase):
    """Tests for class-level default HTML validation mode."""

    def test_default_mode_is_standard(self):
        """Default assert_element_html_mode should be True (standard)."""

        class TestClass(AssertElementMixin, TestCase):
            pass

        test_instance = TestClass()
        self.assertEqual(test_instance.assert_element_html_mode, True)

    def test_class_level_override_to_strict(self):
        """Can override assert_element_html_mode at class level."""

        class StrictTestClass(AssertElementMixin, TestCase):
            assert_element_html_mode = "strict"

        test_instance = StrictTestClass()
        self.assertEqual(test_instance.assert_element_html_mode, "strict")

    def test_class_level_override_to_false(self):
        """Can override assert_element_html_mode to False (no validation)."""

        class NoValidationTestClass(AssertElementMixin, TestCase):
            assert_element_html_mode = False

        test_instance = NoValidationTestClass()
        self.assertEqual(test_instance.assert_element_html_mode, False)

    @unittest.skipUnless(HAS_HTML5LIB, "html5lib not installed")
    def test_class_default_used_when_html_not_specified(self):
        """Class default should be used when html parameter not specified."""

        class StrictByDefaultTest(AssertElementMixin, TestCase):
            assert_element_html_mode = "strict"

        test_instance = StrictByDefaultTest()
        test_instance.setUp()

        # Valid HTML - should use strict validation by default
        html = "<!DOCTYPE html><html><body><div>Test</div></body></html>"
        test_instance.assertElementContains(html, "div", "<div>Test</div>")

        # Invalid HTML - should fail with strict validation
        html_invalid = "<!DOCTYPE html><html><body><div>Test</span></div></body></html>"
        with test_instance.assertRaisesRegex(AssertionError, "Response content failed strict HTML5 validation"):
            test_instance.assertElementContains(html_invalid, "div", "<div>Test</div>")

    def test_explicit_parameter_overrides_class_default(self):
        """Explicit html parameter should override class default."""

        class StrictByDefaultTest(AssertElementMixin, TestCase):
            assert_element_html_mode = "strict"

        test_instance = StrictByDefaultTest()
        test_instance.setUp()

        # Invalid HTML but we explicitly set html=False
        html = "<html><body><div>Test</span></div></body></html>"

        # Should not raise - explicit html=False overrides strict default
        test_instance.assertElementContains(html, "div", "<div>Test</div>", html=False)

    def test_none_uses_class_default(self):
        """html=None should use class default."""

        class CustomTest(AssertElementMixin, TestCase):
            assert_element_html_mode = False

        test_instance = CustomTest()
        test_instance.setUp()

        # Invalid HTML, but class default is False
        html = "<html><body><div>Test</span></div></body></html>"

        # Should not raise - html=None uses class default (False)
        test_instance.assertElementContains(html, "div", "<div>Test</div>", html=None)


@unittest.skipUnless(HAS_HTML5LIB, "html5lib not installed")
class StrictAssertElementMixinTests(StrictAssertElementMixin, TestCase):
    """Tests for StrictAssertElementMixin convenience class."""

    def test_strict_mixin_has_strict_default(self):
        """StrictAssertElementMixin should have 'strict' as default mode."""
        self.assertEqual(self.assert_element_html_mode, "strict")

    def test_strict_mixin_validates_by_default(self):
        """StrictAssertElementMixin should use strict validation by default."""
        html = "<!DOCTYPE html><html><body><div>Test</div></body></html>"

        # Should work - valid HTML, using strict validation by default
        self.assertElementContains(html, "div", "<div>Test</div>")

    def test_strict_mixin_catches_errors_by_default(self):
        """StrictAssertElementMixin should catch validation errors by default."""
        html = "<!DOCTYPE html><html><body><div>Test</span></div></body></html>"

        # Should fail - invalid HTML with strict validation
        with self.assertRaisesRegex(AssertionError, "Response content failed strict HTML5 validation"):
            self.assertElementContains(html, "div", "<div>Test</div>")

    def test_strict_mixin_can_override_per_assertion(self):
        """Can override to standard mode even with StrictAssertElementMixin."""
        html = "<html><body><div>Test</div></body></html>"

        # Should work - explicit html=True uses standard validation
        self.assertElementContains(html, "div", "<div>Test</div>", html=True)

    def test_strict_mixin_can_disable_validation(self):
        """Can disable validation even with StrictAssertElementMixin."""
        html = "<html><body><div>Test</span></div></body></html>"

        # Should work - explicit html=False disables validation
        self.assertElementContains(html, "div", "<div>Test</div>", html=False)
