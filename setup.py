"""
Yass!

Yet Another Static Site!

"""

import os
from setuptools import setup, find_packages


base_dir = os.path.dirname(__file__)

__about__ = {}

with open(os.path.join(base_dir, "yass", "__about__.py")) as f:
    exec(f.read(), __about__)

install_requires = [
    "jinja2==2.8",
    "webassets==0.12.0",
    "click==6.2",
    "pyyaml==5.4",
    "markdown==2.6.2",
    "pyjade==4.0.0",
    "python-frontmatter==0.3.1",
    "livereload==2.5.0",
    "arrow==0.8.0",
    "python-slugify==1.2.1",
    "boto3==1.4.3",
    "paginator",
    "requests",
    #"grequests"
]

setup(
    name=__about__["__title__"],
    version=__about__["__version__"],
    license=__about__["__license__"],
    author=__about__["__author__"],
    author_email=__about__["__email__"],
    description=__about__["__summary__"],
    url=__about__["__uri__"],
    long_description=__about__["__long_description__"],
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
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    zip_safe=False
)