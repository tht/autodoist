#!/usr/bin/python3

from todoist.api import TodoistAPI
from datetime import datetime
import sys
import time
import requests
import argparse
import logging
from datetime import datetime
global overview_item_ids
global overview_item_labels


def make_wide(formatter, w=120, h=36):
    """Return a wider HelpFormatter, if possible."""
    try:
        # https://stackoverflow.com/a/5464440
        # beware: "Only the name of this class is considered a public API."
        kwargs = {'width': w, 'max_help_position': h}
        formatter(None, **kwargs)
        return lambda prog: formatter(prog, **kwargs)
    except TypeError:
        logging.error("Argparse help formatter failed, falling back.")
        return formatter


def main():

    # Version
    current_version = 'v1.2'

    """Main process function."""
    parser = argparse.ArgumentParser(
        formatter_class=make_wide(argparse.HelpFormatter, w=110, h=50))
    parser.add_argument('-a', '--api_key',
                        help='Takes your Todoist API Key.', type=str)
    parser.add_argument(
        '-l', '--label', help='Enable next action labelling. Define which label to use.', type=str)
    parser.add_argument(
        '-r', '--recurring', help='Enable regeneration of sub-tasks in recurring lists.', action='store_true')
    parser.add_argument(
        '-e', '--end', help='Enable alternative end-of-day time instead of default midnight. Enter a number from 1 to 24 to define which hour is used.', type=int)
    parser.add_argument(
        '-d', '--delay', help='Specify the delay in seconds between syncs (default 5).', default=5, type=int)
    parser.add_argument(
        '-ps', '--p_suffix', help='Change suffix for parallel labeling (default "//").', default='//')
    parser.add_argument(
        '-ss', '--s_suffix', help='Change suffix for sequential labeling (default "--").', default='--')
    parser.add_argument('-hf', '--hide_future', help='Skip labelling future tasks after the specified number of days (default 7).',
                        default=7, type=int)
    parser.add_argument(
        '--onetime', help='Update Todoist once and exit.', action='store_true')
    parser.add_argument(
        '--nocache', help='Disables caching data to disk for quicker syncing.', action='store_true')
    parser.add_argument('--debug', help='Enable detailed debugging in log.',
                        action='store_true')
    parser.add_argument('--inbox', help='The method the Inbox should be processed with.',
                        default=None, choices=['parallel', 'sequential'])
    args = parser.parse_args()

    # Set debug
    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(level=log_level,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        handlers=[logging.FileHandler(
                            'debug.log', 'w+', 'utf-8'),
                            logging.StreamHandler()]
                        )

    def sync(api):
        try:
            logging.debug('Syncing the current state from the API')
            api.sync()
        except Exception as e:
            logging.exception(
                'Error trying to sync with Todoist API: %s' % str(e))
            quit()

    def initialise(args):

        # Check we have a API key
        if not args.api_key:
            logging.error(
                "\n\nNo API key set. Run Autodoist with '-a <YOUR_API_KEY>'\n")
            sys.exit(1)

        # Check if AEOD is used
        if args.end is not None:
            if args.end < 1 or args.end > 24:
                logging.error(
                    "\n\nPlease choose a number from 1 to 24 to indicate which hour is used as alternative end-of-day time.\n")
                sys.exit(1)
        else:
            pass

        # Show which modes are enabled:
        modes = []
        m_num = 0
        for x in [args.label, args.recurring, args.end]:
            if x:
                modes.append('Enabled')
                m_num += 1
            else:
                modes.append('Disabled')

        logging.info("\nYou are running with the following functionalities:\n\n   Next action labelling mode: {}\n   Regenerate sub-tasks mode: {}\n   Shifted end-of-day mode: {}\n".format(*modes))

        if m_num == 0:
            logging.info("\n No functionality has been enabled. Please see --help for the available options.\n")
            exit(0)

        # Run the initial sync
        logging.debug('Connecting to the Todoist API')

        api_arguments = {'token': args.api_key}
        if args.nocache:
            logging.debug('Disabling local caching')
            api_arguments['cache'] = None

        api = TodoistAPI(**api_arguments)
        sync(api)

        # Check if label argument is used
        if args.label is not None:
            # Check the next action label exists
            labels = api.labels.all(lambda x: x['name'] == args.label)
            if len(labels) > 0:
                label_id = labels[0]['id']
                logging.debug('Label \'%s\' found as label id %d',
                              args.label, label_id)
            else:
                # Create a new label in Todoist
                #TODO:
                logging.error(
                    "\n\nLabel \'%s\' doesn't exist in your Todoist. Please create it or use your custom label by running Autodoist with the argument '-l <YOUR_EXACT_LABEL>'.\n", args.label)
                sys.exit(1)
        else:
            # Label functionality not needed
            label_id = None

        logging.info("\nAutodoist has connected and is running fine!\n")

        return api, label_id

    def check_for_update(current_version):
        updateurl = 'https://api.github.com/repos/Hoffelhas/autodoist/releases'

        try:
            r = requests.get(updateurl)
            r.raise_for_status()
            release_info_json = r.json()

            if not current_version == release_info_json[0]['tag_name']:
                logging.warning("\n\nYour version is not up-to-date! \nYour version: {}. Latest version: {}\nSee latest version at: {}\n".format(
                    current_version, release_info_json[0]['tag_name'], release_info_json[0]['html_url']))
                return 1
            else:
                return 0
        except requests.exceptions.ConnectionError as e:
            logging.error(
                "Error while checking for updates (Connection error): {}".format(e))
            return 1
        except requests.exceptions.HTTPError as e:
            logging.error(
                "Error while checking for updates (HTTP error): {}".format(e))
            return 1
        except requests.exceptions.RequestException as e:
            logging.error("Error while checking for updates: {}".format(e))
            return 1

    def get_type(object, key):
        len_suffix = [len(args.p_suffix), len(args.s_suffix)]

        try:
            old_type = object[key]
        except Exception as e:
            # logging.debug('No defined project_type: %s' % str(e))
            old_type = None

        try:
            name = object['name'].strip()
        except:
            name = object['content'].strip()

        if name == 'Inbox':
            current_type = args.inbox
        elif name[-len_suffix[0]:] == args.p_suffix:
            current_type = 'parallel'
        elif name[-len_suffix[1]:] == args.s_suffix:
            current_type = 'sequential'
        else:
            current_type = None

        # Check if project type changed with respect to previous run
        if old_type == current_type:
            type_changed = 0
        else:
            type_changed = 1
            object[key] = current_type

        return current_type, type_changed

    def get_project_type(project_object):
        """Identifies how a project should be handled."""
        project_type, project_type_changed = get_type(
            project_object, 'project_type')

        return project_type, project_type_changed

    def get_item_type(item, project_type):
        """Identifies how a item with sub items should be handled."""

        if project_type is None and item['parent_id'] != 0:
            try:
                item_type = item['parent_type']
                item_type_changed = 1
                item['item_type'] = item_type
            except:
                item_type, item_type_changed = get_type(item, 'item_type')
        else:
            item_type, item_type_changed = get_type(item, 'item_type')

        return item_type, item_type_changed

    def add_label(item, label):
        if label not in item['labels']:
            labels = item['labels']
            logging.debug('Updating \'%s\' with label', item['content'])
            labels.append(label)

            try:
                overview_item_ids[str(item['id'])] += 1
            except:
                overview_item_ids[str(item['id'])] = 1
            overview_item_labels[str(item['id'])] = labels

    def remove_label(item, label):
        if label in item['labels']:
            labels = item['labels']
            logging.debug('Removing \'%s\' of its label', item['content'])
            labels.remove(label)

            try:
                overview_item_ids[str(item['id'])] -= 1
            except:
                overview_item_ids[str(item['id'])] = -1
            overview_item_labels[str(item['id'])] = labels

    def update_labels(label_id):
        filtered_overview_ids = [
            k for k, v in overview_item_ids.items() if v != 0]
        for item_id in filtered_overview_ids:
            labels = overview_item_labels[item_id]
            api.items.update(item_id, labels=labels)

    # Check for updates
    check_for_update(current_version)

    # Initialise api
    api, label_id = initialise(args)

    # Main loop
    while True:
        overview_item_ids = {}
        overview_item_labels = {}
        sync(api)

        for project in api.projects.all():

            if label_id is not None:
                # Get project type
                project_type, project_type_changed = get_project_type(project)
                logging.debug('Project \'%s\' being processed as %s',
                              project['name'], project_type)

            # Get all items for the project
            items = api.items.all(
                lambda x: x['project_id'] == project['id'])

            # Change top parents_id in order to sort later on
            for item in items:
                if not item['parent_id']:
                    item['parent_id'] = 0

            # Sort by parent_id and filter for completable items
            items = sorted(items, key=lambda x: (
                x['parent_id'], x['child_order']))
            items = list(
                filter(lambda x: not x['content'].startswith('*'), items))

            if label_id is not None:
                # If project type has been changed, clean everything for good measure
                if project_type_changed == 1:
                    # Remove labels
                    [remove_label(item, label_id) for item in items]
                    # Remove parent types
                    for item in items:
                        item['parent_type'] = None

                # To determine if a sequential task was found
                first_found_project = False
                first_found_item = True

            # For all items in this project
            for item in items:

                # Determine which child_items exist, both all and the ones that have not been checked yet
                non_checked_items = list(
                    filter(lambda x: x['checked'] == 0, items))
                child_items_all = list(
                    filter(lambda x: x['parent_id'] == item['id'], items))
                child_items = list(
                    filter(lambda x: x['parent_id'] == item['id'], non_checked_items))

                # Logic for recurring lists
                if not args.recurring:
                    try:
                        # If old label is present, reset it
                        if item['r_tag'] == 1:
                            item['r_tag'] = 0
                            api.items.update(item['id'])
                    except Exception as e:
                        pass

                # If options turned on, start recurring lists logic
                if args.recurring or args.end:
                    if item['parent_id'] == 0:
                        try:
                            if item['due']['is_recurring']:
                                try:
                                    # Check if the T0 task date has changed
                                    if item['due']['date'] != item['date_old']:

                                        if args.end is not None:
                                            # Determine current hour
                                            t = datetime.today()
                                            current_hour = t.hour

                                            # Check if current time is before our end-of-day
                                            if (args.end - current_hour) > 0:

                                                # Determine the difference in days set by todoist
                                                nd = [
                                                    int(x) for x in item['due']['date'].split('-')]
                                                od = [
                                                    int(x) for x in item['date_old'].split('-')]

                                                new_date = datetime(
                                                    nd[0], nd[1], nd[2])
                                                old_date = datetime(
                                                    od[0], od[1], od[2])
                                                today = datetime(
                                                    t.year, t.month, t.day)
                                                days_difference = (
                                                    new_date-today).days
                                                days_overdue = (
                                                    today - old_date).days

                                                # Only apply if overdue and if it's a daily recurring tasks
                                                if days_overdue >= 1 and days_difference == 1:

                                                    # Find curreny date in string format
                                                    today_str = [str(x) for x in [
                                                        today.year, today.month, today.day]]
                                                    if len(today_str[1]) == 1:
                                                        today_str[1] = ''.join(
                                                            ['0', today_str[1]])

                                                    # Update due-date to today
                                                    item_due = item['due']
                                                    item_due['date'] = '-'.join(
                                                        today_str)
                                                    item.update(due=item_due)
                                                    # item.update(due={'date': '2020-05-29', 'is_recurring': True, 'string': 'every day'})

                                        # Save the new date for reference us
                                        item.update(
                                            date_old=item['due']['date'])

                                        # Mark children for action
                                        if args.recurring is True:
                                            for child_item in child_items_all:
                                                child_item['r_tag'] = 1

                                except Exception as e:
                                    # If date has never been saved before, create a new entry
                                    logging.debug(
                                        'New recurring task detected: %s' % item['content'])
                                    item['date_old'] = item['due']['date']
                                    api.items.update(item['id'])

                        except Exception as e:
                            logging.debug(
                                'Parent not recurring: %s' % item['content'])
                            pass

                    if args.recurring is True and item['parent_id'] != 0:
                        try:
                            if item['r_tag'] == 1:
                                item.update(checked=0)
                                item.update(in_history=0)
                                item['r_tag'] = 0
                                api.items.update(item['id'])

                                for child_item in child_items_all:
                                    child_item['r_tag'] = 1
                        except Exception as e:
                            logging.debug('Child not recurring: %s' %
                                          item['content'])
                            pass

                # If options turned on, start labelling logic
                if label_id is not None:
                    # Skip processing an item if it has already been checked
                    if item['checked'] == 1:
                        continue

                    # Check item type
                    item_type, item_type_changed = get_item_type(
                        item, project_type)
                    logging.debug('Identified \'%s\' as %s type',
                                  item['content'], item_type)

                    # Check the item_type of the project or parent
                    if item_type is None:
                        if item['parent_id'] == 0:
                            item_type = project_type
                        else:
                            try:
                                if item['parent_type'] is None:
                                    item_type = project_type
                                else:
                                    item_type = item['parent_type']
                            except:
                                item_type = project_type
                    else:
                        # Reset in case that parentless task is tagged, overrules project
                        first_found_item = False

                    # If it is a parentless task
                    if item['parent_id'] == 0:
                        if project_type == 'sequential':
                            if not first_found_project:
                                add_label(item, label_id)
                                first_found_project = True
                            elif not first_found_item:
                                add_label(item, label_id)
                                first_found_item = True
                            # else:
                            #     remove_label(item, label_id)
                        elif project_type == 'parallel':
                            add_label(item, label_id)
                        else:
                            # If no project-type has been defined
                            if item_type:
                                add_label(item, label_id)

                    # If there are children
                    if len(child_items) > 0:
                        # Check if item state has changed, if so clean children for good measure
                        if item_type_changed == 1:
                            [remove_label(child_item, label_id)
                                for child_item in child_items]

                        # Process sequential tagged items (item_type can overrule project_type)
                        if item_type == 'sequential':
                            for child_item in child_items:
                                # Pass item_type down to the children
                                child_item['parent_type'] = item_type
                                # Pass label down to the first child
                                if child_item['checked'] == 0 and label_id in item['labels']:
                                    add_label(child_item, label_id)
                                    remove_label(item, label_id)
                                else:
                                    # Clean for good measure
                                    remove_label(child_item, label_id)

                        # Process parallel tagged items or untagged parents
                        elif item_type == 'parallel':
                            remove_label(item, label_id)
                            for child_item in child_items:
                                child_item['parent_type'] = item_type
                                if child_item['checked'] == 0:
                                    # child_first_found = True
                                    add_label(child_item, label_id)

                        # If item is too far in the future, remove the next_action tag and skip
                        if args.hide_future > 0 and 'due_date_utc' in item.data and item['due_date_utc'] is not None:
                            due_date = datetime.strptime(
                                item['due_date_utc'], '%a %d %b %Y %H:%M:%S +0000')
                            future_diff = (
                                due_date - datetime.utcnow()).total_seconds()
                            if future_diff >= (args.hide_future * 86400):
                                remove_label(item, label_id)
                                continue

        # Commit the queue with changes
        if label_id is not None:
            update_labels(label_id)

        if len(api.queue):
            len_api_q = len(api.queue)
            api.commit()
            if len_api_q == 1:
                logging.info(
                    '%d change committed to Todoist.', len_api_q)
            else:
                logging.info(
                    '%d changes committed to Todoist.', len_api_q)
        else:
            logging.info('No changes in queue, skipping sync.')

        # If onetime is set, exit after first execution.
        if args.onetime:
            break

        logging.debug('Sleeping for %d seconds', args.delay)
        time.sleep(args.delay)


if __name__ == '__main__':
    main()
