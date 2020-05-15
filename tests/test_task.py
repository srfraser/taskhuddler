"""Test Task class."""

import datetime
import json
import os
from unittest.mock import patch

import dateutil.parser
import pytest
import taskcluster
from taskhuddler.task import Task, TaskDefinition, TaskStatus


def mocked_status(dummy, task_id):
    return get_dummy_task_status("completed.json")


def mocked_definition(dummy, task_id):
    return get_dummy_task_definition("completed.json")


def get_dummy_task_data(filename):
    with open(os.path.join(os.path.dirname(__file__), "data", filename)) as f:
        return json.loads(f.read()).get("tasks")[0]


def get_dummy_task_status(filename):
    full = get_dummy_task_data(filename)
    return {"status": full.get("status")}


def get_dummy_task_definition(filename):
    full = get_dummy_task_data(filename)
    return full.get("task")


def test_task_taskid():
    task = Task.from_dict(get_dummy_task_data("completed.json"))
    assert task.taskId == "A-8AqzvvRsqH9b0VHBXYjA"


@pytest.mark.parametrize("filename,state", (["completed.json", True], ["unscheduled.json", False], ["failed.json", False]))
def test_task_completed_bool(filename, state):
    task = Task.from_dict(get_dummy_task_data(filename))
    assert task.status.completed is state


@pytest.mark.parametrize("filename,expected", (["completed.json", "completed"], ["unscheduled.json", "unscheduled"], ["failed.json", "failed"]))
def test_task_state_completed(filename, expected):
    task = Task.from_dict(get_dummy_task_data(filename))
    assert task.status.state == expected


@pytest.mark.parametrize(
    "filename,expected",
    (
        ["completed.json", dateutil.parser.parse("2017-10-26T01:03:58.641Z")],
        ["unscheduled.json", None],
        ["missing.json", dateutil.parser.parse("2017-10-26T01:09:00.750Z")],
    ),
)
def test_task_scheduled(filename, expected):
    task = Task.from_dict(get_dummy_task_data(filename))
    assert task.status.scheduled == expected


@pytest.mark.parametrize(
    "filename,expected", (["completed.json", dateutil.parser.parse("2017-10-26T01:03:59.291Z")], ["unscheduled.json", None], ["missing.json", None])
)
def test_task_started(filename, expected):
    task = Task.from_dict(get_dummy_task_data(filename))
    assert task.status.started == expected


@pytest.mark.parametrize(
    "filename,expected", (["completed.json", dateutil.parser.parse("2017-10-26T01:18:11.852Z")], ["unscheduled.json", None], ["missing.json", None])
)
def test_task_resolved(filename, expected):
    task = Task.from_dict(get_dummy_task_data(filename))
    assert task.status.resolved == expected


@pytest.mark.parametrize(
    "filename, expected",
    (
        ["completed.json", [datetime.timedelta(seconds=852, microseconds=561000)]],
        ["failed.json", [datetime.timedelta(seconds=526, microseconds=231000)]],
        ["unscheduled.json", []],
    ),
)
def test_run_durations(filename, expected):
    task = Task.from_dict(get_dummy_task_data(filename))
    assert task.status.run_durations() == expected


@pytest.mark.parametrize("filename, expected", (["completed.json", "test"], ["failed.json", "nightly-l10n"]))
def test_task_kind(filename, expected):
    task = Task.from_dict(get_dummy_task_data(filename))
    assert task.kind == expected


@pytest.mark.parametrize("filename, expected", (["completed.json", False], ["failed.json", True]))
def test_task_has_failures(filename, expected):
    task = Task.from_dict(get_dummy_task_data(filename))
    assert task.status.has_failures == expected


@pytest.mark.parametrize(
    "filename, expected", (["completed.json", "test-windows10-64-nightly/opt-web-platform-tests-e10s-3"], ["failed.json", "nightly-l10n-linux-nightly-2/opt"])
)
def test_task_names(filename, expected):
    task = Task.from_dict(get_dummy_task_data(filename))
    assert task.label == expected
    assert task.task.name == expected


