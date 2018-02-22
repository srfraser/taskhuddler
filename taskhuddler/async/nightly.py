"""Extract useful information from Nightly taskgraphs."""

from taskcluster.async import Index, Queue
from datetime import datetime, timedelta
import asyncio
import aiohttp
import logging
from taskhuddler.async.graph import TaskGraph

log = logging.getLogger(__name__)

VALID_PLATFORMS = [
    'linux-opt',
    'linux64-opt',
    'macosx64-opt',
    'win32-opt',
    'win64-opt'
]


async def load_nightly_graph(dt=None, platform='linux-opt'):
    """Given a date, load the relevant nightly task graph."""
    with aiohttp.ClientSession() as session:
        index = Index(session=session)
        queue = Queue(session=session)

        if not dt:
            dt = datetime.now()

        datestr = dt.strftime("%Y.%m.%d")
        basestr = "gecko.v2.mozilla-central.nightly.{date}.latest.firefox.{platform}"

        found = await index.findTask(basestr.format(date=datestr, platform=platform))
        taskid = found.get('taskId')

        taskdef = await queue.task(taskid)
        # except taskcluster.exceptions.TaskclusterRestFailure:

        taskgroup = taskdef.get('taskGroupId')
        log.debug("Looking at {} for {}".format(taskgroup, datestr))
        if taskgroup:
            return {'date': datestr, 'graph': await TaskGraph(taskgroup)}

    return None


async def find_nightly_graphs(start=None, end=None, platform='linux-opt'):
    """Return a dict of nightly TaskGraphs between the provided dates."""
    if not start:
        start = datetime.now() - timedelta(1)
    if not end:
        end = datetime.now()

    current = end

    tasks = list()

    while current > start:
        log.info("Looking at {}".format(current))
        current = current - timedelta(1)
        tasks.append(asyncio.ensure_future(load_nightly_graph(current)))
    results = await asyncio.gather(*tasks)

    return {r['date']: r['graph'] for r in results if r}
