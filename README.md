
A higher level wrapper around [taskcluster-client.py](https://github.com/taskcluster/taskcluster-client.py) with the aim of having a more Pythonic interface to taskcluster.

Currently aiming to get easier, read-only features available.

## Installation

`pip install taskhuddler`

### For further data analysis, add the optional Pandas dependency
`pip install taskhuddler[pandas]`

## Synchronous Usage

```python
from taskhuddler import TaskGraph

# All tasks will be cached in memory when TaskGraph is called
# But this means data may get stale.
graph = TaskGraph('M5hSue6oRSu_klunMRHolg')
for task in graph.tasks():
    # These two are equivalent. Task() object knows about some features of a task
    print(task.json['status']['taskId'])
    print(task.taskid)  
# Fetch the set of tasks again.
graph.fetch_tasks()

# On-disk caching:
os.environ['TC_CACHE_DIR'] = '/tmp/cache/'
# All future TaskGraph calls from now on will write the
# json to TC_CACHE_DIR and will avoid a call to taskcluster


# Are all the tasks in the 'completed' state?
print(graph.completed)

if graph.completed:
    started = graph.earliest_start_time
    finished = graph.latest_finished_time
    print("Graph took {} to run".format(finished-started))

```

## Pandas

With `pip install taskhuddler[pandas]` the `to_datetime` method becomes available,
returning a Pandas DataFrame with task and run data:
```python
from taskhuddler import TaskGraph

graph = TaskGraph('M5hSue6oRSu_klunMRHolg')

df = graph.to_datetime()
```

## Plans


* Reduce the per-query limit for cached graphs so the initial response is quicker
