from __future__ import print_function

import json
import os
import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

project_dir = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(project_dir, 'version.json')) as filehandle:
    VERSION = json.load(filehandle)['version_string']

with open(os.path.join(project_dir, 'requirements/main.in')) as filehandle:
    requirements_raw = filehandle.readlines()

requirements_without_comments = [
    line for line in requirements_raw if line and not line.startswith('#')
]

with open(os.path.join(project_dir, 'requirements/pandas.in')) as filehandle:
    pandas_raw = filehandle.readlines()

pandas_without_comments = [
    line for line in pandas_raw if line and not line.startswith('#')
]


setup(
    name="taskhuddler",
    version=VERSION,
    description="taskcluster-client wrapper",
    author='Mozilla Release Engineering',
    author_email='release+python@mozilla.com',
    url="https://github.com/mozilla-releng/taskhuddler",
    packages=find_packages(),
    package_data={"": ["version.json"]},
    data_files=[('requirements', ['requirements/main.txt', 'requirements/test.txt',
                                  'requirements/main.in', 'requirements/test.in'])],
    include_package_data=True,
    zip_safe=False,
    license="MPL 2.0",
    install_requires=requirements_without_comments,
    extras_require={
        'pandas': pandas_without_comments,
},
    classifiers=(
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ),
)
