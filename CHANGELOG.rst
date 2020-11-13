Dozer Changelog
===============

0.8 (November 13, 2020)
-----------------------

- Add support for Python 3.8 and 3.9.
- Drop support for Python 3.5.
- Add UI input for existing "floor" query string parameter
  (https://github.com/mgedmin/dozer/issues/2)
- Add UI input to filter type charts by a regular expression
- Add sorting option: monotonicity
- Display traceback on 500 Internal Server Error
- Dicts and sets with unsortable keys are no longer unrepresentable
- Aggregate dynamically-created types with the same ``__name__`` and
  ``__module__`` (`issue 9 <https://github.com/mgedmin/dozer/pull/9>`_).


0.7 (April 23, 2019)
--------------------

* Add support for Python 3.7.
* Drop support for Python 3.3 and 3.4.
* Stop using cgi.escape on Python 3, which is especially important now that
  it's been removed from Python 3.8.


0.6 (May 18, 2017)
------------------

* Add support for Python 3.6.
* Drop support for Python 2.6.
* Fix rare TypeError when listing profiles, if two profiles happen to have
  the exact same timestamp (https://github.com/mgedmin/dozer/pull/4).

0.5 (December 2, 2015)
----------------------
* Make /_dozer show the index page (instead of an internal server
  error).
* Add support for Python 3.4 and 3.5.
* Drop support for Python 2.5.
* Move to GitHub.

0.4 (March 21, 2013)
--------------------
* 100% test coverage.
* Add support for Python 3.2 or newer.
* Drop dependency on Paste.

0.3.2 (February 10, 2013)
--------------------------
* More comprehensive fixes for issue #5 by Mitchell Peabody.
* Fix TypeError: unsupported operand type(s) for +: 'property' and 'str'
  (https://bitbucket.org/bbangert/dozer/issue/3).
* Add a small test suite.

0.3.1 (February 6, 2013)
------------------------
* Fix TypeError: You cannot set Response.body to a text object
  (https://bitbucket.org/bbangert/dozer/issue/5).  Patch by Mitchell Peabody.

0.3 (December 13, 2012)
-----------------------
* Emit the "PIL is not installed" only if the Dozer middleware is
  actually used.
* Give a name to the Dozer memleak thread.
* You can now supply a function directly to Logview(stack_formatter=fn) 
* New configuration option for Logview middleware: tb_formatter, similar
  to stack_formatter, but for exception tracebacks.

0.2 (December 5, 2012)
----------------------
* Adding logview that appends log events for the current request to the bottom
  of the html output for html requests.
* Adding profiler for request profiling and call tree viewing.
* Refactored Dozer into its own leak package.
* New maintainer: Marius Gedminas.

0.1 (June 14, 2008)
-------------------
* Initial public release, port from Dowser, a CherryPy tool.
