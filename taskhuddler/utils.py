"""Common utilities for understanding tasks."""
import logging
import os
import tempfile
from collections import namedtuple
from urllib.parse import urlparse

import boto3
import botocore

log = logging.getLogger(__name__)


def _fetch_s3_file(filename):
    """Read a file's contents from AWS S3."""
    s3 = boto3.resource('s3')
    url = urlparse(filename)
    with tempfile.TemporaryFile() as t_file:
        try:
            s3.Bucket(url.netloc).download_fileobj(url.path.lstrip('/'), t_file)
        except botocore.exceptions.ClientError as e:
            log.debug(e)
            raise
        t_file.seek(0)
        return t_file.read()


def _fetch_local_file(filename):
    """Fetch a local file."""
    with open(filename, 'r') as f:
        return f.read()


def fetch_file(filename):
    """Retrieve a file's contents from either local or remote.

    Args:
        filename (str): The file to load. If prefixed with s3:// it will
            attempt to load the file from s3 using the environment's credentials.
    Returns:
        str: The contents of the file.

    """
    if filename.startswith('s3://'):
        return _fetch_s3_file(filename)
    else:
        return _fetch_local_file(filename)


def _store_s3_file(filename, contents):
    """Store a file on s3."""
    s3 = boto3.client('s3')
    url = urlparse(filename)
    s3.put_object(Bucket=url.netloc, Key=url.path.lstrip('/'), Body=contents)


def _store_local_file(filename, contents):
    """Store a file locally."""
    with open(filename, 'w') as f:
        f.write(contents)


def store_file(filename, contents):
    """Store a file either locally or remotely."""
    if filename.startswith('s3://'):
        _store_s3_file(filename, contents)
    else:
        _store_local_file(filename, contents)


Range = namedtuple('Range', ['start', 'end'])


def allen_overlap(r1, r2):
    """Return True if the two datetimes overlap or are contained."""
    return (r1.start < r2.start) and ((r1.end > r2.start) and (r1.end < r2.end))
    # return max((min(r1.end, r2.end) - max(r1.start, r2.start)).days, -1) + 1


def allen_contains(r1, r2):
    """Is one date contained within the other."""
    return (r1.start < r2.start and r1.end > r2.end) or (r2.start < r1.start and r2.end > r1.end)


def should_merge(r1, r2):
    """Return True if these two datetimes be merged."""
    return allen_overlap(r1, r2) or allen_overlap(r2, r1) or allen_contains(r1, r2)


def merge_dates(r1, r2):
    """Merge two start/end tuples if they overlap."""
    if should_merge(r1, r2):
        return Range(start=min(r1.start, r2.start), end=max(r1.end, r2.end))
    else:
        raise ValueError('Dates do not overlap')


def merge_date_list(dt_list):
    """Merge two lists of datetime objects.

    Given date ranges like this:
       |------|
            |------|
    |---|
                         |------|

    Produce a list of date ranges:
    |--------------|     |------|
    """
    result = list()
    while(dt_list):
        current = dt_list.pop()
        overlaps = [dt for dt in dt_list if should_merge(current, dt)]
        if not overlaps:
            result.append(current)
            continue
        for dt in overlaps:
            current = merge_dates(current, dt)
            dt_list.remove(dt)
        dt_list.append(current)

    return sorted(result)


def tc_options():
    """Set Taskcluster options."""
    return {
        'rootUrl': os.environ.get('TASKCLUSTER_ROOT_URL', 'https://firefox-ci-tc.services.mozilla.com'),
    }
