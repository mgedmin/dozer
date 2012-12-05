Dozer
=====

Dozer was originally a WSGI middleware version of Robert Brewer's
`Dowser CherryPy tool <http://www.aminus.net/wiki/Dowser>`_ that
displays information as collected by the gc module to assist in
tracking down memory leaks.  It now also has middleware for profiling
and for looking at logged messages.


Tracking down memory leaks
--------------------------

Usage::

    from dozer import Dozer

    # my_wsgi_app is a WSGI application
    wsgi_app = Dozer(my_wsgi_app)

Assuming you're serving your application on the localhost at port 5000,
you can then load up ``http://localhost:5000/_dozer/index`` to view the
gc info.


Profiling requests
------------------

Usage::

    from dozer import Profiler

    # my_wsgi_app is a WSGI application
    wsgi_app = Profiler(my_wsgi_app)

Assuming you're serving your application on the localhost at port 5000,
you can then load up ``http://localhost:5000/_profiler`` to view the
list of recorded request profiles.

Here's a blog post by Marius Gedminas that contains `a longer description
of Dozer's profiler <http://mg.pov.lt/blog/profiling-with-dozer.html>`_.


Inspecting log messages
-----------------------

Usage:

    from dozer import Logview

    # my_wsgi_app is a WSGI application
    wsgi_app = Logview(my_wsgi_app)

Every text/html page served by your application will get some HTML and
Javascript injected into the response body listing all logging messages
produced by the thread that generated this response.

Here's a blog post by Marius Gedminas that contains `a longer description
of Dozer's logview <http://mg.pov.lt/blog/capturing-logs-with-dozer.html>`_.
