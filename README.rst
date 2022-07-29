Dozer
=====

.. image:: https://github.com/mgedmin/dozer/workflows/build/badge.svg?branch=master
    :target: https://github.com/mgedmin/dozer/actions

.. image:: https://ci.appveyor.com/api/projects/status/github/mgedmin/dozer?branch=master&svg=true
    :target: https://ci.appveyor.com/project/mgedmin/dozer

.. image:: https://coveralls.io/repos/mgedmin/dozer/badge.svg?branch=master
    :target: https://coveralls.io/r/mgedmin/dozer

Dozer was originally a WSGI middleware version of Robert Brewer's
Dowser CherryPy tool that
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

    from tempfile import mkdtemp
    from dozer import Profiler

    # my_wsgi_app is a WSGI application
    wsgi_app = Profiler(my_wsgi_app, profile_path=mkdtemp(prefix='dozer-'))

Assuming you're serving your application on the localhost at port 5000,
you can then load up ``http://localhost:5000/_profiler`` to view the
list of recorded request profiles.

The profiles are stored in the directory specified via ``profile_path``.  If
you want to keep seeing older profiles after restarting the web app, specify a
fixed directory instead of generating a fresh empty new one with
tempfile.mkdtemp.  Make sure the directory is not world-writable, as the
profiles are stored as `insecure Python pickles, which allow arbitrary command
execution during load
<https://docs.python.org/3/library/pickle.html#module-pickle>`_.

Here's a blog post by Marius Gedminas that contains `a longer description
of Dozer's profiler <https://mg.pov.lt/blog/profiling-with-dozer.html>`_.


Inspecting log messages
-----------------------

Usage::

    from dozer import Logview

    # my_wsgi_app is a WSGI application
    wsgi_app = Logview(my_wsgi_app)

Every text/html page served by your application will get some HTML and
Javascript injected into the response body listing all logging messages
produced by the thread that generated this response.

Here's a blog post by Marius Gedminas that contains `a longer description
of Dozer's logview <https://mg.pov.lt/blog/capturing-logs-with-dozer.html>`_.
