Dozer Changelog
===============

0.4.1 (unreleased)
------------------
* Make /_dozer work show the index page (instead of an internal server
  error).

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
