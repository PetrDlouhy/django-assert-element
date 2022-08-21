=============================
Django assert element
=============================

.. image:: https://badge.fury.io/py/assert_element.svg
    :target: https://badge.fury.io/py/assert_element

.. image:: https://codecov.io/gh/PetrDlouhy/assert_element/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/PetrDlouhy/assert_element

.. image:: https://github.com/PetrDlouhy/django-assert-element/actions/workflows/main.yml/badge.svg?event=registry_package
    :target: https://github.com/PetrDlouhy/django-assert-element/actions/workflows/main.yml

Simple TestCase assertion that finds element based on it's path and check if it equals with given content.

This is more useful than the default Django AssertContains
because it will find the element and show differences if something changed.
The test also tries to ignore differences in whitespaces as much as possible.

Documentation
-------------

The full documentation is at https://assert_element.readthedocs.io.

Quickstart
----------

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
