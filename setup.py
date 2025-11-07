import pathlib

from setuptools import find_packages, setup


def read(filename):
    return pathlib.Path(__file__).parent.joinpath(filename).read_text()


version = '0.9'

setup(
    name="Dozer",
    version=version,
    description="WSGI Middleware version of the CherryPy memory leak debugger",
    long_description=read('README.rst') + '\n\n' + read('CHANGELOG.rst'),
    long_description_content_type='text/x-rst',
    keywords='web wsgi memory profiler',
    license='CC-PDM-1.0',  # i.e. Public Domain
    author='Ben Bangert',
    author_email='ben@groovie.org',
    maintainer='Marius Gedminas',
    maintainer_email='marius@gedmin.as',
    url='https://github.com/mgedmin/dozer',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=[
        "WebOb>=1.2", "Mako",
    ],
    extras_require={
        'test': ['pytest', 'WebTest', 'Pillow'],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
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
