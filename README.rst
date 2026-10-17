Dozer
=====

.. image:: https://github.com/mgedmin/dozer/actions/workflows/build.yml/badge.svg?branch=master
    :target: https://github.com/mgedmin/dozer/actions

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


Securing the debug pages
------------------------

The ``/_dozer`` and ``/_profiler`` pages show potentially sensitive
information: request URLs, object reprs, recorded profiles.  If your
application is served by a WSGI server without a fronting web server
that could require authentication, you can protect these pages with
HTTP Basic authentication::

    from dozer import Dozer, Profiler

    wsgi_app = Dozer(my_wsgi_app, basic_auth=('username', 'password'))
    wsgi_app = Profiler(wsgi_app, profile_path=mkdtemp(prefix='dozer-'),
                        basic_auth=('username', 'password'))

All requests to the debug pages that don't carry the correct
credentials get a 401 response, and your browser asks for a username
and password.  Applications pass through unaffected.

When configuring the middleware via PasteDeploy you can use a
``username:password`` string instead::

    [filter:dozer]
    use = egg:Dozer#dozer
    basic_auth = username:password
