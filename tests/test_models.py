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
