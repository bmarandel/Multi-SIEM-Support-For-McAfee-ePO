#!/usr/local/bin/python3

import json
import requests
from datetime import datetime
from mcafee_epo import Client, APIError

# Define appropriate values based on your environment
epo_server = "https://192.168.100.20:8443"
epo_user = "query"
epo_pwd = "mcafee"

# We tell python to ignore Self-Signed Certificates from ePO
epo_session = requests.Session()
epo_session.verify = False
requests.urllib3.disable_warnings(requests.urllib3.exceptions.InsecureRequestWarning)

try:
    print('Connecting to ePO... ')
    client = Client(epo_server, epo_user, epo_pwd, epo_session)
    
    # Ask ePO for available Queries based on our ePO Acount and Permission Set
    queries = client('core.listQueries')
    print('Found {} queries available.'.format(len(queries)))

    # Search for the QueryID we want to use
    group_filter = "Threat Events"
    query_filter = "Threat Events generated within the last full hour"
    print('Searching for query: {} ...'.format(query_filter))
    # Browse the queries and keep only entry matching the filters
    search_id = [q['id'] for q in queries if q['groupName']==group_filter and q['name']==query_filter]
    
    # Do we found a query Id?
    if (len(search_id) == 1):
        # Found a query Id, using it to request events
        print('Getting events from query ({})...'.format(search_id[0]))
        threat_events = client('core.executeQuery', search_id[0])
        nb_events = len(threat_events)
        print('Got {} event(s).'.format(nb_events))
        
        # Do we got events from ePO?
        if (nb_events > 0):
            # Yes, we got events, try to save them in a file
            now = datetime.utcnow().strftime('%Y-%m-%d-%H%M%S')
            filename = 'events_' + now + '.json'
            try:
                file = open(filename, 'w')
            except OSError:
                print('Cannot open the file {}!'.format(filename))
                print('No event(s) saved!')
            else:
                file.write(json.dumps(threat_events))
                file.close()
                print('{} event(s) saved in {}.'.format(nb_events, filename))
    else:
        # Zero or more than one query Id was found
        # User need access to Threat Event Logs permission
        print('No Threat Events query found, verify your Permission Set.')

except APIError:
        # User need access to Queries and Reports permission
        print('Authorization failed, please verify your Permission Set!')

except requests.exceptions.HTTPError:
    # An error occured while trying to connect to ePO
    print('Failed, please verify your credentials!')
