NextAction
==========

A more GTD-like workflow for Todoist.

This program looks for pre-defined tags in every list and parentless task in your Todoist account to automatically add and remove `@next_action` labels.

The result will be a clear, current and comprehensive list of next actions without the need for further thought.

Uses the Todoist Sync API; note that Todoist Premium is required to function properly, since labels are used.

Requirements
============

* Python 3.8
* ```todoist-python``` package.

Activating NextAction
=====================

Projects and parentless tasks can be tagged independently from each other to create the required functionality.

Sequential list processing
--------------------------
If a project or task ends with `--`, the child tasks will be treated as a priority queue and the most important will be labeled `@next_action`. Importance is determined by order in the list.

Parallel list processing
------------------------
If a project or task name ends with `//`, the child tasks will be treated as parallel `@next_action`s.
A waterfall processing is applied, where the lowest possible child tasks are labelled.

Parentless tasks
------------------------
Any parentless task can be be given a type by appending `//` or `--` to the name of the task. This works if there is no list type, and will override a previously defined list type.

Executing NextAction
====================

You can run NexAction from any system that supports Python.

Running NextAction
------------------

NextAction will read your environment to retrieve your Todoist API key, so to run on a Linux/Mac OSX you can use the following commandline

    python nextaction.py -a <API Key>

Additional arguments
------------------

Several arguments can be provided, for example to change the default label:

    python nextaction.py -l <label>

Or to change the suffix tags:

    python nextaction.py --parallel_suffix <tag>
    python nextaction.py --serial_suffix <tag>
    
