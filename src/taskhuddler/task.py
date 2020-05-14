"""class Task, to extract data about tasks."""

import dateutil.parser
from taskcluster import Queue

from .utils import tc_options


class TaskDefinition:
    """Data and queries about a task definition."""

    def __init__(self, json=None, task_id=None, queue=None):
        """Init."""
        # taskId is not provided in the definition
        if task_id:
            self.task_id = task_id
        if json:
            self.def_json = json.get("task", json)
            return
        if not task_id:
            raise ValueError("No task definition or taskId provided")
        self.queue = queue
        if self.queue is None:
            self.queue = Queue(tc_options())
        self._fetch_definition()

    def _fetch_definition(self):
        self.def_json = self.queue.task(self.task_id)

    def __repr__(self):
        """repr."""
        return "<TaskDefinition {}>".format(self.task_id)

    def __str__(self):
        """Str representation."""
        return "<TaskDefinition {}>".format(self.task_id)

    @property
    def json(self):
        """Return json."""
        return self.def_json

    @property
    def label(self):
        """Extract label."""
        return self.def_json.get("tags", {}).get("label", self.def_json.get("metadata").get("name", ""))

    @property
    def kind(self):
        """Return the task's kind."""
        return self.def_json["tags"].get("kind", "")

    @property
    def scopes(self):
        """Return a list of the scopes used, if any."""
        return self.def_json.get("scopes", [])

    @property
    def name(self):
        """Return the name of the task."""
        return self.def_json["metadata"]["name"]


class TaskStatus:
    """Data and queries about a task status."""

    def __init__(self, json=None, task_id=None, queue=None):
        """Init."""
        if task_id:
            self.task_id = task_id
        if json:
            # We might be passed {'status': ... } or just the contents
            self.status_json = json.get("status", json)
            self.task_id = self.status_json["taskId"]
            return
        if not task_id:
            raise ValueError("No task definition or taskId provided")
        self.queue = queue
        if not self.queue:
            self.queue = Queue(tc_options())
        self._fetch_status()

    def _fetch_status(self):
        json = self.queue.status(self.task_id)
        self.status_json = json.get("status", json)

    def __repr__(self):
        """repr."""
        return "<TaskStatus {}>".format(self.task_id)

    def __str__(self):
        """Str representation."""
        return "<TaskStatus {}:{}>".format(self.task_id, self.state)

    @property
    def json(self):
        """Return json."""
        return self.status_json

    @property
    def state(self):
        """Return current task state."""
        return self.status_json.get("state", "")

    @property
    def has_failures(self):
        """Return True if this task has any run failures."""
        return len([r for r in self.status_json.get("runs", list()) if r.get("state") in ["failed", "exception"]]) > 0

    @property
    def completed(self):
        """Return True if this task has completed.

        Returns: Bool
            if the highest runId has state 'completed'

        """
        return self.state == "completed"

    def _extract_date(self, run_field, run_id=-1):
        """Return datetime of the given field in the task runs."""
        if not self.status_json.get("runs"):
            return
        field_data = self.status_json["runs"][run_id].get(run_field)
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
        if not self.json["status"].get("runs"):
            return durations
        for run in self.status_json.get("runs", list()):
            started = run.get("started")
            resolved = run.get("resolved")
            if started and resolved:
                durations.append(dateutil.parser.parse(resolved) - dateutil.parser.parse(started))
        return durations


class Task(TaskDefinition, TaskStatus):
    """Collected information about a single task."""

    def __init__(self, json=None, task_id=None, queue=None):
        """init."""
        if json:
            self.def_json = json.get("task")
            self.status_json = json.get("status")
            self.task_id = self.status_json["taskId"]
            return
        if task_id:
            self.task_id = task_id
        else:
            raise ValueError("No task definition or taskId provided")
        self.queue = queue
        if not self.queue:
            self.queue = Queue(tc_options())
        if self.task_id:
            self._fetch_definition()
            self._fetch_status()

    def __repr__(self):
        """repr."""
        return "<Task {}>".format(self.task_id)

    def __str__(self):
        """Str representation."""
        return "<Task {}:{}>".format(self.task_id, self.state)

    @property
    def taskid(self):
        """Compatibility wrapper."""
        return self.task_id

    @property
    def json(self):
        """Reconstruct json as presented by listTaskGroup."""
        return {"task": self.def_json, "status": self.status_json}
