import os
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()

version = '0.3'

setup(
    name="Dozer",
    version=version,
    description="WSGI Middleware version of the CherryPy memory leak debugger",
    long_description=read('README.rst') + '\n\n' + read('CHANGELOG.rst'),
    keywords='web wsgi memory profiler',
    license='Public Domain',
    author='Ben Bangert',
    author_email='ben@groovie.org',
    maintainer='Marius Gedminas',
    maintainer_email='marius@gedmin.as',
    url='https://bitbucket.org/bbangert/dozer',
    packages=find_packages(exclude=['ez_setup']),
    zip_safe=False,
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=['nose'],
    install_requires=[
        "Paste>=1.6", "WebOb>=0.9.2", "mako",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: Public Domain",
        "Programming Language :: Python :: 2.7",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points="""
        [paste.filter_factory]
        dozer = dozer:dozer_filter_factory
        profile = dozer:profile_filter_factory
        logview = dozer:logview_filter_factory
        [paste.filter_app_factory]
        dozer = dozer:dozer_filter_app_factory
        profile = dozer:profile_filter_app_factory
        logview = dozer:logview_filter_app_factory
    """,
)
