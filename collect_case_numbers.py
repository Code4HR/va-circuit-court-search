import cookielib
import os
import pymongo
import re
import sys
import threading
import time
import urllib
import urllib2
from bs4 import BeautifulSoup
from datetime import datetime
from pprint import pprint
from pymongo.errors import BulkWriteError
from time import sleep

user_agent = u"Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; " + \
    u"rv:1.9.2.11) Gecko/20101012 Firefox/3.6.11"
running = True

class caseNumberThread(threading.Thread):
    def __init__(self, court):
        threading.Thread.__init__(self)
        self.court = court
        self.courtName = court[5:].replace(' Circuit Court', '')
    def run(self):
        client = pymongo.MongoClient(os.environ['MONGO_URI'])
        db = client.va_circuit_court_cases
        opener = get_opener()
        get_list_of_courts(opener)
        last_record = db.case_numbers.find_one({'court': self.courtName}, \
                                sort=[('name', pymongo.DESCENDING)])
        last_name = 'A'
        if last_record is not None:
            last_name = last_record['name']
        if "FRANK'S" in last_name and 'Arlington' in self.courtName:
            last_name = "FRANK'T"
        print self.courtName, last_name
        get_case_numbers(opener, db, self.court, self.courtName, last_name)

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

def get_case_numbers(opener, db, court, courtName, name):
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
    final_case = get_cases(BeautifulSoup(html), courtName, db)

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

    final_case_prev = None
    while(final_case != final_case_prev and running):
        curHour = datetime.today().hour
        if curHour > 7 and curHour < 18:
            print 'Rate limit during working hours', datetime.today().time()
            time.sleep(15)
        else:
            time.sleep(1)
        print 'Request', courtName, datetime.today().time()
        search_results = opener.open(search_url, data)
        html = search_results.read()
        final_case_prev = final_case
        print 'Saving', courtName, datetime.today().time()
        final_case = get_cases(BeautifulSoup(html), courtName, db)
        print 'Saved', courtName, datetime.today().time()

def get_cases(html, court, db):
    final_case = None
    bulk = db.case_numbers.initialize_ordered_bulk_op()
    for row in html.find(class_="nameList").find_all('tr'):
        cols = row.find_all('td')
        if len(cols) > 4:
            case_number = cols[0].span.a.string.strip()
            name = cols[1].string.strip()
            charge = cols[2].string
            date = cols[3].string
            status = cols[4].string
            if charge is not None: charge = charge.strip()
            if date is not None: date = date.strip()
            if status is not None: status = status.strip()
            bulk.find({
                'court': court,
                'case_number': case_number
            }).upsert().replace_one({
                'court': court,
                'case_number': case_number,
                'name': name,
                'charge': charge,
                'date': date,
                'status': status
            })
            print case_number, name, court
            final_case = case_number
    try:
        bulk.execute()
    except BulkWriteError as bwe:
        pprint(bwe.details)
        raise bwe
    return final_case

try:
    opener = get_opener()
    courts = get_list_of_courts(opener)
    last_court_index = 0
    while last_court_index < len(courts):
        court_name = courts[last_court_index]['fullName']
        if threading.activeCount() < 4:
            caseNumberThread(court_name).start()
            last_court_index += 1
        time.sleep(3)

    while threading.activeCount() > 1:
        time.sleep(3)
    print 'Finished!'
except (KeyboardInterrupt, SystemExit):
    print 'Kill all threads'
    running = False

