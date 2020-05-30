# Autodoist

This program adds two major functionalities to Todoist to help automate your workflow:

1) Assign automatic `@next_action` labels for a more GTD-like workflow
2) Enable regeneration of sub-tasks in lists with a recurring date
3) Postpone the end-of-day time to after midnight to finish your daily recurring tasks

If this tool helped you out, I would really appreciate your support by providing me with some coffee!

<a href=https://ko-fi.com/hoffelhas>
 <img src="https://i.imgur.com/MU1rAPG.png" width="150">
</a>

# Requirements

* Python 3.8
* ```todoist-python``` package.

# Automatic next action labels

The program looks for pre-defined tags in the name of every project and parentless tasks in your Todoist account to automatically add and remove `@next_action` labels. 

Projects and parentless tasks can be tagged independently from each other to create the required functionality. If this tag is not defined, it will not activate this functionality. The result will be a clear, current and comprehensive list of next actions without the need for further thought.

See the example given at [running autodoist](#running-autodoist) on how to run this mode. Make sure that the label exists in your Todoist before running. Todoist Premium is required in order to use labels and to make this functionality possible.

## Sequential list processing

If a project or parentless task ends with `--`, the sub-tasks will be treated as a priority queue and the most important will be labeled `@next_action`. Importance is determined by order in the list.

![Serial task](https://i.imgur.com/SUkhPiE.gif)

## Parallel list processing

If a project or parentless task name ends with `//`, the sub-tasks will be treated as parallel `@next_action`s.
A waterfall processing is applied, where the lowest possible sub-tasks are labelled.

![Parallel task](https://i.imgur.com/NPTLQ8B.gif)

## Parentless tasks

Any parentless task can be be given a type by appending `//` or `--` to the name of the task. This works if there is no project type, and will override a previously defined project type.

[See example 1 with a parallel project](https://i.imgur.com/d9Qfq0v.gif)

[See example 2 with a serial project](https://i.imgur.com/JfaAOzZ.gif)

# Recurring lists

The program looks for all parentless tasks with a recurring date. If they contain sub-tasks, they will be regenerated in the same order when the parentless task is checked. Todoist Premium is not required for this functionality.

![See example](https://i.imgur.com/WKKd14o.gif)

# Postpone the end-of-day

You have a daily recurring task, but you're up working late and now it's past midnight. Todoist will automatically mark it overdue and when you check it, it moved to tomorrow. After a good nights rest you can't complete the task that day!

By setting an alternative time for the end-of-day you can now finish your work after midnight and the new date will automatically be corrected for you. Todoist Premium is not required for this functionality.

![See example 1](https://i.imgur.com/tvnTMOJ.gif)

# Executing Autodoist

You can run Autodoist from any system that supports Python.

## Running Autodoist

Autodoist will read your environment to retrieve your Todoist API key and additional arguments. In order to run on Windows/Linux/Mac OSX you can use the following commandlines.
    
If you want to enable labelling mode, run with the `-l` argument:

    python autodoist.py -a <API Key> -l <LABEL_NAME>
    
If you want to enable regeneration of sub-tasks in recurring lists, run with the `-r` argument:

    python autodoist.py -a <API Key> -r
    
If you want to enable an alternative end-of-day, run with the `-e` argument and a number from 1 to 24 to specify which hour:

    python autodoist.py -a <API Key> -e <NUMBER>
    
These modes can be run individually, or combined with each other.

## Additional arguments

Several additional arguments can be provided, for example to change the suffix tags for parallel and sequential projects:

    python autodoist.py --p_suffix <tag>
    python autodoist.py --s_suffix <tag>

In addition, if you experience issues with syncing you can increase the api syncing time (default 5 seconds):
    
    python autodoist.py --delay <time in seconds>

For all arguments check the help:

    python autodoist.py --help