@pytest.mark.parametrize(
    "filename, expected",
    (
        ["completed.json", []],
        [
            "continuation1.json",
            [
                "project:releng:signing:cert:nightly-signing",
                "project:releng:signing:format:mar_sha384",
                "project:releng:signing:format:sha2signcode",
                "project:releng:signing:format:sha2signcodestub",
            ],
        ],
    ),
)
def test_scopes(filename, expected):
    task = Task.from_dict(get_dummy_task_data(filename))
    assert task.scopes == expected


def test_task_query_by_task_id():
    task_id = "A-8AqzvvRsqH9b0VHBXYjA"

    with patch.object(taskcluster.Queue, "task", new=mocked_definition), patch.object(taskcluster.Queue, "status", new=mocked_status):
        task = Task.from_task_id(task_id)
        assert task.kind == "test"
        assert task.status.state == "completed"


@pytest.mark.parametrize(
    "filename,started,is_completed,state",
    (
        ["completed.json", dateutil.parser.parse("2017-10-26T01:03:59.291Z"), True, "completed"],
        ["unscheduled.json", None, False, "unscheduled"],
        ["missing.json", None, False, "failed"],
    ),
)
def test_task_status_by_json(filename, started, is_completed, state):
    task = TaskStatus.from_dict(get_dummy_task_data(filename))
    assert task.started == started
    assert task.completed is is_completed
    assert task.state == state


def test_task_status_by_task_id():
    task_id = "A-8AqzvvRsqH9b0VHBXYjA"
    with patch.object(taskcluster.Queue, "status", new=mocked_status):
        task = TaskStatus.from_task_id(task_id)
        assert task.state == "completed"


def test_task_status_no_input():
    with pytest.raises(TypeError):
        TaskStatus()


def test_task_definition_no_input():
    with pytest.raises(TypeError):
        TaskDefinition()


def test_task_no_input():
    with pytest.raises(TypeError):
        Task()


def test_run_durations2():
    task = Task.from_dict(get_dummy_task_data("completed.json"))
    assert task.status.run_durations() == [datetime.timedelta(seconds=852, microseconds=561000)]


def test_task_str():
    task = Task.from_dict(get_dummy_task_data("completed.json"))
    assert "{}".format(task) == "<Task A-8AqzvvRsqH9b0VHBXYjA:completed>"


def test_task_repr():
    task = Task.from_dict(get_dummy_task_data("completed.json"))
    assert repr(task) == "<Task A-8AqzvvRsqH9b0VHBXYjA>"


def test_task_definition():
    with patch.object(taskcluster.Queue, "task", new=mocked_definition), patch.object(taskcluster.Queue, "status", new=mocked_status):
        taskdef = TaskDefinition.from_task_id("A-8AqzvvRsqH9b0VHBXYjA")
    assert taskdef.label == "test-windows10-64-nightly/opt-web-platform-tests-e10s-3"


def test_task_definition_only_def():
    taskdef = TaskDefinition.from_dict("taskid", get_dummy_task_definition("completed.json"))
    assert taskdef.label == "test-windows10-64-nightly/opt-web-platform-tests-e10s-3"


def test_task_definition_only_taskid():
    task_id = "A-8AqzvvRsqH9b0VHBXYjA"
    with patch.object(taskcluster.Queue, "task", new=mocked_definition), patch.object(taskcluster.Queue, "status", new=mocked_status):
        taskdef = TaskDefinition.from_task_id(task_id)
    assert taskdef.label == "test-windows10-64-nightly/opt-web-platform-tests-e10s-3"


def test_task_definition_empty():
    with pytest.raises(TypeError):
        TaskDefinition()


def test_task_definition_json_view():
    taskdef_json = get_dummy_task_definition("completed.json")
    taskdef = TaskDefinition.from_dict("taskid", taskdef_json)
    from dataclasses import asdict

    result = asdict(taskdef)
    del result["taskId"]
    assert result == taskdef_json
