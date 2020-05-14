import datetime
import json
import os
import tempfile
from unittest.mock import patch

import dateutil.parser
import pytest
import taskcluster
from taskhuddler.graph import TaskGraph

TASK_IDS = [
    "A-8AqzvvRsqH9b0VHBXYjA",
    "A-aPcZanRJaxM-IToHyyHw",
    "B-aPcZanRJaxM-IToHyyHw",
    "A0BaQjdkS8Wdy2Ev_1pLgA",
    "A0VWjOkmRNqkKrRUj83BEA",
    "A0cabJ3WTeCrDN15nbTPYw",
]


def mocked_listTaskGroup(dummy, groupid, query):
    if "continuationToken" in query:
        filename = "{}.json".format(query["continuationToken"])
    else:
        filename = "completed.json"

    with open(os.path.join(os.path.dirname(__file__), "data", filename)) as f:
        return json.loads(f.read())


def test_taskgraph_str():
    with patch.object(taskcluster.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw")
        assert "{}".format(graph) == "<TaskGraph eShtp2faQgy4iZZOIhXvhw>"


def test_taskgraph_repr():
    with patch.object(taskcluster.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw")
        assert repr(graph) == "<TaskGraph eShtp2faQgy4iZZOIhXvhw>"


def test_cache_file():
    tmpdir = tempfile.mkdtemp()
    os.environ["TC_CACHE_DIR"] = tmpdir
    with patch.object(taskcluster.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw")
        # and again to hit the cached copy.
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw")
        assert repr(graph) == "<TaskGraph eShtp2faQgy4iZZOIhXvhw>"
    del os.environ["TC_CACHE_DIR"]


@pytest.mark.parametrize("limit", [None, 2])
def test_taskgraph_tasks(limit):
    with patch.object(taskcluster.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw")
        found_taskids = [task.taskid for task in graph.tasks(limit=limit)]
        if limit:
            expected_task_ids = TASK_IDS[:limit]
        else:
            expected_task_ids = TASK_IDS

        assert found_taskids == expected_task_ids


@pytest.mark.parametrize("limit", [None, 2])
def test_taskgraph_limit_tasks(limit):
    with patch.object(taskcluster.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw", limit=limit)
        found_taskids = [task.taskid for task in graph.tasks()]
        if limit:
            expected_task_ids = TASK_IDS[:limit]
        else:
            expected_task_ids = TASK_IDS

        assert found_taskids == expected_task_ids


def test_task_timings():
    with patch.object(taskcluster.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw")
    expected = [
        {"duration": 852, "kind": "test", "platform": "windows10-64-nightly"},
        {"duration": 196, "kind": "repackage-signing", "platform": "windows2012-32"},
        {"duration": 71, "kind": "repackage-signing", "platform": "osx-cross"},
    ]
    timings = [t for t in graph.task_timings()]
    assert timings == expected


def test_kinds():
    with patch.object(taskcluster.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw")
    expected = ["nightly-l10n", "repackage-signing", "test", "beetmover-checksums", "missing-treeherder"]
    assert sorted(graph.kinds) == sorted(expected)


@pytest.mark.parametrize("kind,expected", [(None, 6), ("test", 1)])
def test_filter_kinds(kind, expected):
    with patch.object(taskcluster.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw")
    filtered = [t for t in graph.filter_tasks_by_kind(kind=kind)]
    assert len(filtered) == expected


def test_tasks_with_failures():
    with patch.object(taskcluster.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw")
    filtered = [t for t in graph.tasks_with_failures()]
    assert len(filtered) == 1


def test_task_names_with_failures():
    with patch.object(taskcluster.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw")
    filtered = [t for t in graph.task_names_with_failures()]
    assert filtered == ["nightly-l10n-linux-nightly-2/opt"]
    assert len(filtered) == 1


def test_taskgraph_completed_bool():
    with patch.object(taskcluster.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw")
        assert graph.completed is False


def test_graph_started():
    with patch.object(taskcluster.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw")
        assert graph.earliest_start_time == dateutil.parser.parse("2017-10-26T01:03:59.291Z")


def test_graph_completed():
    with patch.object(taskcluster.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw")
        assert graph.latest_finished_time == dateutil.parser.parse("2017-10-26T03:57:42.727Z")


def test_graph_states():
    with patch.object(taskcluster.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw")
        assert graph.current_states() == {"completed": 4, "failed": 1, "unscheduled": 1}


def test_graph_total_compute_time():
    with patch.object(taskcluster.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw")
        assert graph.total_compute_time() == datetime.timedelta(seconds=1316, microseconds=516000)


def test_graph_total_wall_time():
    with patch.object(taskcluster.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw")
        assert graph.total_wall_time() == datetime.timedelta(seconds=10423, microseconds=436000)


def test_graph_total_compute_wall_time():
    with patch.object(taskcluster.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw")
        assert graph.total_compute_wall_time() == datetime.timedelta(seconds=1245, microseconds=391000)


def test_graph_to_dataframe():
    with patch.object(taskcluster.Queue, "listTaskGroup", new=mocked_listTaskGroup):
        graph = TaskGraph("eShtp2faQgy4iZZOIhXvhw")
        df = graph.to_dataframe()
        assert sorted(df.taskid.to_list()) == sorted(
            ["A-8AqzvvRsqH9b0VHBXYjA", "A-aPcZanRJaxM-IToHyyHw", "A0BaQjdkS8Wdy2Ev_1pLgA", "A0VWjOkmRNqkKrRUj83BEA", "B-aPcZanRJaxM-IToHyyHw"]
        )
