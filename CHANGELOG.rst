Dozer Changelog
===============

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
