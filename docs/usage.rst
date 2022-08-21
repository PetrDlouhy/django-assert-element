=====
Usage
=====

To use Django assert element in a project, add it to your `INSTALLED_APPS`:

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
