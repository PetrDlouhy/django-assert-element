=============================
Django assert element
=============================

.. image:: https://badge.fury.io/py/assert_element.svg
    :target: https://badge.fury.io/py/assert_element

.. image:: https://travis-ci.org/PetrDlouhy/assert_element.svg?branch=master
    :target: https://travis-ci.org/PetrDlouhy/assert_element

.. image:: https://codecov.io/gh/PetrDlouhy/assert_element/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/PetrDlouhy/assert_element

Simple TestCase assertion that finds element based on it's path and check if it equals with given content.

Documentation
-------------

The full documentation is at https://assert_element.readthedocs.io.

Quickstart
----------

Install Django assert element::

    pip install assert_element

Add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'assert_element.apps.AssertElementConfig',
        ...
    )

Add Django assert element's URL patterns:

.. code-block:: python

    from assert_element import urls as assert_element_urls


    urlpatterns = [
        ...
        url(r'^', include(assert_element_urls)),
        ...
    ]

Features
--------

* TODO

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
