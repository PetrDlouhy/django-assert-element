=============================
Django assert element
=============================

.. image:: https://badge.fury.io/py/assert_element.svg
    :target: https://badge.fury.io/py/assert_element

.. image:: https://codecov.io/gh/PetrDlouhy/assert_element/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/PetrDlouhy/assert_element

.. image:: https://github.com/PetrDlouhy/django-assert-element/actions/workflows/main.yml/badge.svg?event=registry_package
    :target: https://github.com/PetrDlouhy/django-assert-element/actions/workflows/main.yml

Simple ``TestCase`` assertion that finds element based on its CSS selector and checks if it equals the given content.
In case the content is not matching it outputs nice and clean diff of the two compared HTML pieces.

This is more useful than the default Django ``self.assertContains(response, ..., html=True)``
because it will find the element and show differences if something changed.

Why Use assertElementHTML?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Primary Benefits:**

1. **Targeted Error Messages** - Shows only the relevant element on failure, not the entire HTML response
2. **Precise Testing** - Forces you to write specific, maintainable tests with CSS selectors
3. **Less Brittle** - Tests focus on semantic structure, not exact formatting
4. **Better Debugging** - Failures point directly to the problematic element

**Comparison:**

.. code-block:: python

    # ❌ BAD - Dumps entire HTML response on failure (thousands of lines)
    self.assertContains(response, "Company Dashboard")
    self.assertIn("Company Dashboard", response.content.decode())

    # ✅ GOOD - Shows only the relevant element (clean, focused)
    self.assertElementHTML(response, "h1", "<h1>Company Dashboard</h1>")

Whitespace Normalization
~~~~~~~~~~~~~~~~~~~~~~~~~

The library uses aggressive whitespace normalization to focus on HTML semantic meaning
rather than cosmetic formatting differences:

* **Normalizes cosmetic differences**: Multiple spaces, tabs, newlines, and attribute spacing
* **Handles structural variations**: Self-closing vs explicit tags (``<br/>`` vs ``<br></br>``)
* **Preserves semantic meaning**: Only fails when HTML content actually differs in meaning
* **Browser-consistent**: Mimics how browsers treat whitespace (collapsed to single spaces)

This prevents false positive test failures caused by insignificant whitespace variations
while still catching genuine HTML content differences.

**How it works:** The normalization uses BeautifulSoup to parse and normalize HTML structure,
then collapses whitespace to single spaces (as browsers do), making tests resilient to formatting changes.

**Example:** These assertions would pass because the differences are cosmetic:

.. code-block:: python

    # All of these work - whitespace is normalized automatically:
    self.assertElementHTML(response, 'p', '<p>hello world</p>')
    self.assertElementHTML(response, 'p', '<p>hello   world</p>')  # Multiple spaces
    self.assertElementHTML(response, 'p', '<p>hello\tworld</p>')   # Tab
    self.assertElementHTML(response, 'p', '<p>\n  hello world  \n</p>')  # Newlines

To check that an element's HTML includes a fragment after sanitization, use::

    self.assertElementContainsHTML(response, 'div', '<span>hello</span>')

The old ``assertElementHTML`` name is preserved for backwards compatibility
but will be removed in a future release.

Complete Element Matching
~~~~~~~~~~~~~~~~~~~~~~~~~

**Critical:** ``assertElementHTML`` does **exact element matching**, not content checking.
You must include the element's own tags in the expected string.

.. code-block:: python

    # Given: <button class="submit-btn">Save</button>
    self.assertElementHTML(
        response,
        'button.submit-btn',
        '<button class="submit-btn">Save</button>'
    )  # ✓ Correct

    self.assertElementHTML(
        response,
        'button.submit-btn',
        'Save'
    )  # ✗ Wrong - missing element tags

CSS Selectors Only
~~~~~~~~~~~~~~~~~~

Use CSS selectors (not XPath) to target elements:

.. code-block:: python

    # ✅ Good - CSS selectors
    self.assertElementHTML(response, '#page-title', '<h1 id="page-title">Dashboard</h1>')
    self.assertElementHTML(response, '.invoice-number', '<span class="invoice-number">123</span>')
    self.assertElementHTML(response, 'button.submit-btn', '<button class="submit-btn">Save</button>')

    # ❌ Bad - XPath not supported
    # self.assertElementHTML(response, '//div[@class="invoice"]', ...)  # Won't work

Single Element Requirement
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The CSS selector must match exactly one element. If multiple elements match, ``assertElementHTML``
will raise an exception with details about all matching elements.

**Error when multiple elements found:**

.. code-block:: console

    Exception: More than one element found (3): .member-email
    Found elements:
      1. <span class="member-email">user1@example.com</span>
      2. <span class="member-email">user2@example.com</span>
      3. <span class="member-email">user3@example.com</span>

**Solutions:**

Solution 1: Add Semantic Classes/IDs (Recommended)
----------------------------------------------------

Add semantic classes or IDs to your templates to make selectors unique:

.. code-block:: html

    <!-- Template -->
    <div class="empty-state-message">No team members yet.</div>
    <a href="/invite/" class="invite-team-link">Invite Team Members</a>

.. code-block:: python

    # Test
    self.assertElementHTML(
        response,
        '.empty-state-message',
        '<div class="empty-state-message">No team members yet.</div>'
    )

**Benefits:**

* Makes templates more semantic and maintainable
* Improves accessibility (IDs/classes can be used by screen readers)
* Makes tests self-documenting

Solution 2: Use nth-child Selectors
-----------------------------------

When you need to target a specific element in a list:

.. code-block:: python

    # Target first row in a table
    self.assertElementHTML(
        response,
        'tbody tr:nth-child(1) .invoice-number',
        '<span class="invoice-number">1/FV/12/2025</span>'
    )

