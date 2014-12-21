import cookielib
import urllib
import urllib2
import os
import pickle
import pymongo
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from flask import Flask, session, render_template

app = Flask(__name__)

user_agent = u"Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; " + \
    u"rv:1.9.2.11) Gecko/20101012 Firefox/3.6.11"


def getCases(html, name, names):
    for row in html.find(class_="nameList").find_all('tr'):
        cols = row.find_all('td')
        if len(cols) > 4:
            if name not in cols[1].string:
                return True
            names.append({
                'caseNumber': cols[0].span.a.string.strip(),
                'name': cols[1].string.strip(),
                'charge': cols[2].string.strip(),
                'date': cols[3].string.strip(),
                'status': cols[4].string.strip()
            })
        elif len(cols) > 3:
            if name not in cols[1].get_text() and name not in \
                    cols[2].get_text():
                return True
            names.append({
                'caseNumber': cols[0].span.a.string.strip(),
                'name': cols[1].get_text(),
                'otherName': cols[2].get_text(),
                'status': cols[3].string.strip()
            })
    return False


def lookupCases(opener, name, court, division):
    cases = []

    data = urllib.urlencode({
        'category': division,
        'lastName': name,
        'courtId': court,
        'submitValue': 'N'})
    cases_url = u"http://ewsocis1.courts.state.va.us/CJISWeb/Search.do"
    searchResults = opener.open(cases_url, data)
    html = searchResults.read()
    done = getCases(BeautifulSoup(html), name, cases)

    data = urllib.urlencode({
        'courtId': court,
        'pagelink': 'Next',
        'lastCaseProcessed': '',
        'firstCaseProcessed': '',
        'lastNameProcessed': '',
        'firstNameProcessed': '',
        'category': division,
        'firstCaseSerialNumber': 0,
        'lastCaseSerialNumber': 0,
        'searchType': '',
        'emptyList': ''})

    count = 1
    search_url = u"http://ewsocis1.courts.state.va.us/CJISWeb/Search.do"
    while(not done and count < 6):
        search_results = opener.open(search_url, data)
        html = search_results.read()
        done = getCases(BeautifulSoup(html), name, cases)
        count += 1
    return cases


def getCasesInVirginiaBeach(html, name, names):
    resultsTable = html.find(class_="tablesorter")
    if resultsTable is None:
        return True

    for row in resultsTable.find('tbody').find_all('tr'):
        cols = row.find_all('td')
        if len(cols) > 5:
            names.append({
                'caseNumber': cols[0].a.string or '',
                'link': 'https://vbcircuitcourt.com' + cols[0].a['href'],
                'otherName': cols[1].string or '',
                'caseStyle': ''.join(cols[2].findAll(text=True))
                .replace('\r\n', ' ') or '',
                'name': ''.join(cols[3].findAll(text=True))
                .replace('\r\n', ' ') or '',
                'partyType': cols[4].string.capitalize() + ':',
                'status': cols[5].string or ''
            })
    return False


def lookupCasesInVirginiaBeach(name, division):
    cases = []

    url = u'https://vbcircuitcourt.com/public/search.do?searchType=1' + \
        u'&indexName=publiccasesearch&q=' + name.replace(' ', '+') + \
        u'%20FilterByCourtType:"' + division + u'"'

    searchResults = urllib2.urlopen(url)
    html = searchResults.read()
    done = getCasesInVirginiaBeach(BeautifulSoup(html), name, cases)

    count = 1
    while(not done and count < 6):
        searchResults = urllib2.urlopen(url + '&start=' + str(count * 30))
        html = searchResults.read()
        done = getCasesInVirginiaBeach(BeautifulSoup(html), name, cases)
        count += 1
    return cases


@app.route("/search/<name>/court/<path:court>")
def searchCourt(name, court):
    if 'cookies' not in session:
        return "Error. Please reload the page."
    
    courtId = court[:3]
    courtSearch = {'name': court[5:], 'id': courtId}
    
    db = pymongo.Connection(os.environ['MONGO_URI'])['va-circuit-court-search']
    cases = db['cases'].find_one({'name': name, 'court': court})
    if cases is not None:
        print 'Found cached search'
        courtSearch['criminalCases'] = cases['criminalCases']
        courtSearch['civilCases'] = cases['civilCases']
    elif 'Virginia Beach' in court:
        courtSearch['criminalCases'] = lookupCasesInVirginiaBeach(name, 
                                                                  'CRIMINAL')
        courtSearch['civilCases'] = lookupCasesInVirginiaBeach(name, 'CIVIL')
    else:
        cookieJar = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
        opener.addheaders = [('User-Agent', user_agent)]
        
        for cookie in pickle.loads(session['cookies']):
            cookieJar.set_cookie(cookie)
        
        data = urllib.urlencode({
            'courtId': courtId,
            'courtType': 'C',
            'caseType': 'ALL',
            'testdos': False,
            'sessionCreate': 'NEW',
            'whichsystem': court})
        place_url = u"http://ewsocis1.courts.state.va.us/CJISWeb/MainMenu.do"
        opener.open(place_url, data)
        
        courtSearch['criminalCases'] = lookupCases(opener, name.upper(),
                                                   courtId, 'R')
        courtSearch['civilCases'] = lookupCases(opener, name.upper(),
                                                courtId, 'CIVIL')
    
    if cases is None:
        print 'Caching search'
        db['cases'].insert({
            'name': name,
            'court': court,
            'criminalCases': courtSearch['criminalCases'],
            'civilCases': courtSearch['civilCases'],
            'dateSaved': datetime.utcnow()
        })
    return render_template('court.html', court=courtSearch)


@app.route("/search/<name>")
def search(name):
    db = pymongo.Connection(os.environ['MONGO_URI'])['va-circuit-court-search']
    db['cases'].remove({
        'dateSaved': {'$lt': datetime.utcnow() + timedelta(days=-60)}
    })
    
    cookieJar = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
    opener.addheaders = [('User-Agent', user_agent)]

    home = opener.open('http://ewsocis1.courts.state.va.us/CJISWeb/circuit.jsp')

    session['cookies'] = pickle.dumps(list(cookieJar))

    courts = []
    html = BeautifulSoup(home.read())
    for option in html.find_all('option'):
        courts.append({
            'fullName': option['value'],
            'id': option['value'][:3],
            'name': option['value'][5:]
        })
    data = {'name': name.upper(), 'courts': courts}
    cases = db['cases'].find({'name': name.upper()})
    for case in cases:
        for court in data['courts']:
            if case['court'] == court['fullName']:
                court['criminalCases'] = case['criminalCases']
                court['civilCases'] = case['civilCases']
    return render_template('search.html', data=data)


@app.route("/")
def index():
    return render_template('index.html')

if __name__ == "__main__":
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.secret_key = 'doesnt-need-to-be-secret'
    app.run(host='0.0.0.0', port=port, debug=True)
