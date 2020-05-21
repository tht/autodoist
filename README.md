# Autodoist

This program adds two major functionalities to Todoist to help automate your workflow:

1) Assign automatic `@next_action` labels for a more GTD-like workflow
2) Enable re-use of subtasks in lists with a recurring date

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

Make sure the label ```next_action``` exists in your Todoist before running the program. The default label can be changed, see the example at section [Additional Arguments](#additional-arguments) below. Todoist Premium is required in order to use labels and to make this functionality possible.

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

The program looks for all parentless tasks with a recurring date. If they contain sub-tasks, they will be restored in the same order when the parentless task is checked. Todoist Premium is not required for this functionality.

![See example](https://i.imgur.com/WKKd14o.gif)


# Executing Autodoist

You can run Autodoist from any system that supports Python.

## Running Autodoist

Autodoist will read your environment to retrieve your Todoist API key, so to run on Windows/Linux/Mac OSX you can use the following commandline:

    python autodoist.py -a <API Key>
    
If you want to enable recurring re-use mode, run with the `-r` argument:

    python autodoist.py -a <API Key> -r
    
## Additional arguments

Several arguments can be provided, for example to change the default label:

    python autodoist.py -l <label>

Or to change the suffix tags:

    python autodoist.py --parallel_suffix <tag>
    python autodoist.py --serial_suffix <tag>

In addition, if you experience issues with syncing you can change the api syncing time (default 10 seconds):
    
    python autodoist.py --delay <time in seconds>

For all arguments check help:

    python autodoist.py --help
