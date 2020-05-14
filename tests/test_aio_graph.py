import json
import os
import tempfile
from unittest.mock import patch

import pytest
import taskcluster
from taskhuddler.aio import TaskGraph

TASK_IDS = ["A-8AqzvvRsqH9b0VHBXYjA", "A-aPcZanRJaxM-IToHyyHw", "A0BaQjdkS8Wdy2Ev_1pLgA", "A0VWjOkmRNqkKrRUj83BEA", "A0cabJ3WTeCrDN15nbTPYw"]


async def mocked_listTaskGroup(dummy, groupid, query):
    if "continuationToken" in query:
        filename = "{}.json".format(query["continuationToken"])
    else:
        filename = "completed.json"

    with open(os.path.join(os.path.dirname(__file__), "data", filename)) as f:
        return json.loads(f.read())


@pytest.mark.asyncio
async def test_taskgraph_str():
    with patch.object(taskcluster.aio.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = await TaskGraph("eShtp2faQgy4iZZOIhXvhw")
        assert "{}".format(graph) == "<TaskGraph eShtp2faQgy4iZZOIhXvhw>"


@pytest.mark.asyncio
async def test_taskgraph_repr():
    with patch.object(taskcluster.aio.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = await TaskGraph("eShtp2faQgy4iZZOIhXvhw")
        assert repr(graph) == "<TaskGraph eShtp2faQgy4iZZOIhXvhw>"


@pytest.mark.asyncio
async def test_cache_file():
    tmpdir = tempfile.mkdtemp()
    os.environ["TC_CACHE_DIR"] = tmpdir
    with patch.object(taskcluster.aio.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = await TaskGraph("eShtp2faQgy4iZZOIhXvhw")
        # and again to hit the cached copy.
        graph = await TaskGraph("eShtp2faQgy4iZZOIhXvhw")
        assert repr(graph) == "<TaskGraph eShtp2faQgy4iZZOIhXvhw>"
