"""Helpful wrapper around release related taskcluster operations."""

import datetime
import json
import logging
import os
from collections import defaultdict

from taskcluster import Queue

from .task import Task
from .utils import Range, fetch_file, merge_date_list, store_file, tc_options

log = logging.getLogger(__name__)


class TaskGraph(object):
    """Helper class for dealing with Task Graphs."""

    def __init__(self, groupid, limit=None):
        """init."""
        self.groupid = groupid
        self.tasklist = None

        if 'TC_CACHE_DIR' in os.environ:
            self.cache_file = os.path.join(os.environ.get(
                'TC_CACHE_DIR'), "{}.json".format(self.groupid))
        else:
            self.cache_file = None

        self.fetch_tasks(limit=limit)

    def __repr__(self):
        """repr."""
        return "<TaskGraph {}>".format(self.groupid)

    def __str__(self):
        """Str representation."""
        return "<TaskGraph {}>".format(self.groupid)

    def fetch_tasks(self, limit=None):
        """
        Return tasks with the associated group ID.

        Handles continuationToken without the user being aware of it.

        Enforces the limit parameter as a limit of the total number of tasks
        to be returned.
        """
        if self.cache_file:
            if self._read_file_cache():
                return

        query = {}
        if limit:
            # Default taskcluster-client api asks for 1000 tasks.
            query['limit'] = min(limit, 1000)

        def under_limit(length):
            """Indicate if we've returned enough tasks."""
            if not limit or length < limit:
                return True
            return False

        queue = Queue(options=tc_options())
        outcome = queue.listTaskGroup(self.groupid, query=query)
        tasks = outcome.get('tasks', [])
        while under_limit(len(tasks)) and outcome.get('continuationToken'):
            query.update({
                'continuationToken': outcome.get('continuationToken')
            })
            outcome = queue.listTaskGroup(self.groupid, query=query)
            tasks.extend(outcome.get('tasks', []))

        if limit:
            tasks = tasks[:limit]
        self.tasklist = [Task(json=data) for data in tasks]

        if self.cache_file:
            self._write_file_cache()

    def _write_file_cache(self):
        store_file(self.cache_file, json.dumps(self.tasks(as_json=True)))

    def _read_file_cache(self):
        try:
            jsondata = json.loads(fetch_file(self.cache_file))
            self.tasklist = [Task(json=data) for data in jsondata]
        except Exception as e:
            log.debug(e)
            return False
        return True

    def tasks(self, limit=None, as_json=False):
        """Return all tasks in the graph."""
        if as_json:
            return [t.json for t in self.tasklist[:limit]]
        else:
            return self.tasklist[:limit]

    @property
    def completed(self):
        """Have all the tasks completed.

        Returns bool.
        """
        return all([task.completed for task in self.tasks()])

    def current_states(self):
        """Count the occurences of current states."""
        states = defaultdict(int)
        for state in [task.state for task in self.tasks()]:
            states[state] += 1
        return states

    @property
    def earliest_start_time(self):
        """Find the earliest start time for any task in the graph."""
        return min([task.started for task in self.tasks() if task.started])

    @property
    def latest_finished_time(self):
        """Find the latest finish time for resolved tasks."""
        return max([task.resolved for task in self.tasks() if task.resolved])

    def total_compute_time(self):
        """Sum of all the task run times, as timedelta."""
        return sum([sum(task.run_durations(), datetime.timedelta(0)) for task in self.tasks() if task.completed], datetime.timedelta(0, 0))

    def total_wall_time(self):
        """Return the total wall time for this graph.

        May not be a useful value if human decision tasks exist
        """
        return self.latest_finished_time - self.earliest_start_time

    def total_compute_wall_time(self):
        """Return the total time spent running tasks, ignoring wait times."""
        dt_list = [Range(start=task.started, end=task.resolved)
                   for task in self.tasks() if task.completed]
        merged = merge_date_list(dt_list)
        return sum([m.end - m.start for m in merged], datetime.timedelta(0, 0))

    def task_timings(self):
        """For every finished task that has fields we group on, report duration."""
        for task in self.tasklist:
            if not task.completed:
                continue
            try:
                kind = task.json['task']['tags']['kind']
                platform = task.json['task']['extra']['treeherder']['machine']['platform']
            except KeyError:
                continue
            yield {
                'kind': kind,
                'platform': platform,
                'duration': (task.resolved - task.started).seconds
            }

    def to_dataframe(self):
        """Return a Pandas dataframe containing task data."""
        try:
            import pandas as pd
        except ModuleNotFoundError:
            raise NotImplementedError('Please install Pandas: taskhuddler[pandas]')

        entries = list()
        for task in self.tasklist:
            for run in task.status_json.get('runs', list()):
                # Some tasks have no platform
                try:
                    platform = task.json['task']['extra']['treeherder']['machine']['platform']
                except KeyError:
                    platform = None
                entries.append({
                    'name': task.name,
                    'taskid': task.taskid,
                    'kind': task.kind,
                    'platform': platform,
                    'worker_type': task.status_json.get('workerType'),
                    'worker_id': run.get('workerId'),
                    'run_id': run['runId'],
                    'scheduled': run.get('scheduled'),
                    'started': run.get('started'),
                    'resolved': run.get('resolved'),
                    'state': run.get('state'),

                })
        df = pd.DataFrame.from_dict(entries)
        df['scheduled'] = pd.to_datetime(df.scheduled)
        df['started'] = pd.to_datetime(df.started)
        df['resolved'] = pd.to_datetime(df.resolved)
        return df

    @property
    def kinds(self):
        """Return a list of the task kinds in use."""
        return list(set([task.kind for task in self.tasklist if task.kind != '']))

    def filter_tasks_by_kind(self, kind=None):
        """Return only those tasks of the given kind.

        Arguments:
            kind: string, may contain regex

        """
        import re
        for task in self.tasklist:
            if not kind:
                yield task
            elif re.match(kind, task.kind):
                yield task

    def tasks_with_failures(self):
        """Return tasks which have failures in any run."""
        for task in self.tasklist:
            if task.has_failures:
                yield task

    def task_names_with_failures(self):
        """Return the names of tasks which have failures."""
        for task in self.tasks_with_failures():
            yield task.name
