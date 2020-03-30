#!/usr/bin/python3

import logging
import argparse

from todoist.api import TodoistAPI

import time
import sys
from datetime import datetime

def main():
    """Main process function."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--api_key', help='Todoist API Key')
    parser.add_argument('-l', '--label', help='The next action label to use', default='next_action')
    parser.add_argument('-d', '--delay', help='Specify the delay in seconds between syncs', default=10, type=int)
    parser.add_argument('--debug', help='Enable debugging', action='store_true')
    parser.add_argument('--inbox', help='The method the Inbox project should be processed',
                        default=None, choices=['parallel', 'serial'])
    parser.add_argument('--parallel_suffix', default='//')
    parser.add_argument('--serial_suffix', default='--')
    parser.add_argument('--hide_future', help='Hide future dated next actions until the specified number of days',
                        default=7, type=int)
    parser.add_argument('--onetime', help='Update Todoist once and exit', action='store_true')
    parser.add_argument('--nocache', help='Disables caching data to disk for quicker syncing', action='store_true')
    args = parser.parse_args()

    # Set debug
    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(level=log_level)

    args.api_key = "18fa3286dd8f7c4fefe8655f8732a235b4ed7fb0"

    # Check we have a API key
    if not args.api_key:
        logging.error('No API key set, exiting...')
        sys.exit(1)

    # Run the initial sync
    logging.debug('Connecting to the Todoist API')

    api_arguments = {'token': args.api_key}
    if args.nocache:
        logging.debug('Disabling local caching')
        api_arguments['cache'] = None

    api = TodoistAPI(**api_arguments)
    logging.debug('Syncing the current state from the API')
    api.sync()

    # Check the next action label exists
    labels = api.labels.all(lambda x: x['name'] == args.label)
    if len(labels) > 0:
        label_id = labels[0]['id']
        logging.debug('Label \'%s\' found as label id %d', args.label, label_id)
    else:
        logging.error("Label \'%s\' doesn't exist, please create it or change TODOIST_NEXT_ACTION_LABEL.", args.label)
        sys.exit(1)

    def get_type(object,key):
        len_suffix = [len(args.parallel_suffix), len(args.serial_suffix)]

        try:
            old_type = object[key]
        except Exception as e:
            logging.debug('No defined project_type: %s' % str(e))
            old_type = None   

        try:
            name = object['name'].strip()
        except:
            name = object['content'].strip()
        
        if name == 'Inbox':
            current_type = args.inbox
        elif name[-len_suffix[0]:] == args.parallel_suffix:
            current_type =  'parallel'
        elif name[-len_suffix[1]:] == args.serial_suffix:
            current_type = 'serial'
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
        project_type, project_type_changed = get_type(project_object,'project_type')

        return project_type, project_type_changed

    def get_item_type(item, project_type):
        """Identifies how a item with sub items should be handled."""
        
        if project_type is None and item['parent_id'] != 0:
            try:
                item_type = item['parent_type']
                item_type_changed = 1
            except:
                item_type, item_type_changed = get_type(item,'item_type') 
        else:
            item_type, item_type_changed = get_type(item,'item_type')

        return item_type, item_type_changed

    def add_label(item, label):
        if label not in item['labels']:
            labels = item['labels']
            logging.debug('Updating \'%s\' with label', item['content'])
            labels.append(label)
            api.items.update(item['id'], labels=labels)

    def remove_label(item, label):
        if label in item['labels']:
            labels = item['labels']
            logging.debug('Updating \'%s\' without label', item['content'])
            labels.remove(label)
            api.items.update(item['id'], labels=labels)

    # Main loop
    while True:
        try:
            api.sync()
        except Exception as e:
            logging.exception('Error trying to sync with Todoist API: %s' % str(e))
        else:
            for project in api.projects.all():

                print(project['name'])

                # Get project type
                project_type, project_type_changed = get_project_type(project)
                logging.debug('Project \'%s\' being processed as %s', project['name'], project_type)
                
                # Get all items for the project
                items = api.items.all(lambda x: x['project_id'] == project['id'])
                
                # Change top parents_id in order to sort later on
                for item in items:
                    if not item['parent_id']:
                        item['parent_id'] = 0

                # Sort by parent_id and filter for completable items
                items = sorted(items, key=lambda x: (x['parent_id'], x['child_order']))
                items = list(filter(lambda x: not x['content'].startswith('*'), items))

                # If project type has been changed, clean everything foor good measure
                if project_type_changed == 1:
                    [remove_label(item, label_id) for item in items]
                        
                first_found = False

                for item in items:
                    
                    # Skip processing an item if it has already been checked
                    if item['checked'] == 1:
                        continue

                    print(item['content'])

                    # Check item type
                    item_type, item_type_changed = get_item_type(item, project_type)                           
                    logging.debug('Identified \'%s\' as %s type', item['content'], item_type)
                    
                    # Check for child_items
                    child_items = list(filter(lambda x: x['parent_id'] == item['id'], items))

                    if project_type is None and item_type is None and project_type_changed == 1:
                        # Clean the item and its children
                        remove_label(item, label_id)
                        for child_item in child_items:
                            child_item['parent_type'] = None

                        # We can immediately continue
                        continue
                    else:
                        # Define item_type if not present
                        if item_type is None:
                            item_type = project_type
                        
                        # Add labels to top items
                        if item['parent_id'] == 0:
                            if project_type == 'serial':
                                if not first_found:
                                    add_label(item, label_id)
                                    first_found = True
                                else:
                                    remove_label(item, label_id)
                            elif project_type == 'parallel':
                                add_label(item, label_id)
                            else:
                                if item_type:
                                    add_label(item, label_id)
                    
                        # If there are children, label them instead
                        if len(child_items) > 0:
                            child_first_found = False

                            # Check if state has changed, if so clean for good measure
                            if item_type_changed == 1:
                                [remove_label(child_item, label_id) for child_item in child_items]

                            # Process serial tagged items
                            if item_type == 'serial':
                                for child_item in child_items:
                                    if child_item['checked'] == 0 and not child_first_found and label_id in item['labels']:
                                        child_first_found = True
                                        add_label(child_item, label_id)
                                        child_item['parent_type'] = item_type
                                    else:
                                        remove_label(child_item, label_id)
                            # Process parallel tagged items or untagged parents
                            elif item_type == 'parallel':
                                for child_item in child_items:
                                    if child_item['checked'] == 0:
                                        child_first_found = True
                                        add_label(child_item, label_id)
                                        child_item['parent_type'] = item_type

                            # Remove the label from the parent
                            if item_type and child_first_found:
                                remove_label(item, label_id)

                        # If item is too far in the future, remove the next_action tag and skip
                        if args.hide_future > 0 and 'due_date_utc' in item.data and item['due_date_utc'] is not None:
                            due_date = datetime.strptime(item['due_date_utc'], '%a %d %b %Y %H:%M:%S +0000')
                            future_diff = (due_date - datetime.utcnow()).total_seconds()
                            if future_diff >= (args.hide_future * 86400):
                                remove_label(item, label_id)
                                continue

            if len(api.queue):
                logging.debug('%d changes queued for sync... commiting to Todoist.', len(api.queue))
                api.commit()
            else:
                logging.debug('No changes queued, skipping sync.')

        # If onetime is set, exit after first execution.
        if args.onetime:
            break

        logging.debug('Sleeping for %d seconds', args.delay)
        time.sleep(args.delay)

if __name__ == '__main__':
    main()
