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

def get_case_numbers(opener, court, name):
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
    
    cases = []
    data = urllib.urlencode({
        'category': 'R',
        'lastName': name,
        'courtId': courtId,
        'submitValue': 'N'})
    search_url = u"http://ewsocis1.courts.state.va.us/CJISWeb/Search.do"
    search_results = opener.open(search_url, data)
    html = search_results.read()
    done = get_cases(BeautifulSoup(html), cases)

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

    count = 1
    while(not done and count < 10):
        search_results = opener.open(search_url, data)
        html = search_results.read()
        done = get_cases(BeautifulSoup(html), cases)
        count += 1
    return cases

def get_cases(html, names):
    for row in html.find(class_="nameList").find_all('tr'):
        cols = row.find_all('td')
        if len(cols) > 1:
            case_number = cols[0].span.a.string.strip()
            name = cols[1].string.strip()
            names.append({
                'case_number': case_number,
                'name': name
            })
            print case_number, name
    return False

opener = get_opener()
courts = get_list_of_courts(opener)
get_case_numbers(opener, courts[0]['fullName'], 'A')
