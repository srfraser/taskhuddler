import json
import os
from unittest.mock import patch

import dateutil.parser
import pytest
import taskcluster
from taskhuddler.aio import Task, TaskDefinition, TaskStatus


async def mocked_status(dummy, task_id):
    return get_dummy_task_status("completed.json")


async def mocked_definition(dummy, task_id):
    return get_dummy_task_definition("completed.json")


def get_dummy_task_json(filename):
    with open(os.path.join(os.path.dirname(__file__), "data", filename)) as f:
        return json.loads(f.read()).get("tasks")[0]


def get_dummy_task_status(filename):
    full = get_dummy_task_json(filename)
    return full.get("status")


def get_dummy_task_definition(filename):
    full = get_dummy_task_json(filename)
    return full.get("task")


@pytest.mark.asyncio
async def test_task_str():
    with patch.object(taskcluster.aio.Queue, "status", new=mocked_status), patch.object(taskcluster.aio.Queue, "task", new=mocked_definition):
        task = await Task(task_id="A-8AqzvvRsqH9b0VHBXYjA")
        assert "{}".format(task) == "<Task A-8AqzvvRsqH9b0VHBXYjA:completed>"
        assert repr(task) == "<Task A-8AqzvvRsqH9b0VHBXYjA>"


@pytest.mark.parametrize(
    "filename,started,is_completed,state",
    (
        ["completed.json", dateutil.parser.parse("2017-10-26T01:03:59.291Z"), True, "completed"],
        ["unscheduled.json", None, False, "unscheduled"],
        ["missing.json", None, False, "failed"],
    ),
)
@pytest.mark.asyncio
async def test_task_status_by_json(filename, started, is_completed, state):
    task = await TaskStatus(json=get_dummy_task_json(filename))
    assert task.started == started
    assert task.completed is is_completed
    assert task.state == state


@pytest.mark.asyncio
async def test_task_status_by_task_id():
    task_id = "A-8AqzvvRsqH9b0VHBXYjA"
    with patch.object(taskcluster.aio.Queue, "status", new=mocked_status):
        task = await TaskStatus(task_id=task_id)
        assert task.state == "completed"


@pytest.mark.asyncio
async def test_task_status_no_input():
    with pytest.raises(ValueError):
        await TaskStatus()


@pytest.mark.asyncio
async def test_taskstatus_str():
    with patch.object(taskcluster.aio.Queue, "status", new=mocked_status):
        task = await TaskStatus(task_id="A-8AqzvvRsqH9b0VHBXYjA")
        assert "{}".format(task) == "<TaskStatus A-8AqzvvRsqH9b0VHBXYjA:completed>"
        assert repr(task) == "<TaskStatus A-8AqzvvRsqH9b0VHBXYjA>"


@pytest.mark.asyncio
async def test_taskdef_str():
    with patch.object(taskcluster.aio.Queue, "task", new=mocked_definition):
        task = await TaskDefinition(task_id="A-8AqzvvRsqH9b0VHBXYjA")
        assert "{}".format(task) == "<TaskDefinition A-8AqzvvRsqH9b0VHBXYjA>"
        assert repr(task) == "<TaskDefinition A-8AqzvvRsqH9b0VHBXYjA>"
