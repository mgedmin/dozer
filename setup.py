import os
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


def read(filename):
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return f.read()


version = '0.5'

tests_require = ['nose', 'mock', 'WebTest', 'Pillow']

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
    url='https://github.com/mgedmin/dozer',
    packages=find_packages(exclude=['ez_setup']),
    zip_safe=False,
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=tests_require,
    install_requires=[
        "WebOb>=1.2", "Mako",
    ],
    extras_require={
        'test': tests_require,
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: Public Domain",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
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
