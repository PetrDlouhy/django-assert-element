=============================
Django assert element
=============================

.. image:: https://badge.fury.io/py/assert_element.svg
    :target: https://badge.fury.io/py/assert_element

.. image:: https://codecov.io/gh/PetrDlouhy/assert_element/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/PetrDlouhy/assert_element

.. image:: https://github.com/PetrDlouhy/django-assert-element/actions/workflows/main.yml/badge.svg?event=registry_package
    :target: https://github.com/PetrDlouhy/django-assert-element/actions/workflows/main.yml

Simple ``TestCase`` assertion that finds element based on it's xpath and check if it equals with given content.
In case the content is not matching it outputs nice and clean diff of the two compared HTML pieces.

This is more useful than the default Django ``self.assertContains(response, ..., html=True)``
because it will find the element and show differences if something changed.

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
            self.assertElementContains(
                response,
                'div[id="my-div"]',
                '<div id="my-div">My div</div>',
            )

The first attribute can be response or content string.
Second attribute is the xpath to the element.
Third attribute is the expected content.

**Error Output Example**: If response = `<html><div id="my-div">Myy div</div></html>` the error output of the `assertElementContains` looks like this:

.. code-block:: console

    ======================================================================
    FAIL: test_element_differs (tests.test_models.MyTestCase.test_element_differs)
    Element not found raises Exception
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "/home/petr/soubory/programovani/blenderkit/django-assert-element/assert_element/tests/test_models.py", line 53, in test_element_differs
        self.assertElementContains(
      File "/home/petr/soubory/programovani/blenderkit/django-assert-element/assert_element/assert_element/assert_element.py", line 58, in assertElementContains
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

**Whitespace Example**: These assertions would pass because the differences are cosmetic:

.. code-block:: python

    # These are all equivalent due to whitespace normalization:
    self.assertElementContains(response, 'p', '<p>hello world</p>')
    self.assertElementContains(response, 'p', '<p>hello   world</p>')  # Multiple spaces
    self.assertElementContains(response, 'p', '<p>hello\tworld</p>')   # Tab
    self.assertElementContains(response, 'p', '<p>\n  hello world  \n</p>')  # Newlines

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
