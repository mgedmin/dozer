try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

version = '0.1'

setup(
    name="Dowser",
    version=version,
    description='GC WSGI Explorer',
    long_description="",
    keywords='web wsgi memory profiler',
    license='BSD',
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
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
