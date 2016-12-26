"""
Yass!

Yet Another Static Site!

"""

import os
from setuptools import setup, find_packages

install_requires = [
    "jinja2==2.8",
    "webassets==0.12.0",
    "click==6.2",
    "pyyaml==3.11",
    "markdown==2.6.2",
    "pyjade==4.0.0",
    "python-frontmatter==0.3.1",
    "jinja-macro-tags==0.1",
    "livereload==2.5.0",
    "arrow==0.8.0",
]

setup(
    name="Yass",
    version="0.0.1",
    license="MIT",
    author="Mardix",
    author_email="",
    description="Yet Another Static Site generator for everybody",
    url="https://github.com/mardix/yass",
    long_description="Static site generator",
    py_modules=['yass'],
    entry_points=dict(console_scripts=[
        'yass=yass.cli:cmd'
    ]),
    include_package_data=True,
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    install_requires=install_requires,
    keywords=['static site generator'],
    platforms='any',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: MIT',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    zip_safe=False
)