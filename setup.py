from __future__ import print_function

import json
import os
import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

project_dir = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(project_dir, "version.json")) as filehandle:
    VERSION = json.load(filehandle)["version_string"]


setup(
    name="taskhuddler",
    version=VERSION,
    description="taskcluster-client wrapper",
    author="Mozilla Release Engineering",
    author_email="release+python@mozilla.com",
    url="https://github.com/mozilla-releng/taskhuddler",
    packages=find_packages("src"),
    package_data={"": ["version.json"]},
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    license="MPL 2.0",
    install_requires=["aiofiles", "aiohttp", "async-timeout<4.0", "asyncinit", "certifi", "idna-ssl", "python-dateutil", "taskcluster",],
    extras_require={"pandas": ["pandas"]},
    classifiers=[
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
