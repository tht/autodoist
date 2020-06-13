# Autodoist

This program adds three major functionalities to Todoist to help automate your workflow:

1) Assign automatic next-action labels for a more GTD-like workflow
   - Flexible options to label tasks sequentially or in parallel
   - Limit labels based on a start-date or hide future tasks based on the due date
2) Enable regeneration of sub-tasks in lists with a recurring date
3) Postpone the end-of-day time to after midnight to finish your daily recurring tasks

If this tool helped you out, I would really appreciate your support by providing me with some coffee!

<a href=https://ko-fi.com/hoffelhas>
 <img src="https://i.imgur.com/MU1rAPG.png" width="150">
</a>

# Requirements

* Python 3.8
* ```todoist-python``` package.

# 1. Automatic next action labels

The program looks for pre-defined tags in the name of every project and parentless tasks in your Todoist account to automatically add and remove `@next_action` labels. 

Projects and parentless tasks can be tagged independently from each other to create the required functionality. If this tag is not defined, it will not activate this functionality. The result will be a clear, current and comprehensive list of next actions without the need for further thought.

See the example given at [running autodoist](#running-autodoist) on how to run this mode. If the label does not exist yet in your Todoist, a possibility is given to automatiacally create it. Todoist Premium is required in order to use labels and to make this functionality possible.

## Sequential processing

If a project or parentless task ends with `--`, both the parentless tasks and its sub-tasks will be treated as a priority queue and the most important will be labeled. Importance is determined by order in the list.

![Serial task](https://i.imgur.com/SUkhPiE.gif)

## Parallel processing

If a project or parentless task name ends with `//`, both the parentless tasks and its sub-tasks will be treated as parallel. A waterfall processing is applied, where the lowest possible sub-tasks are labelled.

![Parallel task](https://i.imgur.com/NPTLQ8B.gif)

## Added labelling flexibility

If a project ends with `-/`, all parentless tasks are processed sequentially, and its sub-tasks in parallel.

[See example](https://i.imgur.com/uGJFeXB.gif)

If a project ends with `/-`, all parentless tasks are processed in parallel, and its sub-tasks sequentially.

[See example](https://i.imgur.com/5lZ1BVI.gif)

Any parentless task can also be be given a type by appending `//` or `--` to the name of the task. This works if there is no project type, and will override a previously defined project type.

[See example 1 with a parallel project](https://i.imgur.com/d9Qfq0v.gif)

[See example 2 with a serial project](https://i.imgur.com/JfaAOzZ.gif)

## Start/Due date enhanced experience

Two methods are provided to hide tasks that are not relevant yet.

- Prevent labels by defining a start-date. The label is only assigned if this date is reached. A start date can be added to a task by adding 'start-date=DD-MM-YYYY'.
[See an example of using start-dates](https://i.imgur.com/WJRoJzW.png).

- Prevent labels of all tasks if the due date is too far in the future. Define the amount by running with the argument '-hf <NUMBER_OF_DAYS>'.
[See an example of the hide-future functionality](https://i.imgur.com/LzSoRUm.png).

# 2. Regenerate sub-tasks in recurring lists

The program looks for all parentless tasks with a recurring date. If they contain sub-tasks, they will be regenerated in the same order when the parentless task is checked. Todoist Premium is not required for this functionality.

![See example](https://i.imgur.com/WKKd14o.gif)

# 3. Postpone the end-of-day

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

    python autodoist.py --pp_suffix <tag>
    python autodoist.py --ss_suffix <tag>
    
Or if you want to hide all tasks due in the future:

    python autodoist.py --hf <NUMBER_OF_DAYS>

In addition, if you experience issues with syncing you can increase the api syncing time (default 5 seconds):
    
    python autodoist.py --delay <time in seconds>

For all arguments, please check out the help:

    python autodoist.py --help
