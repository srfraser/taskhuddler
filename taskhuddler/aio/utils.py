"""Common utilities for understanding task graphs, async version."""

from urllib.parse import urlparse
import tempfile

import aioboto3
import aiofiles


async def _fetch_s3_file(filename):
    """Read a file's contents from AWS S3."""
    async with aioboto3.resource('s3') as client:
        with tempfile.TemporaryFile() as t_file:
            url = urlparse(filename)
            await client.Bucket(url.netloc).download_fileobj(url.path.lstrip('/'), t_file)
            t_file.seek(0)
            return t_file.read()


async def _fetch_local_file(filename):
    """Fetch a local file asynchronously."""
    async with aiofiles.open(filename, mode='r') as f:
        return await f.read()


async def fetch_file(filename):
    """Retrieve a file's contents from either local or remote.

    Args:
        filename (str): The file to load. If prefixed with s3:// it will
            attempt to load the file from s3 using the environment's credentials.
    Returns:
        str: The contents of the file.

    """
    if filename.startswith('s3://'):
        return await _fetch_s3_file(filename)
    else:
        return await _fetch_local_file(filename)


async def _store_s3_file(filename, contents):
    """Store a file on s3."""
    url = urlparse(filename)
    async with aioboto3.resource('s3') as client:
        await client.put_object(Bucket=url.netloc, Key=url.path.lstrip('/'), Body=contents)


async def _store_local_file(filename, contents):
    """Store a file locally."""
    async with aiofiles.open(filename, mode='w') as f:
        await f.write(contents)


async def store_file(filename, contents):
    """Store a file either locally or remotely."""
    if filename.startswith('s3://'):
        await _store_s3_file(filename, contents)
    else:
        await _store_local_file(filename, contents)
