import scraperwiki
import cookielib, urllib, urllib2
import json
import os
import flask
import pickle
from bs4 import BeautifulSoup
from datetime import datetime
from flask import Flask, session, Response, render_template

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
        elif len(cols) > 3:
            if name not in cols[1].get_text() and name not in cols[2].get_text():
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
    
    data = urllib.urlencode({'category': division,
        'lastName':name,
        'courtId':court,
        'submitValue':'N'})
    searchResults = opener.open('http://ewsocis1.courts.state.va.us/CJISWeb/Search.do', data)
    html = searchResults.read()
    done = getCases(BeautifulSoup(html), name, cases)
    
    data = urllib.urlencode({'courtId':court,
        'pagelink':'Next',
        'lastCaseProcessed':'',
        'firstCaseProcessed':'',
        'lastNameProcessed':'',
        'firstNameProcessed':'',
        'category': division,
        'firstCaseSerialNumber':0,
        'lastCaseSerialNumber':0,
        'searchType':'',
        'emptyList':''})
    
    count = 1
    while(not done and count < 6):
        searchResults = opener.open('http://ewsocis1.courts.state.va.us/CJISWeb/Search.do', data)
        html = searchResults.read()
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
                'caseStyle': ''.join(cols[2].findAll(text=True)).replace('\r\n', ' ') or '',
                'name': ''.join(cols[3].findAll(text=True)).replace('\r\n', ' ') or '',
                'partyType': cols[4].string.capitalize() + ':',
                'status': cols[5].string or ''
            })
    return False
    
def lookupCasesInVirginiaBeach(name, division):    
    cases = []
    
    url = 'https://vbcircuitcourt.com/public/search.do?searchType=1&indexName=publiccasesearch&q=' + name.replace(' ', '+')
    url = url + '%20FilterByCourtType:"' + division + '"'
    
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
    
    cookieJar = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.11) Gecko/20101012 Firefox/3.6.11')]
    for cookie in pickle.loads(session['cookies']):
        cookieJar.set_cookie(cookie)
    
    courtId = court[:3]
    data = urllib.urlencode({'courtId':courtId,
        'courtType':'C',
        'caseType':'ALL',
        'testdos':False,
        'sessionCreate':'NEW',
        'whichsystem':court})
    place = opener.open('http://ewsocis1.courts.state.va.us/CJISWeb/MainMenu.do', data)
    
    courtSearch = {'name': court[5:], 'id': courtId}
    courtSearch['criminalCases'] = lookupCases(opener, name.upper(), courtId, 'R')
    courtSearch['civilCases'] = lookupCases(opener, name.upper(), courtId, 'CIVIL')
    
    if 'Virginia Beach' in court:
        courtSearch['criminalCases'].extend(lookupCasesInVirginiaBeach(name, 'CRIMINAL'))
        courtSearch['civilCases'].extend(lookupCasesInVirginiaBeach(name, 'CIVIL'))
    
    return render_template('court.html', court=courtSearch)
    
