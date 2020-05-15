"""Helpful wrapper around release related taskcluster operations."""

import logging
from dataclasses import dataclass

from taskcluster.aio import Queue
from taskhuddler.task import Task as SyncTask
from taskhuddler.task import TaskArtifact as SyncTaskArtifact
from taskhuddler.task import TaskDefinition as SyncTaskDefinition
from taskhuddler.task import TaskStatus as SyncTaskStatus
from taskhuddler.utils import tc_options

log = logging.getLogger(__name__)


@dataclass
class TaskDefinition(SyncTaskDefinition):
    """Helper class for dealing with Tasks, asyncio version."""

    @classmethod
    async def from_task_id(cls, task_id):
        queue = Queue(tc_options())
        taskdef = await queue.task(task_id)
        return cls(taskId=task_id, **taskdef)


@dataclass
class TaskStatus(SyncTaskStatus):
    """Helper class for dealing with Tasks, asyncio version."""

    @classmethod
    async def from_task_id(cls, task_id):
        queue = Queue(tc_options())
        status = await queue.status(task_id)
        return cls(**status["status"])


@dataclass
class TaskArtifact(SyncTaskArtifact):
    """Understanding task artifacts."""

    async def fetch(self, queue=None):
        self.queue = queue
        if self.queue is None:
            self.queue = Queue(tc_options())
        if self.run_id:
            return await self.queue.getArtifact(self.task_id, self.run_id, self.name)
        else:
            return await self.queue.getLatestArtifact(self.task_id, self.name)


@dataclass(repr=False)
class Task(SyncTask):
    """Helper class for dealing with Tasks, asyncio version."""

    @classmethod
    async def from_task_id(cls, task_id):
        queue = Queue(tc_options())
        status = await queue.status(task_id)
        taskdef = await queue.task(task_id)
        return cls(TaskDefinition.from_dict(task_id, taskdef), TaskStatus.from_dict(status["status"]))