Solution 3: Make Selector More Specific
---------------------------------------

Combine selectors to narrow down to a unique element:

.. code-block:: python

    # Instead of just '.member-email', use:
    self.assertElementHTML(
        response,
        '.business-plan-members .member-email',
        '<span class="member-email">user@example.com</span>'
    )

Common Patterns
~~~~~~~~~~~~~~~

Dynamic Content
---------------

Extract dynamic values from models, don't hardcode:

.. code-block:: python

    def test_with_dynamic_content(self):
        invoice = Invoice.objects.create(
            number="1/FV/12/2025",
            total=Decimal("100.00")
        )

        response = self.client.get(f'/invoices/{invoice.id}/')

        # Build expected HTML with dynamic values from the model
        expected = f'<span class="invoice-number">{invoice.full_number}</span>'
        self.assertElementHTML(response, '.invoice-number', expected)

Testing Form Errors
-------------------

.. code-block:: python

    # Template has: <div class="invalid-feedback d-block email-field-error">...</div>
    self.assertElementHTML(
        response,
        '.email-field-error',
        '<div class="invalid-feedback d-block email-field-error">',
    )

Testing Empty States
---------------------

.. code-block:: python

    self.assertElementHTML(
        response,
        '.empty-state-message',
        '<p class="text-muted empty-state-message">No team members yet.</p>'
    )

Testing Modal Content
---------------------

.. code-block:: python

    self.assertElementHTML(
        response,
        '.upgrade-plan-id',
        f'<input type="hidden" name="plan_id" value="{plan.id}" class="upgrade-plan-id">'
    )

Best Practices
~~~~~~~~~~~~~~

1. **Use Semantic Selectors** - Prefer ``.invoice-number`` over ``.table tbody tr:first-child td:nth-child(2)``
2. **Extract Dynamic Data** - Get UUIDs/timestamps from models, don't hardcode
3. **Modify Templates for Testability** - Add semantic classes/IDs when needed
4. **Keep Selectors Simple** - Avoid overly complex CSS selectors

Common Pitfalls
~~~~~~~~~~~~~~~

1. **Missing Element Tags** - Must include the selected element's own tags, not just inner text
2. **Multiple Element Selection** - Selector must target exactly one element (use solutions above)
3. **Hardcoded Dynamic Content** - Extract UUIDs/timestamps from models, don't hardcode
4. **Overly Complex Selectors** - Prefer semantic classes over deep CSS selectors

Other similar projects
----------------------

I released this package just to realize after few days, that there are some other very similar projects:

* https://pypi.org/project/django_html_assertions/
* https://django-with-asserts.readthedocs.io/en/latest/
* https://github.com/robjohncox/python-html-assert

Documentation
-------------

The full documentation is at https://assert_element.readthedocs.io.

Quickstart
----------

Install by:

.. code-block:: bash

    pip install assert-element

Usage in tests:

.. code-block:: python

    from assert_element import AssertElementMixin

    class MyTestCase(AssertElementMixin, TestCase):
        def test_something(self):
            response = self.client.get(address)
            self.assertElementHTML(
                response,
                'div[id="my-div"]',
                '<div id="my-div">My div</div>',
            )
            self.assertElementContainsHTML(
                response,
                'div[id="my-div"]',
                '<span>My</span>',
            )

The first attribute can be response or content string.
Second attribute is the CSS selector to the element.
Third attribute is the expected content.

**Error Output Example**: If response = ``<html><div id="my-div">Myy div</div></html>`` the error output of the ``assertElementHTML`` looks like this:

.. code-block:: console

    ======================================================================
    FAIL: test_element_differs (tests.test_models.MyTestCase.test_element_differs)
    Element not found raises Exception
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "/home/petr/soubory/programovani/blenderkit/django-assert-element/assert_element/tests/test_models.py", line 53, in test_element_differs
        self.assertElementHTML(
      File "/home/petr/soubory/programovani/blenderkit/django-assert-element/assert_element/assert_element/assert_element.py", line 58, in assertElementHTML
        self.assertEqual(element_txt, soup_1_txt)
    AssertionError: '<div\n id="my-div"\n>\n Myy div \n</div>' != '<div\n id="my-div"\n>\n My div \n</div>'
      <div
       id="my-div"
      >
    -  Myy div
    ?    -
    +  My div
      </div>

which is much cleaner than the original django ``assertContains()`` output.

API Reference
~~~~~~~~~~~~~

``assertElementHTML(request, html_element, element_text)``
--------------------------------------------------------------

**Parameters:**

* ``request`` - Django response object or HTML string
* ``html_element`` - CSS selector string (e.g., ``'#id'``, ``'.class'``, ``'button.submit-btn'``)
* ``element_text`` - Expected full element HTML string (must include element's own tags)

**Raises:**

* ``Exception`` - If no element found, multiple elements found, or element doesn't match

**Example:**

.. code-block:: python

    self.assertElementHTML(
        response,
        'h1#page-title',
        '<h1 id="page-title">Dashboard</h1>'
    )

How It Works
~~~~~~~~~~~~

1. Parses HTML using BeautifulSoup
2. Selects element(s) using CSS selector
3. Validates exactly one element found
4. Normalizes both actual and expected HTML (whitespace, structure)
5. Compares normalized HTML strings

The normalization process:

* Uses BeautifulSoup for structural normalization
* Collapses consecutive whitespace to single spaces
* Normalizes line endings
* Preserves semantic structure while ignoring cosmetic formatting


Running Tests
-------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox


Development commands
---------------------

::

    pip install -r requirements_dev.txt
    invoke -l


Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
