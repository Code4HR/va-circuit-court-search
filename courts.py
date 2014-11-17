import scraperwiki
import cookielib, urllib, urllib2
import json
from bs4 import BeautifulSoup
from flask import Flask, Response, render_template
app = Flask(__name__)

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
    return False


def search(opener, name, court):    
    cases = []
    
    data = urllib.urlencode({'category':'R',
        'lastName':name,
        'courtId':court,
        'submitValue':'N'})
    search = opener.open('http://ewsocis1.courts.state.va.us/CJISWeb/Search.do', data)
    done = getCases(BeautifulSoup(search.read()), name, cases)

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
        done = getCases(BeautifulSoup(content), name, cases)
    return cases

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
        cases = search(opener, name, courtId)
        response['cases'] = cases
        yield response

@app.route("/")
def index():
    return render_template('index.html')

def stream_template(template_name, **context):
    # http://flask.pocoo.org/docs/patterns/streaming/#streaming-from-templates
    app.update_template_context(context)
    t = app.jinja_env.get_template(template_name)
    rv = t.stream(context)
    # uncomment if you don't need immediate reaction
    ##rv.enable_buffering(5)
    return rv

@app.route('/search/<name>')
def search_name(name):
    return Response(stream_template('search.html', data={'name': name.upper(), 'courts': start(name.upper())}))

if __name__ == "__main__":
    app.debug = True
    app.run()
