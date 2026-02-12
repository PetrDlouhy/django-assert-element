.. :changelog:

History
-------

0.7.0 (2026-02-12)
++++++++++++++++++

* added HTML validation modes for catching structural errors
* added standard HTML validation (default) using Django's parse_html
* added optional strict HTML5 validation using html5lib (install with: pip install assert-element[strict])
* added class-level validation mode configuration via assert_element_html_mode attribute
* added StrictAssertElementMixin convenience class for strict-by-default validation
* improved backward compatibility - all existing code works unchanged
* added 21 new tests for validation modes (49 total tests)

0.6.1 (2025-12-18)
++++++++++++++++++

* fixed whitespace normalization in attribute values (regression fix)
* attribute values now properly normalize multi-line formatting to single line
* improved tolerance for cosmetic whitespace differences in srcset, style, and other attributes
* added comprehensive test coverage for real-world HTML formatting variations

0.6.0 (2025-12-11)
++++++++++++++++++

* added element preview in error messages for easier debugging
* improved HTML formatting with proper self-closing tag handling
* normalized boolean attribute handling for consistent comparisons
* added pre-commit configuration for unified CI checks
* enhanced README with comprehensive examples and documentation

0.5.0 (2025-08-15)
++++++++++++++++++

* improved whitespace sanitization with aggressive normalization
* enhanced test coverage for semantically meaningful whitespace differences
* updated documentation with detailed whitespace normalization behavior

0.4.0 (2023-07-21)
++++++++++++++++++

* more readable output when assertion fails

0.3.0 (2022-09-16)
++++++++++++++++++

* more tolerance in whitespace differences

0.2.0 (2022-09-01)
++++++++++++++++++

* first attribute can be response or content itself

0.1.0 (2022-08-21)
++++++++++++++++++

* First release on PyPI.
