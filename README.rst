A higher level wrapper around `taskcluster-client.py <https://github.com/taskcluster/taskcluster-client.py>`_ with the aim of having a more Pythonic interface to taskcluster.

Currently aiming to get easier, read-only features available.

Installation
============

``pip install taskhuddler``

For further data analysis, add the optional Pandas dependency
-------------------------------------------------------------
``pip install taskhuddler[pandas]``

Examining a Task Group
======================

.. code-block:: python

    from taskhuddler import TaskGraph

    # All tasks will be cached in memory when TaskGraph is called
    # But this means data may get stale.
    graph = TaskGraph('M5hSue6oRSu_klunMRHolg')
    for task in graph.tasks():
        print(task.taskId)
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



Examining Tasks
===============

TaskDefinition, TaskStatus and Task are all available to work with tasks. A `Task` is a wrapper around
a TaskDefinition and a TaskStatus.



The Task class populates both a TaskStatus and TaskDefinition, each of which can be used by themselves
.. code-block:: python

    from taskhuddler import Task, TaskDefinition, TaskStatus
    from dataclasses import asdict

    mytask = Task.from_task_id('M5hSue6oRSu_klunMRHolg')
    print(task.status.state)

    print(asdict(task))

    my_task_def = TaskDefinition.from_task_id('M5hSue6oRSu_klunMRHolg')
    my_task_def = TaskDefinition.from_dict(mytask.task)

    my_task_status = TaskStatus.from_task_id('M5hSue6oRSu_klunMRHolg')
    my_task_status = TaskStatus.from_dict(mytask.status)




Pandas
======

With ``pip install taskhuddler[pandas]`` the ``to_datetime`` method becomes available,
returning a Pandas DataFrame with task and run data:

.. code-block:: python

    from taskhuddler import TaskGraph

    graph = TaskGraph('M5hSue6oRSu_klunMRHolg')

    df = graph.to_dataframe()

Plans
=====

* Reduce the per-query limit for cached graphs so the initial response is quicker
