"""class Task, to extract data about tasks."""

import json
from dataclasses import dataclass, field
from typing import List

import dateutil.parser
from taskcluster import Queue

from .utils import tc_options


@dataclass
class TaskDefinition:
    """Data and queries about a task definition."""

    taskId: str
    provisionerId: str = field(repr=False)  # TODO remove all these, include repr.
    workerType: str = field(repr=False)
    schedulerId: str = field(repr=False)
    taskGroupId: str = field(repr=False)
    dependencies: list = field(repr=False)
    requires: str = field(repr=False)
    routes: list = field(repr=False)
    priority: str = field(repr=False)
    retries: int = field(repr=False)
    created: str = field(repr=False)
    deadline: str = field(repr=False)
    expires: str = field(repr=False)
    scopes: list = field(repr=False)
    payload: dict = field(repr=False)
    metadata: dict = field(repr=False)
    tags: dict = field(repr=False)
    extra: dict = field(repr=False)

    @classmethod
    def from_dict(cls, taskId, data):
        """Create TaskDefinition from existing data.

        taskId is not reurned from queue.task but will be in data from
        listTaskGroup
        """
        if "taskId" in data:
            return cls(**data)
        return cls(taskId, **data)

    @classmethod
    def from_task_id(cls, task_id):
        queue = Queue(tc_options())
        taskdef = queue.task(task_id)
        return cls(taskId=task_id, **taskdef)

    @property
    def label(self):
        """Extract label."""
        return self.tags.get("label", self.metadata.get("name", ""))

    @property
    def kind(self):
        """Return the task's kind."""
        return self.tags.get("kind", "")

    @property
    def name(self):
        """Return the name of the task."""
        return self.metadata["name"]


@dataclass
class RunStatus:
    runId: int
    state: str
    reasonCreated: str
    reasonResolved: str
    workerGroup: str
    workerId: str
    takenUntil: str
    scheduled: str
    started: str
    resolved: str


@dataclass
class TaskStatus:
    taskId: str
    provisionerId: str = field(repr=False)
    workerType: str = field(repr=False)
    schedulerId: str = field(repr=False)
    taskGroupId: str = field(repr=False)
    deadline: str = field(repr=False)
    expires: str = field(repr=False)
    retriesLeft: int = field(repr=False)
    state: str
    runs: List[RunStatus] = field(default_factory=list, repr=False)

    @classmethod
    def from_dict(cls, data):
        return cls(**data.get("status", data))

    @classmethod
    def from_task_id(cls, task_id):
        queue = Queue(tc_options())
        status = queue.status(task_id)
        return cls(**status["status"])

    @property
    def has_failures(self):
        """Return True if this task has any run failures."""
        return len([r for r in self.runs if r.get("state") in ["failed", "exception"]]) > 0

    @property
    def completed(self):
        """Return True if this task has completed."""
        return self.state == "completed"

    def _extract_date(self, run_field, run_id=-1):
        """Return datetime of the given field in the task runs."""
        if not self.runs:
            return
        field_data = self.runs[run_id].get(run_field)
        if not field_data:
            return
        return dateutil.parser.parse(field_data)

    @property
    def scheduled(self):
        """Return datetime of the task scheduled time."""
        if self.state == "unscheduled":
            return
        return self._extract_date("scheduled")

    @property
    def started(self):
        """Return datetime of the most recent run's start."""
        return self._extract_date("started")

    @property
    def resolved(self):
        """Return datetime of the most recent run's finish time."""
        return self._extract_date("resolved")

    def run_durations(self):
        """Return a list of timedelta objects, of run durations."""
        durations = list()
        for run in self.runs:
            started = run.get("started")
            resolved = run.get("resolved")
            if started and resolved:
                durations.append(dateutil.parser.parse(resolved) - dateutil.parser.parse(started))
        return durations

    @property
    def latest_runid(self):
        """Return the most recent runId."""
        return max([run.get("runId", 0) for run in self.runs], default=None)


@dataclass
class TaskArtifact:
    """Understanding task arifacts."""

    name: str
    expires: str
    storage_type: str
    content_type: str
    task_id: str
    run_id: str

    @classmethod
    def from_dict(cls, data, task_id=None, run_id=None):
        return cls(
            task_id=task_id, run_id=run_id, name=data["name"], expires=data["expires"], storage_type=data["storageType"], content_type=data["contentType"]
        )

    def simple_name_match(self, pattern):
        return pattern in self.name

    def fetch(self, queue=None):
        self.queue = queue
        if self.queue is None:
            self.queue = Queue(tc_options())
        if self.run_id:
            return self.queue.getArtifact(self.task_id, self.run_id, self.name)
        else:
            return self.queue.getLatestArtifact(self.task_id, self.name)


# Should this be a dataclass itself? How does that work?
@dataclass(repr=False)
class Task:
    """Collected information about a single task."""

    task: TaskDefinition
    status: TaskStatus
    artifact_store: list = field(default_factory=list)

    @classmethod
    def from_dict(cls, data):
        return cls(TaskDefinition.from_dict(data["status"]["taskId"], data["task"]), TaskStatus.from_dict(data["status"]))

    @classmethod
    def from_task_id(cls, task_id):
        queue = Queue(tc_options())
        status = queue.status(task_id)
        taskdef = queue.task(task_id)
        return cls(TaskDefinition.from_dict(task_id, taskdef), TaskStatus.from_dict(status["status"]))

    def __repr__(self):
        """repr."""
        return "<Task {}>".format(self.task_id)

    def __str__(self):
        """Str representation."""
        return "<Task {}:{}>".format(self.task_id, self.status.state)

    @property
    def taskId(self):
        """Ease-of-use wrapper."""
        return self.task.taskId

    @property
    def task_id(self):
        """Name compatibility wrapper."""
        return self.task.taskId

    @property
    def label(self):
        return self.task.label

    @property
    def kind(self):
        return self.task.kind

    @property
    def scopes(self):
        return self.task.scopes

    def artifacts(self):
        """List artifacts the task has produced."""
        if not self.status:
            return list()
        if not self.artifact_store:
            queue = Queue(tc_options())
            list_artifacts = queue.listArtifacts(self.task_id, self.status.latest_runid, query={})
            self.artifact_store = [TaskArtifact.from_dict(a, task_id=self.task_id, run_id=self.status.latest_runid) for a in list_artifacts["artifacts"]]
        return self.artifact_store

    def artifacts_matching(self, pattern):
        if not self.status:
            return list()
        for artifact in self.artifacts():
            if pattern in artifact.name:
                yield artifact

    def fetch_artifact(self, name, destination=None):
        for artifact in self.artifacts_matching(name):
            content = artifact.fetch()
            if not destination:
                return content
            with open(destination, "w") as f:
                if isinstance(content, str):
                    f.write(content)
                else:
                    json.dump(content, f, indent=4)

    def fetch_artifacts_matching(self, pattern):
        for artifact in self.artifacts_matching(pattern):
            content = artifact.fetch()
            with open("test.json", "w") as f:
                json.dump(content, f, indent=4)
