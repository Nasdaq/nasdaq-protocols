Developer's Guide
=================

This guide is intended for developers who want to contribute to the
development of the `nasdaq-protocols` library.


Guidelines
----------
Before merging to main, please ensure that the following guidelines are met:

- All existing tests are passing.
- New tests are added when needed.
- Pylint reports no errors, 10/10
- Code is documented and docstrings are added when needed.
- Documentation is included in the rst files.


Building
________
.. code-block:: console

    $ tox r

`tox r` will execute all of the following.

- `tox -e lint` - Runs linter and validates the code
- `tox -e test` - Runs the pytest test cases
- `tox -e build` - Builds the package sdist and wheel
- `tox -e doc` - Builds the documentation


FAQ
___
- **Why is pycharm debugger not stopping at breakpoints?**
  Disable the coverage statement from pytest.ini. Refer https://stackoverflow.com/a/56235965/4248850

- **Why is the coverage not reported in pycharm?**
  Disable the coverage statement from pytest.ini