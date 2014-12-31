from bs4 import BeautifulSoup
from datetime import datetime
import os
import pymongo
import re
from pprint import pprint

def get_data_from_table(case, table):
    table_cells = table.find_all('td')
    for cell in table_cells:
        strings = list(cell.stripped_strings)
        if len(strings) < 2:
            continue
        name = strings[0].encode('ascii', 'ignore') \
                         .replace(':', '').replace(' ', '')
        value = strings[1].encode('ascii', 'ignore')
        case[name] = value

def get_hearings_from_table(case, table):
    case['Hearings'] = []
    
    rows = table.find_all('tr')
    col_names = [x.encode('ascii') for x in rows.pop(0).stripped_strings]
    col_names[0] = 'Number'
    for row in rows:
        hearing = {}
        for i, col in enumerate(row.find_all('td')):
            val = col.get_text(strip=True) \
                     .encode('ascii', 'ignore')
            if val != '':
                hearing[col_names[i]] = val
        hearing_dt = hearing['Date'] + hearing['Time']
        hearing['Datetime'] = datetime.strptime(hearing_dt, "%m/%d/%Y%I:%M%p")
        case['Hearings'].append(hearing)

def value_to_datetime(case, name):
    case[name] = datetime.strptime(case[name], "%m/%d/%Y")

def process_case_details(case, html):
    tables = html.find_all('table')
    details_table = tables[4]
    hearings_table = tables[6]
    final_disposition_table = tables[8]
    sentencing_table = tables[9]
    appeal_table = tables[10]
    
    get_data_from_table(case, details_table)
    get_data_from_table(case, final_disposition_table)
    get_data_from_table(case, sentencing_table)
    get_hearings_from_table(case, hearings_table)
    
    # TODO: handle appeal table... not sure what that looks like
    
    if 'Filed' in case:
        value_to_datetime(case, 'Filed')
    if 'OffenseDate' in case:
        value_to_datetime(case, 'OffenseDate')
    if 'ArrestDate' in case: 
        value_to_datetime(case, 'ArrestDate')
    if 'DispositionDate' in case:
        value_to_datetime(case, 'DispositionDate')

def process_case_pleadings(case, html):
    tables = html.find_all('table')
    case_number_table = tables[3]
    pleadings_table = tables[4]
    
    case['CaseNumber'] = list(case_number_table.stripped_strings)[1] \
                                .encode('ascii', 'ignore')
    case['Pleadings'] = []
    rows = pleadings_table.find_all('tr')
    col_names = [x.encode('ascii') for x in rows.pop(0).stripped_strings]
    for row in rows:
        pleadings = {}
        for i, col in enumerate(row.find_all('td')):
            val = col.get_text(strip=True) \
                     .encode('ascii', 'ignore')
            if val != '':
                pleadings[col_names[i]] = val
        value_to_datetime(pleadings, 'Filed')
        case['Pleadings'].append(pleadings)

def process_case_services(case, html):
    tables = html.find_all('table')
    case_number_table = tables[3]
    services_table = tables[4]
    
    case['CaseNumber'] = list(case_number_table.stripped_strings)[1] \
                                .encode('ascii', 'ignore')
    case['Services'] = []
    rows = services_table.find_all('tr')
    col_names = [x.encode('ascii').replace(' ', '') \
                 for x in rows.pop(0).stripped_strings]
    for row in rows:
        services = {}
        for i, col in enumerate(row.find_all('td')):
            val = col.get_text(strip=True) \
                     .encode('ascii', 'ignore')
            if val != '':
                services[col_names[i]] = val
        if 'HearDate' in services:
            value_to_datetime(services, 'HearDate')
        if 'DateServed' in services:
            value_to_datetime(services, 'DateServed')
        case['Services'].append(services)

client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client.va_circuit_court

last_locality = sorted(db.criminal_cases.distinct('Court'))[-1]
last_case_number = db.criminal_cases.find_one({'Court': last_locality}, \
                    sort=[('CaseNumber', pymongo.DESCENDING)])['CaseNumber']

skip_directory = True
skip_case = True

base_path = '../va-circuit-court-search-files/'
locality_directories = os.walk(base_path).next()[1]
for directory in locality_directories:
    if last_locality == directory:
        skip_directory = False
    if skip_directory: continue
    
    filenames = os.listdir(base_path + directory)
    for filename in filenames:
        if last_case_number in filename:
            skip_case = False
        if skip_case: continue
        
        cur_path = base_path + directory + '/' + filename
        with open(cur_path, 'r') as f:
            print cur_path
            case = {'Court': directory}
            html = BeautifulSoup(f.read())
            
            if 'pleadings' in filename:
                process_case_pleadings(case, html)
            elif 'services' in filename:
                process_case_services(case, html)
            elif '.html' in filename:
                process_case_details(case, html)
            else:
                print 'Skipping unsupported file'
                continue
            
            db.criminal_cases.update({
                'Court': case['Court'],
                'CaseNumber': case['CaseNumber']
            }, {
                '$set': case
            }, upsert = True)
print 'Done'
