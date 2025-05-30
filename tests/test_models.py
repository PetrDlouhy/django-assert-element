#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_assert_element
------------

Tests for `assert_element` models module.
"""

from django.test import TestCase

from assert_element import AssertElementMixin


class MyTestCase(AssertElementMixin, TestCase):
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
        with self.assertRaisesRegex(Exception, "More than one element found: title"):
            self.assertElementContains(
                "<title>Not Found</title><title>Not Found</title>",
                "title",
                "<title>Not Found</title>",
            )
