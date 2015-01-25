import cookielib
import os
import pymongo
import re
import sys
import urllib
import urllib2
from bs4 import BeautifulSoup
from time import sleep

user_agent = u"Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; " + \
    u"rv:1.9.2.11) Gecko/20101012 Firefox/3.6.11"

def get_opener():
    # Get cookie and list of courts
    cookieJar = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
    opener.addheaders = [('User-Agent', user_agent)]
    return opener

def get_list_of_courts(opener):
    home = opener.open('http://ewsocis1.courts.state.va.us/CJISWeb/circuit.jsp')
    courts = []
    html = BeautifulSoup(home.read())
    for option in html.find_all('option'):
        courts.append({
            'fullName': option['value'],
            'id': option['value'][:3],
            'name': option['value'][5:]
        })
    return courts

def get_case_numbers(opener, db, court, name):
    courtId = court[:3]
    data = urllib.urlencode({
        'courtId': courtId,
        'courtType': 'C',
        'caseType': 'ALL',
        'testdos': False,
        'sessionCreate': 'NEW',
        'whichsystem': court})
    place_url = u"http://ewsocis1.courts.state.va.us/CJISWeb/MainMenu.do"
    opener.open(place_url, data)
    
    data = urllib.urlencode({
        'category': 'R',
        'lastName': name,
        'courtId': courtId,
        'submitValue': 'N'})
    search_url = u"http://ewsocis1.courts.state.va.us/CJISWeb/Search.do"
    search_results = opener.open(search_url, data)
    html = search_results.read()
    final_case = get_cases(BeautifulSoup(html), court, db)

    data = urllib.urlencode({
        'courtId': courtId,
        'pagelink': 'Next',
        'lastCaseProcessed': '',
        'firstCaseProcessed': '',
        'lastNameProcessed': '',
        'firstNameProcessed': '',
        'category': 'R',
        'firstCaseSerialNumber': 0,
        'lastCaseSerialNumber': 0,
        'searchType': '',
        'emptyList': ''})

    #count = 1
    final_case_prev = None
    while(final_case != final_case_prev):
        search_results = opener.open(search_url, data)
        html = search_results.read()
        final_case_prev = final_case
        final_case = get_cases(BeautifulSoup(html), court, db)
        #count += 1

def get_cases(html, court, db):
    final_case = None
    for row in html.find(class_="nameList").find_all('tr'):
        cols = row.find_all('td')
        if len(cols) > 1:
            case_number = cols[0].span.a.string.strip()
            name = cols[1].string.strip()
            db.case_numbers.update({
                'court': court,
                'case_number': case_number
            }, {
                '$set': {
                    'court': court,
                    'case_number': case_number,
                    'name': name,
                    'charge': cols[2].string.strip(),
                    'date': cols[3].string.strip(),
                    'status': cols[4].string.strip()
                }
            }, upsert = True)
            print case_number, name
            final_case = case_number
    return final_case

client = pymongo.MongoClient(os.environ['MONGO_URI'])
db = client.va_circuit_court_case_numbers
opener = get_opener()
courts = get_list_of_courts(opener)

for court in courts:
    last_record = db.case_numbers.find_one({'court': court['fullName']}, \
                        sort=[('name', pymongo.DESCENDING)])
    last_name = 'A'
    if last_record is not None:
        last_name = last_record['name']
    print court['fullName'], last_name
    get_case_numbers(opener, db, court['fullName'], last_name)