@app.route("/search/<name>")
def search(name):
    cookieJar = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.11) Gecko/20101012 Firefox/3.6.11')]
    #home = opener.open('http://ewsocis1.courts.state.va.us/CJISWeb/circuit.jsp')
    
    print 'Open Portal'
    opener.open('https://secure.alexandriava.gov/ajis/index.php')
    print cookieJar
    
    print 'Open Login Page'
    data = urllib.urlencode({
        'username':'WEBNOIMG',
        'password':'NOIMGWEB',
        'launchAJIS':'GO'
    })
    opener.open('http://ajis.alexandriava.gov/ajis/Common/login.cfm', data)
    
    print 'Open App'
    data = urllib.urlencode({
        'id_user':'WEBNOIMG',
        'frf_password':'NOIMGWEB',
        'Submit':'',
        'ValidSessionCount':0,
        'JustLoggedIn':'',
        'cde_log_user_ind':'Y',
        'autologin_ind':'Y',
        'username_hold':'WEBNOIMG',
        'password_hold':'NOIMGWEB',
        'FormUID':'RefreshUID4197017285370161119213',
        'id_user_Network':'',
        'ind_set_UserID':'',
        'frf_computer_name':'',
        'BrowserId':1,
        'cde_function_nv':'CF030',
        'cde_page_id_nv':'CF030A',
        'cde_script_id_nv':'',
        'cde_path_nv':'',
        'AppSource':'',
        'AppAction':'',
        'AppForm':'CF030a.cfm',
        'AppTarget':'',
        'SessionExpireWarningMsgTime':14220000,
        'ColorTHead':'',
        'ReturnTo_nv':'OFF',
        'cde_security_ins':'',
        'BrowseButton':'',
        'OriginatingFormValues':'',
        'VISITEDROWS':'',
        'applybr':0,
        'applypwed':0,
        'calculate':'',
        'putFunctionInQ':'N',
        'putKeysInLittleQ':'N',
        'putKeysInBigQ':'Y',
        'fetchKeys':'N',
        'cookiesDisabled':'false',
        'bigQInEffect':'false',
        'deletedRows_List':'',
        'FunctionListState':'',
        'prev_function':'',
        'scrollx':'',
        'lastusedfunc1':'',
        'lastusedfunc2':'',
        'lastusedfunc3':'',
        'lastusedfunc4':'',
        'lastusedfunc5':'',
        'lastusedfunc6':'',
        'FuncListContents':'',
        'IndicatorToLogoff':False,
        'OpenedByScript':False,
        'UserId':'',
        'LogonCount':'',
        'CheckFuncCall':'',
        'tms_bf':datetime.now().strftime('%m/%d/%Y %H:%M:%S'),
        'HTMLForFLMain':'',
        'RemoveKeysOnCancel':'N',
        'RemoveUserAreaOnCancel':'Y',
        'cde_appl_data_src':'AJISWEB',
        'ShowFuncList':'',
        'PrintPageContents':'',
        'FuncListRand':''
    })
    app = opener.open('http://ajis.alexandriava.gov/ajis/System/cf030_dcsn.cfm', data)
    
    data = urllib.urlencode({
        'AppAction': '',
        'AppForm': '',
        'AppSource': '',
        'AppTarget': 'CC600WEB',
        'BrowseButton': '',
        'BrowserId': '1',
        'CheckFuncCall': '',
        'ColorTHead': '',
        'DaysToExpire': '#DaysToExpire#',
        #'FuncListContents': '<body+style="height:100%;+width:100%"><table+cellpadding="0"+cellspacing="0"+style="width:450px"><tr><td+valign="top"+cellpadding="0"+cellspacing="0"><img+src="/images/scales.png"><a+href="#"+onClick="return+treeMenuClickRoot();"+style="color:black;+text-decoration:none">&nbsp;AJISWEB&nbsp;</a></td></tr><tr+valign=top><td+title=""><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="nonurl"+href="#"+onClick="return+treeMenuClick(0,+false,+true);;"><img+src="/images/menu_folder_open.gif"+align=left+border=0+vspace=0+hspace=0>Frequently+Used+Functions</a></td></tr><tr+valign=top><td+title="CF400WA(CF400WA)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_corner.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CF400WA\',\'\');"+onClick="return+treeMenuClick(1,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>AJIS+User+Instructions</a></td></tr><tr+valign=top><td+title=""><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="nonurl"+href="#"+onClick="return+treeMenuClick(2,+false,+true);;"><img+src="/images/menu_folder_open.gif"+align=left+border=0+vspace=0+hspace=0>Judgment+-+General+Access</a></td></tr><tr+valign=top><td+title="CC102WEB(CC102WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_corner.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC102WEB\',\'\');"+onClick="return+treeMenuClick(3,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Judgment+Search+&+List</a></td></tr><tr+valign=top><td+title=""><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="nonurl"+href="#"+onClick="return+treeMenuClick(4,+false,+true);;"><img+src="/images/menu_folder_open.gif"+align=left+border=0+vspace=0+hspace=0>Civil+-+General+Access</a></td></tr><tr+valign=top><td+title="CC240WEB(CC240WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC240WEB\',\'\');"+onClick="return+treeMenuClick(5,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Civil+Name+Search+&+List</a></td></tr><tr+valign=top><td+title="CC300WEB(CC300WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC300WEB\',\'\');"+onClick="return+treeMenuClick(6,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Civil+Case+Search+&+List</a></td></tr><tr+valign=top><td+title="CC012WEB(CC012WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC012WEB\',\'\');"+onClick="return+treeMenuClick(7,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Church+&+Organization+Trustees+Search+&+List</a></td></tr><tr+valign=top><td+title="CC034WEB(CC034WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC034WEB\',\'\');"+onClick="return+treeMenuClick(8,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Financing+Statement+Search+&+List</a></td></tr><tr+valign=top><td+title="CC042WEB(CC042WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC042WEB\',\'\');"+onClick="return+treeMenuClick(9,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Marriage+License+Search+&+List</a></td></tr><tr+valign=top><td+title="CC052WEB(CC052WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC052WEB\',\'\');"+onClick="return+treeMenuClick(10,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Name+Change+Search+&+List</a></td></tr><tr+valign=top><td+title="CC072WEB(CC072WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC072WEB\',\'\');"+onClick="return+treeMenuClick(11,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Trade+Name+and+Participant+Search+&+List</a></td></tr><tr+valign=top><td+title="CC093WEB(CC093WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC093WEB\',\'\');"+onClick="return+treeMenuClick(12,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Search+Warrant/Affidavit+Search+&+List</a></td></tr><tr+valign=top><td+title="CC083WEB(CC083WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_corner.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC083WEB\',\'\');"+onClick="return+treeMenuClick(13,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Special+Conservators+of+the+Peace+Search+&+List</a></td></tr><tr+valign=top><td+title=""><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="nonurl"+href="#"+onClick="return+treeMenuClick(14,+false,+true);;"><img+src="/images/menu_folder_open.gif"+align=left+border=0+vspace=0+hspace=0>Criminal+-+General+Access</a></td></tr><tr+valign=top><td+title="CC600WEB(CC600WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_corner.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC600WEB\',\'\');"+onClick="return+treeMenuClick(15,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Criminal+Case+Search+&+List</a></td></tr><tr+valign=top><td+title=""><img+src="/images/menu_corner.gif"+align=left+border=0+vspace=0+hspace=0><a+class="nonurl"+href="#"+onClick="return+treeMenuClick(16,+false,+true);;"><img+src="/images/menu_folder_closed.gif"+align=left+border=0+vspace=0+hspace=0>ReadMe+Documents</a></td></tr></table></body>',
        'FuncListRand': '0.344304221453',
        #'FunctionListState': 'AFRAMEMenu_WEBNOIMG=1%2C0%2C1%2C0%2C1%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C1%2C0%2C0%2C0;AFRAMEMenu_WEBNOIMG-selected=15;',
        'HTMLForFLMain': '',
        'IndicatorToLogoff': 'False',
        'LogonCount': '6',
        'OpenedByScript': 'False',
        'OriginatingFormValues': '',
        'PrintPageContents': '',
        'RemoveKeysOnCancel': 'N',
        'RemoveUserAreaOnCancel': 'Y',
        'ReturnTo_nv': 'OFF',
        'SessionExpireWarningMsgTime': '14220000',
        'ShowFuncList': 'N',
        'UserId': 'WEBNOIMG',
        'VISITEDROWS': '',
        'applybr': '0',
        'applypwed': '0',
        'bigQInEffect': 'false',
        'calculate': '',
        'cde_appl_data_src': 'AJISWEB',
        'cde_function_nv': '',
        'cde_page_id_nv': '',
        'cde_path_nv': '',
        'cde_script_id_nv': '',
        'cde_security_ins': '',
        'cookiesDisabled': 'false',
        'deletedRows_List': '',
        'fetchKeys': 'N',
        'frf_welcome_msg': 'Welcome+to+the+AJISWEB+System.\r\nPlease+select+a+task+from+the+function+list+to+get+started.\r\n',
        'lastusedfunc1': 'CC600WEB',
        'lastusedfunc2': '',
        'lastusedfunc3': '',
        'lastusedfunc4': '',
        'lastusedfunc5': '',
        'lastusedfunc6': '',
        'prev_function': '',
        'putFunctionInQ': 'Y',
        'putKeysInBigQ': 'Y',
        'putKeysInLittleQ': 'N',
        'scrollx': '',
        'tms_bf': '11/27/2014+11:02:03'
    })
    app = opener.open('http://ajis.alexandriava.gov/ajis/Navigation/nv_ok.cfm', data)
    
    print 'Do Search'
    data = urllib.urlencode({
        'AppAction': 'cc600a_actn.cfm',
        'AppForm': 'cc600a2.cfm',
        'AppSource': 'CC600a1.cfm',
        'AppTarget': '',
        'BrowseButton': '',
        'BrowserId': '1',
        'CheckFuncCall': '',
        'ColorTHead': '',
        'FieldForSubmit': '',
        'FuncListContents': '<body+style="height:100%;+width:100%"><table+cellpadding="0"+cellspacing="0"+style="width:450px"><tr><td+valign="top"+cellpadding="0"+cellspacing="0"><img+src="/images/scales.png"><a+href="#"+onClick="return+treeMenuClickRoot();"+style="color:black;+text-decoration:none">&nbsp;AJISWEB&nbsp;</a></td></tr><tr+valign=top><td+title=""><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="nonurl"+href="#"+onClick="return+treeMenuClick(0,+false,+true);;"><img+src="/images/menu_folder_open.gif"+align=left+border=0+vspace=0+hspace=0>Frequently+Used+Functions</a></td></tr><tr+valign=top><td+title="CF400WA(CF400WA)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_corner.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CF400WA\',\'\');"+onClick="return+treeMenuClick(1,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>AJIS+User+Instructions</a></td></tr><tr+valign=top><td+title=""><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="nonurl"+href="#"+onClick="return+treeMenuClick(2,+false,+true);;"><img+src="/images/menu_folder_open.gif"+align=left+border=0+vspace=0+hspace=0>Judgment+-+General+Access</a></td></tr><tr+valign=top><td+title="CC102WEB(CC102WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_corner.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC102WEB\',\'\');"+onClick="return+treeMenuClick(3,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Judgment+Search+&+List</a></td></tr><tr+valign=top><td+title=""><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="nonurl"+href="#"+onClick="return+treeMenuClick(4,+false,+true);;"><img+src="/images/menu_folder_open.gif"+align=left+border=0+vspace=0+hspace=0>Civil+-+General+Access</a></td></tr><tr+valign=top><td+title="CC240WEB(CC240WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC240WEB\',\'\');"+onClick="return+treeMenuClick(5,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Civil+Name+Search+&+List</a></td></tr><tr+valign=top><td+title="CC300WEB(CC300WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC300WEB\',\'\');"+onClick="return+treeMenuClick(6,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Civil+Case+Search+&+List</a></td></tr><tr+valign=top><td+title="CC012WEB(CC012WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC012WEB\',\'\');"+onClick="return+treeMenuClick(7,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Church+&+Organization+Trustees+Search+&+List</a></td></tr><tr+valign=top><td+title="CC034WEB(CC034WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC034WEB\',\'\');"+onClick="return+treeMenuClick(8,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Financing+Statement+Search+&+List</a></td></tr><tr+valign=top><td+title="CC042WEB(CC042WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC042WEB\',\'\');"+onClick="return+treeMenuClick(9,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Marriage+License+Search+&+List</a></td></tr><tr+valign=top><td+title="CC052WEB(CC052WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC052WEB\',\'\');"+onClick="return+treeMenuClick(10,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Name+Change+Search+&+List</a></td></tr><tr+valign=top><td+title="CC072WEB(CC072WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC072WEB\',\'\');"+onClick="return+treeMenuClick(11,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Trade+Name+and+Participant+Search+&+List</a></td></tr><tr+valign=top><td+title="CC093WEB(CC093WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC093WEB\',\'\');"+onClick="return+treeMenuClick(12,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Search+Warrant/Affidavit+Search+&+List</a></td></tr><tr+valign=top><td+title="CC083WEB(CC083WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_corner.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC083WEB\',\'\');"+onClick="return+treeMenuClick(13,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Special+Conservators+of+the+Peace+Search+&+List</a></td></tr><tr+valign=top><td+title=""><img+src="/images/menu_tee.gif"+align=left+border=0+vspace=0+hspace=0><a+class="nonurl"+href="#"+onClick="return+treeMenuClick(14,+false,+true);;"><img+src="/images/menu_folder_open.gif"+align=left+border=0+vspace=0+hspace=0>Criminal+-+General+Access</a></td></tr><tr+valign=top><td+title="CC600WEB(CC600WEB)"><img+src="/images/menu_bar.gif"+align=left+border=0+vspace=0+hspace=0><img+src="/images/menu_corner.gif"+align=left+border=0+vspace=0+hspace=0><a+class="url"+href="Javascript:parent.OSF(\'CC600WEB\',\'\');"+onClick="return+treeMenuClick(15,+true,+false);;"><img+src="/images/menu_pixel.gif"+align=left+border=0+vspace=0+hspace=0>Criminal+Case+Search+&+List</a></td></tr><tr+valign=top><td+title=""><img+src="/images/menu_corner.gif"+align=left+border=0+vspace=0+hspace=0><a+class="nonurl"+href="#"+onClick="return+treeMenuClick(16,+false,+true);;"><img+src="/images/menu_folder_closed.gif"+align=left+border=0+vspace=0+hspace=0>ReadMe+Documents</a></td></tr></table></body>',
        'FuncListRand': '0.344304221453',
        'FunctionListState': 'AFRAMEMenu_WEBNOIMG=1%2C0%2C1%2C0%2C1%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C1%2C0%2C0%2C0;AFRAMEMenu_WEBNOIMG-selected=15;',
        'HTMLForFLMain': '',
        'IndicatorToLogoff': 'False',
        'LastButtonClicked': 'OK',
        'LogonCount': '6',
        'OpenedByScript': 'False',
        'OriginatingFormValues': '',
        'PrintPageContents': '',
        'RemoveKeysOnCancel': 'N',
        'RemoveUserAreaOnCancel': 'Y',
        'ReturnTo': 'on',
        'ReturnTo_nv': 'ON',
        'SessionExpireWarningMsgTime': '14220000',
        'ShowFuncList': 'N',
        'UserId': 'WEBNOIMG',
        'VISITEDROWS': '',
        'applybr': '0',
        'applypwed': '0',
        'bigQInEffect': 'false',
        'calculate': '',
        'cde_PageId_List': 'CC600B',
        'cde_appl_data_src': 'AJISWEB',
        'cde_case_stat': '+',
        'cde_comparison_sy': 'ST',
        'cde_display_sy': '+',
        'cde_function_nv': 'CC600WEB',
        'cde_page_id_nv': 'CC600A',
        'cde_party_role': 'DEF',
        'cde_path_nv': '01',
        'cde_script_id_nv': 'CC600',
        'cde_search_type_sy': 'SP',
        'cde_security_ins': '',
        'cookiesDisabled': 'false',
        'deletedRows_List': '',
        'dte_case_init': '',
        'dte_case_init_thru': '',
        'dte_date': '',
        'fetchKeys': 'N',
        'frf_badge_num': '',
        'frf_docket': '',
        'frf_id_value': '',
        'frf_otn_state': '',
        'lastusedfunc1': 'CC600WEB',
        'lastusedfunc2': '',
        'lastusedfunc3': '',
        'lastusedfunc4': '',
        'lastusedfunc5': '',
        'lastusedfunc6': '',
        'nme_ff_upper': '',
        'nme_first_upper': '',
        'nme_last_upper': 'jones',
        'nme_middle_upper': '',
        'num_cde_juris': '3',
        'num_cde_juris_d': 'Alexandria+Circuit+Court',
        'num_pol_case': '',
        'prev_function': '',
        'putFunctionInQ': 'N',
        'putKeysInBigQ': 'Y',
        'putKeysInLittleQ': 'N',
        'scrollx': '',
        'tabname': 'tab1',
        'tms_bf': '11/27/2014+11:02:07'
    })
    app = opener.open('http://ajis.alexandriava.gov/ajis/Court/cc600a_actn.cfm', data)
    print BeautifulSoup(app.read()).get_text()
    
    #pprint({x.split('=')[0] : urllib.unquote(x.split('=')[1]) for x in raw.split('&')})
    #session['cookies'] = pickle.dumps(list(cookieJar))
    
    #courts = []
    #html = BeautifulSoup(home.read())
    #for option in html.find_all('option'):
    #    courts.append({'fullName': option['value'], 'id': option['value'][:3], 'name': option['value'][5:]})
    #    
    #return render_template('search.html', data={'name': name.upper(), 'courts': courts})
    
    return 'OK'

@app.route("/")
def index():
    return render_template('index.html')

if __name__ == "__main__":
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.secret_key = 'doesnt-need-to-be-secret'
    app.run(host='0.0.0.0', port=port, debug=True)
