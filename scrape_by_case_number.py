import cookielib
import os
import re
import sys
import urllib
import urllib2
from bs4 import BeautifulSoup
from time import sleep

user_agent = u"Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; " + \
    u"rv:1.9.2.11) Gecko/20101012 Firefox/3.6.11"

courts_with_fm_case_number = [
    'Charlotte Circuit Court',
    'Chesterfield Circuit Court',
    'Page Circuit Court',
    'Richmond City Circuit Court',
    'Wise Circuit Court'
]

def get_case_number_with_mf(case_number):
    return [
        case_number[:4] + 'M' + case_number[5:],
        case_number[:4] + 'F' + case_number[5:]
    ]

def get_case_number(court, case_count, charge_count):
    case_number = 'CR14' + format(case_count, '06') + \
        '-' + format(charge_count, '02')
    if court in courts_with_fm_case_number:
        return get_case_number_with_mf(case_number)
    return [case_number]

def getFilePath(court_name):
    court_name = court_name.replace(' ', '').replace('/', '')
    return '../va-circuit-court-search-files/' + court_name + '/'

def run():
    # Get cookie and list of courts
    cookieJar = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
    opener.addheaders = [('User-Agent', user_agent)]
    
    home = opener.open('http://ewsocis1.courts.state.va.us/CJISWeb/circuit.jsp')
    
    courts = []
    html = BeautifulSoup(home.read())
    for option in html.find_all('option'):
        courts.append({
            'fullName': option['value'],
            'id': option['value'][:3],
            'name': option['value'][5:]
        })
    
    # Go to court
    for index, court in enumerate(courts):
        #if 'Giles' not in court['name']: continue
        print court['name']
        file_path = getFilePath(court['name'])
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        #elif len(courts) > index + 1:
        #    next_file_path = getFilePath(courts[index+1]['name'])
        #    if os.path.exists(next_file_path):
        #        continue
        
        data = urllib.urlencode({
            'courtId': court['id'],
            'courtType': 'C',
            'caseType': 'ALL',
            'testdos': False,
            'sessionCreate': 'NEW',
            'whichsystem': court['fullName']})
        place_url = u"http://ewsocis1.courts.state.va.us/CJISWeb/MainMenu.do"
        opener.open(place_url, data)
        
        # search by case numbers
        sequential_cases_missed_count = 0
        case_count = -1
        file_list = os.listdir(file_path)
        for file_name in file_list:
            if '.html' not in file_name: continue
            cur_count = int(file_name[5:10])
            if cur_count > case_count:
                case_count = cur_count - 1
        
        search_next_case = True
        while search_next_case:
            case_count += 1
            search_next_charge = True
            charge_count = -1
            while search_next_charge:
                charge_count += 1
                if charge_count > 99:
                    break
                case_numbers = get_case_number(court['name'], case_count, charge_count)
                
                for case_number in case_numbers:
                    # get case info
                    data = urllib.urlencode({
                        'categorySelected': 'R',
                        'caseNo': case_number,
                        'courtId': court['id'],
                        'submitValue': ''})
                    cases_url = u"http://ewsocis1.courts.state.va.us/CJISWeb/CaseDetail.do"
                    case_details = opener.open(cases_url, data)
                    html = BeautifulSoup(case_details.read())
                
                    case_exists = html.find(text=re.compile('Case not found')) is None
                    if case_exists:
                        break
                    else:
                        print 'Could not find ' + case_number
                
                if case_exists:
                    html_is_invalid = html.find(text=re.compile(case_number)) is None
                    if html_is_invalid:
                        raise Exception('Case detail HTML is invalid')
                    
                    print 'Found ' + case_number
                    sequential_cases_missed_count = 0
                    
                    filename = file_path + case_number + '.html'
                    with open(filename, 'w') as text_file:
                        text_file.write(html.prettify().encode('UTF-8'))
                    
                    data = urllib.urlencode({
                        'categorySelected': 'R',
                        'caseStatus':'A',
                        'caseNo': case_number,
                        'courtId': court['id'],
                        'submitValue': 'P'})
                    case_details = opener.open(cases_url, data)
                    html = BeautifulSoup(case_details.read())
                    html_is_invalid = html.find(text=re.compile(case_number)) is None
                    if html_is_invalid:
                        raise Exception('Case detail pleadings HTML is invalid')
                    filename = file_path + case_number + '_pleadings.html'
                    with open(filename, 'w') as text_file:
                        text_file.write(html.prettify().encode('UTF-8'))
                    
                    data = urllib.urlencode({
                        'categorySelected': 'R',
                        'caseStatus':'A',
                        'caseNo': case_number,
                        'courtId': court['id'],
                        'submitValue': 'S'})
                    case_details = opener.open(cases_url, data)
                    html = BeautifulSoup(case_details.read())
                    html_is_invalid = html.find(text=re.compile(case_number)) is None
                    if html_is_invalid:
                        raise Exception('Case detail services HTML is invalid')
                    filename = file_path + case_number + '_services.html'
                    with open(filename, 'w') as text_file:
                        text_file.write(html.prettify().encode('UTF-8'))
                    
                    data = urllib.urlencode({'courtId': court['id']})
                    opener.open(place_url, data)
                    sleep(1)
                else:
                    print 'Could not find ' + case_number
                    if charge_count > 0:
                        search_next_charge = False
                    if charge_count == 1:
                        sequential_cases_missed_count += 1
                        if sequential_cases_missed_count > 9:
                            search_next_case = False

while True:
    try:
        run()
        break
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        print "Unexpected error:", sys.exc_info()
        print 'Restarting in 30 seconds'
        sleep(30)
print 'Done!'
