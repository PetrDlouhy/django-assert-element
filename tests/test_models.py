#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for assert_element package.

This module contains comprehensive tests for the assert_element functionality,
including integration tests for assertElementContains and detailed analysis
of HTML whitespace sanitization behavior.
"""

from django.test import TestCase

from assert_element import AssertElementMixin
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
        with self.assertRaisesRegex(
            Exception, r"More than one element found \(\d+\): title"
        ):
            self.assertElementContains(
                "<title>Not Found</title><title>Not Found</title>",
                "title",
                "<title>Not Found</title>",
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
            # 4. Significant trailing whitespace in attributes
            (
                "Attribute value trailing whitespace",
                '<input value="test">',
                '<input value="test ">',
            ),  # value has trailing space
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
                    print(
                        f"Attribute whitespace normalized: {repr(html1)} == {repr(html2)}"
                    )
                else:
                    print(
                        f"Attribute whitespace preserved: {repr(html1)} != {repr(html2)}"
                    )

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
