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

def getFilePath(court_name):
    court_name = court_name.replace(' ', '').replace('/', '')
    return 'files/' + court_name + '/'

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
        print court['name']
        file_path = getFilePath(court['name'])
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        elif len(courts) > index + 1:
            next_file_path = getFilePath(courts[index+1]['name'])
            if os.path.exists(next_file_path):
                continue
        
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
        if len(file_list) > 0:
            case_count = int(file_list[-1][4:10]) - 1
        
        search_next_case = True
        while search_next_case:
            case_count += 1
            case_number = 'CR14' + format(case_count, '06')
            
            search_next_specific_case = True
            specific_case_count = -1
            while search_next_specific_case:
                specific_case_count += 1
                specific_case_number = case_number + '-' + format(specific_case_count, '02')
                
                # get case info
                data = urllib.urlencode({
                    'categorySelected': 'R',
                    'caseNo': specific_case_number,
                    'courtId': court['id'],
                    'submitValue': ''})
                cases_url = u"http://ewsocis1.courts.state.va.us/CJISWeb/CaseDetail.do"
                case_details = opener.open(cases_url, data)
                case_details_str = case_details.read()
                if case_details_str == '':
                    raise Exception('Read case details failed')
                html = BeautifulSoup(case_details_str)
                case_exists = html.find(text=re.compile('Case not found')) is None
                
                if case_exists:
                    print 'Found ' + specific_case_number
                    sequential_cases_missed_count = 0
                    
                    filename = file_path + specific_case_number + '.html'
                    with open(filename, 'w') as text_file:
                        text_file.write(html.prettify().encode('UTF-8'))
                    
                    data = urllib.urlencode({
                        'categorySelected': 'R',
                        'caseStatus':'A',
                        'caseNo': specific_case_number,
                        'courtId': court['id'],
                        'submitValue': 'P'})
                    case_details = opener.open(cases_url, data)
                    case_details_str = case_details.read()
                    if case_details_str == '':
                        raise Exception('Read case details failed')
                    html = BeautifulSoup(case_details_str)
                    filename = file_path + specific_case_number + '_pleadings.html'
                    with open(filename, 'w') as text_file:
                        text_file.write(html.prettify().encode('UTF-8'))
                    
                    data = urllib.urlencode({
                        'categorySelected': 'R',
                        'caseStatus':'A',
                        'caseNo': specific_case_number,
                        'courtId': court['id'],
                        'submitValue': 'S'})
                    case_details = opener.open(cases_url, data)
                    case_details_str = case_details.read()
                    if case_details_str == '':
                        raise Exception('Read case details failed')
                    html = BeautifulSoup(case_details_str)
                    filename = file_path + specific_case_number + '_services.html'
                    with open(filename, 'w') as text_file:
                        text_file.write(html.prettify().encode('UTF-8'))
                    
                    data = urllib.urlencode({'courtId': court['id']})
                    opener.open(place_url, data)
                    sleep(1)
                else:
                    print 'Could not find ' + specific_case_number
                    if specific_case_count > 0:
                        search_next_specific_case = False
                    if specific_case_count == 1:
                        sequential_cases_missed_count += 1
                        if sequential_cases_missed_count > 9:
                            search_next_case = False

while True:
    try:
        run()
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        print "Unexpected error:", sys.exc_info()[0]
