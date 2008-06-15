try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

version = '0.1'

setup(
    name="Dozer",
    version=version,
    description='GC WSGI Explorer',
    long_description="""
Dozer
=====

Dozer is a WSGI middleware version of Robert Brewer's
`Dowser CherryPy tool <http://www.aminus.net/wiki/Dowser>`_ that
displays information as collected by the gc module to assist in
tracking down memory leaks.

Usage::

    from dozer import Dozer

    # my_wsgi_app is a WSGI application
    wsgi_app = Dozer(my_wsgi_app)

Assuming you're serving your application on the localhost at port 5000,
you can then load up ``http://localhost:5000/_dozer/index`` to view the
gc info.

""",
    keywords='web wsgi memory profiler',
    license='Public Domain',
    author='Ben Bangert',
    author_email='ben@groovie.org',
    url='http://www.pylonshq.com/',
    packages=find_packages(exclude=['ez_setup']),
    zip_safe=False,
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=['nose'],
    install_requires=[
        "Paste>=1.6", "WebOb>=0.9.2",
    ],
    dependency_links=[
        "http://www.pylonshq.com/download/0.9.7"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: Public Domain",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points="""
        [paste.filter_factory]
        dozer = dozer:dozer_filter_factory
        [paste.filter_app_factory]
        dozer = dozer:dozer_filter_app_factory
    """,
)
