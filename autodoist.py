#!/usr/bin/python3

from todoist.api import TodoistAPI
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
    current_version = 'v1.3'

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
        '-pp', '--pp_suffix', help='Change suffix for parallel-parallel labeling (default "//").', default='//')
    parser.add_argument(
        '-ss', '--ss_suffix', help='Change suffix for sequential-sequential labeling (default "--").', default='--')
    parser.add_argument(
        '-ps', '--ps_suffix', help='Change suffix for parallel-sequential labeling (default "/-").', default='/-')
    parser.add_argument(
        '-sp', '--sp_suffix', help='Change suffix for sequential-parallel labeling (default "-/").', default='-/')
    parser.add_argument(
        '-df', '--dateformat', help='Strptime() format of starting date (default "%%d-%%m-%%Y").', default = '%d-%m-%Y')
    parser.add_argument(
        '-hf', '--hide_future', help='Prevent labelling of future tasks beyond a specified number of days.', default = 0, type=int)
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

    def query_yes_no(question, default="yes"):
        # """Ask a yes/no question via raw_input() and return their answer.

        # "question" is a string that is presented to the user.
        # "default" is the presumed answer if the user just hits <Enter>.
        #     It must be "yes" (the default), "no" or None (meaning
        #     an answer is required of the user).

        # The "answer" return value is True for "yes" or False for "no".
        # """
        valid = {"yes": True, "y": True, "ye": True,
                "no": False, "n": False}
        if default is None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            raise ValueError("invalid default answer: '%s'" % default)

        while True:
            sys.stdout.write(question + prompt)
            choice = input().lower()
            if default is not None and choice == '':
                return valid[default]
            elif choice in valid:
                return valid[choice]
            else:
                sys.stdout.write("Please respond with 'yes' or 'no' "
                                "(or 'y' or 'n').\n")

    def initialise(args):

        # Check we have a API key
        if not args.api_key:
            logging.error(
                "\n\nNo API key set. Run Autodoist with '-a <YOUR_API_KEY>'\n")
            sys.exit(1)

        # Check if alternative end of day is used
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

        logging.info("You are running with the following functionalities:\n\n   Next action labelling mode: {}\n   Regenerate sub-tasks mode: {}\n   Shifted end-of-day mode: {}\n".format(*modes))

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
                logging.info(
                    "\n\nLabel '{}' doesn't exist in your Todoist\n".format(args.label))
                # sys.exit(1)
                response = query_yes_no('Do you want to automatically create this label?')

                if response:
                    api.labels.add(args.label)
                    api.commit()
                    api.sync()
                    labels = api.labels.all(lambda x: x['name'] == args.label)
                    label_id = labels[0]['id']
                    logging.info('Label {} has been created!'.format(args.label))
                else:
                    logging.info('Exiting Autodoist.')
                    exit(1)

        else:
            # Label functionality not needed
            label_id = None

        logging.info("Autodoist has connected and is running fine!\n")

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

    def check_name(name):
        len_suffix = [len(args.pp_suffix), len(args.ss_suffix), len(args.ps_suffix), len(args.sp_suffix)]

        if name == 'Inbox':
            current_type = args.inbox
        elif name[-len_suffix[0]:] == args.pp_suffix:
            current_type = 'parallel'
        elif name[-len_suffix[1]:] == args.ss_suffix:
            current_type = 'sequential'
        elif name[-len_suffix[1]:] == args.ps_suffix:
            current_type = 'p-s'
        elif name[-len_suffix[1]:] == args.sp_suffix:
            current_type = 's-p'
        else:
            current_type = None

        return current_type

    def get_type(object, key):

        try:
            old_type = object[key]
        except:
            # logging.debug('No defined project_type: %s' % str(e))
            old_type = None

        try:
            object_name = object['name'].strip()
        except:
            object_name = object['content'].strip()
        
        current_type = check_name(object_name)

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

    def get_section_type(section_object):
        """Identifies how a section should be handled."""
        if section_object is not None:
            section_type, section_type_changed = get_type(
                section_object, 'section_type')
        else:
            section_type = None
            section_type_changed = 0

        return section_type, section_type_changed

    def get_item_type(item, project_type):
        """Identifies how an item with sub items should be handled."""

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

    def create_none_section(): # TODO: actually only needs to be created once?
        none_sec = {
            'id': None,
            'name': 'None',
            'section_order': 0
        }
        return none_sec

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

            if project['name'] == 'Test //':
                print('here')

            if label_id is not None:
                # Get project type
                project_type, project_type_changed = get_project_type(project)
                logging.debug('Project \'%s\' being processed as %s',
                              project['name'], project_type)
                
            # Get all items for the project
            # items = api.items.all(
            #     lambda x: x['project_id'] == project['id'])
            
            
            # section_ids = [x['id'] for x in sections]
            # section_ids.insert(0,None)

            # sections.append(create_none_section()) # Add a None-section to handle items in a project that have no section, append is faster than insert(0,ind)
            
            project_items = api.items.all(lambda x: x['project_id'] == project['id'])

            # Run for both none-sectioned and sectioned items
            for s in [0,1]:
                if s == 0:
                    sections = [create_none_section()]
                elif s == 1:
                    sections = api.sections.all(lambda x: x['project_id'] == project['id'])

                for section in sections:
                    
                    # Get section type
                    section_type, section_type_changed = get_section_type(
                        section)
                    logging.debug('Identified \'%s\' as %s type',
                        section['name'], section_type)
                    
                    # Get all items for the section
                    
                    items = [x for x in project_items if x['section_id'] == section['id']]
                    # items = api.items.all(lambda x: x['section_id'] == section['id'])
                    # sections = [x['section_id'] for x in items] # better than api.sections.all(lambda x: x['project_id'] == project['id']), since then NoneTypes are not shown
        
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
                        # If some type has been changed, clean everything for good measure
                        if project_type_changed == 1 or section_type_changed == 1:
                            # Remove labels
                            [remove_label(item, label_id) for item in items]
                            # Remove parent types
                            for item in items:
                                item['parent_type'] = None
        
                        # To determine if a sequential task was found
                        first_found_project = False
                        first_found_section = False
                        first_found_item = True
        
                    # For all items in this section
                    for item in items:
                        active_type = None # Reset

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
                            except:
                                pass
        
                        # If options turned on, start recurring lists logic
                        if args.recurring or args.end:
                            if item['parent_id'] == 0:
                                try:
                                    if item['due']['is_recurring']:
                                        try:
                                            # Check if the T0 task date has changed
                                            if item['due']['date'] != item['date_old']:
                                                
                                                # Save the new date for reference us
                                                item.update(
                                                    date_old=item['due']['date'])
                                                
                                                # Mark children for action
                                                if args.recurring:
                                                    for child_item in child_items_all:
                                                        child_item['r_tag'] = 1
                                                
                                                # If alternative end of day, fix due date if needed
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
        
                                        except:
                                            # If date has never been saved before, create a new entry
                                            logging.debug(
                                                'New recurring task detected: %s' % item['content'])
                                            item['date_old'] = item['due']['date']
                                            api.items.update(item['id'])
        
                                except:
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
                                except:
                                    logging.debug('Child not recurring: %s' %
                                                item['content'])
                                    pass
        
                        # If options turned on, start labelling logic
                        if label_id is not None:
                            # Skip processing an item if it has already been checked
                            if item['checked'] == 1:
                                #TODO: remove label if it has it?
                                continue
        
                            # Check item type
                            item_type, item_type_changed = get_item_type(
                                item, project_type)
                            logging.debug('Identified \'%s\' as %s type',
                                        item['content'], item_type)

                            

                            # If there is no item 
                            if item_type is not None:
                                # Reset in case that parentless task is tagged, overrules project
                                first_found_item = False

                            # Determine hierarchy types for logic
                            hierarchy_types = [item_type, section_type, project_type]
                            active_types = [type(x) != type(None) for x in hierarchy_types]
        
                            # If it is a parentless task
                            if item['parent_id'] == 0:
                                if active_types[0]:
                                    # Do item types
                                    active_type = item_type
                                    add_label(item, label_id)
                                    

                                elif active_types[1]:
                                    # Do section types
                                    active_type = section_type

                                    if section_type == 'sequential' or section_type == 's-p':
                                        if not first_found_section:
                                            add_label(item, label_id)
                                            first_found_section = True    
                                    elif section_type == 'parallel' or section_type == 'p-s':
                                        add_label(item, label_id)

                                elif active_types[2]:
                                    # Do project types
                                    active_type = project_type

                                    if project_type == 'sequential' or project_type == 's-p':
                                        if not first_found_project:
                                            add_label(item, label_id)
                                            first_found_project = True
                                        # elif not first_found_item and not project_type == 's-p':
                                        #     add_label(item, label_id)
                                        #     first_found_item = True
            
                                    elif project_type == 'parallel' or project_type == 'p-s':
                                        add_label(item, label_id)
                        
                            # If there are children
                            if len(child_items) > 0:
                                # Check if item state has changed, if so clean children for good measure
                                if item_type_changed == 1:
                                    [remove_label(child_item, label_id)
                                        for child_item in child_items]
                                       
                                # Process sequential tagged items (item_type can overrule project_type)
                                if active_type == 'sequential' or active_type == 'p-s':
                                    for child_item in child_items:
                                        # Pass item_type down to the children
                                        child_item['parent_type'] = active_type
                                        # Pass label down to the first child
                                        if child_item['checked'] == 0 and label_id in item['labels']:
                                            add_label(child_item, label_id)
                                            remove_label(item, label_id)
                                        else:
                                            # Clean for good measure
                                            remove_label(child_item, label_id)
        
                                # Process parallel tagged items or untagged parents
                                elif active_type == 'parallel' or (active_type == 's-p' and label_id in item['labels']):
                                    remove_label(item, label_id)
                                    for child_item in child_items:
                                        child_item['parent_type'] = active_type
                                        if child_item['checked'] == 0:
                                            # child_first_found = True
                                            add_label(child_item, label_id)
        
                            # If item is too far in the future, remove the next_action tag and skip
                            try:
                                if args.hide_future > 0 and 'due' in item.data and item['due'] is not None:
                                    due_date = datetime.strptime(item['due']['date'], "%Y-%m-%d")
                                    future_diff = (due_date - datetime.today()).days
                                    if future_diff >= args.hide_future:
                                        remove_label(item, label_id)
                                        continue
                            except:
                                # Hide-future not set, skip
                                continue
                            
                            # If start-date has not passed yet, remove label
                            try:
                                f = item['content'].find('start=')
                                if f > -1:
                                    f_end = item['content'][f+6:].find(' ')
                                    if f_end > -1:
                                        start_date = item['content'][f+6:f+6+f_end]
                                    else:
                                        start_date = item['content'][f+6:]
                                    start_date = datetime.strptime(start_date , args.dateformat)
                                    future_diff = (datetime.today()-start_date).days
                                    if future_diff < 0:
                                        remove_label(item, label_id)
                                        continue
        
                            except Exception as e:
                                logging.exception(
                                    'Error start-date: %s' % str(e))
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
