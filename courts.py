from bs4 import BeautifulSoup
import scraperwiki
import cookielib, urllib, urllib2
import sys

def getNames(html, name):
    for row in html.find(class_="nameList").find_all('tr'):
        cols = row.find_all('td')
        if len(cols) > 4:
            if name not in cols[1].string:
                return True
            print cols[1].string + ' Charge: ' + cols[2].string
    return False


def search(opener, name, court):
    data = urllib.urlencode({'category':'R',
        'lastName':name,
        'courtId':court,
        'submitValue':'N'})
    search = opener.open('http://ewsocis1.courts.state.va.us/CJISWeb/Search.do', data)
    done = getNames(BeautifulSoup(search.read()), name)

    data = urllib.urlencode({'courtId':court,
        'pagelink':'Next',
        'lastCaseProcessed':'',
        'firstCaseProcessed':'',
        'lastNameProcessed':'',
        'firstNameProcessed':'',
        'category':'R',
        'firstCaseSerialNumber':0,
        'lastCaseSerialNumber':0,
        'searchType':'',
        'emptyList':''})
    while(not done):
        search = opener.open('http://ewsocis1.courts.state.va.us/CJISWeb/Search.do', data)
        content = search.read()
        done = getNames(BeautifulSoup(content), name)

name = sys.argv[1]

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
opener.addheaders = [
    ('User-Agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.11) Gecko/20101012 Firefox/3.6.11'),
    ]
home = opener.open('http://ewsocis1.courts.state.va.us/CJISWeb/circuit.jsp')
html = BeautifulSoup(home.read())

for option in html.find_all('option'):
    system = option['value']
    courtId = system[:3]
    courtName = system[5:]
    
    print ''
    print courtName
    
    data = urllib.urlencode({'courtId':courtId,
        'courtType':'C',
        'caseType':'ALL',
        'testdos':False,
        'sessionCreate':'NEW',
        'whichsystem':system})
    place = opener.open('http://ewsocis1.courts.state.va.us/CJISWeb/MainMenu.do', data)
    search(opener, name, courtId)

print 'Done!'
