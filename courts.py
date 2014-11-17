import scraperwiki
import cookielib, urllib, urllib2
import json
from bs4 import BeautifulSoup
from flask import Flask, Response
app = Flask(__name__)

def getNames(html, name, names):
    for row in html.find(class_="nameList").find_all('tr'):
        cols = row.find_all('td')
        if len(cols) > 4:
            if name not in cols[1].string:
                return True
            names.append({'name': cols[1].string.strip(), 'charge': cols[2].string.strip()})
    return False


def search(opener, name, court):    
    names = []
    
    data = urllib.urlencode({'category':'R',
        'lastName':name,
        'courtId':court,
        'submitValue':'N'})
    search = opener.open('http://ewsocis1.courts.state.va.us/CJISWeb/Search.do', data)
    done = getNames(BeautifulSoup(search.read()), name, names)

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
        done = getNames(BeautifulSoup(content), name, names)
    return names

def start(name):
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
        
        response = {'court': courtName}
        
        data = urllib.urlencode({'courtId':courtId,
            'courtType':'C',
            'caseType':'ALL',
            'testdos':False,
            'sessionCreate':'NEW',
            'whichsystem':system})
        place = opener.open('http://ewsocis1.courts.state.va.us/CJISWeb/MainMenu.do', data)
        names = search(opener, name, courtId)
        response['names'] = names
        yield json.dumps(response)

@app.route("/")
def hello():
    return "Hello World!"

@app.route('/search/<name>')
def search_name(name):
    return Response(start(name.upper()), mimetype='application/json')

if __name__ == "__main__":
    app.debug = True
    app.run()
