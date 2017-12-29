# -*- coding: utf-8 -*-
import GmailAPI
import httplib2
import soFifa
import time
import re
import sys
import StringIO
from unidecode import unidecode
import datetime


def sendError(service,botEmail,to,team,err):

    '''
    Sends an error message to the requester, notifying them that the request couldn't
    be processed. Calls create_message function from GmailAPI and passes the returned
    object to the send_message function from the GmailAPI.
    Args: service,str botEmail, str to, str team, str err
    Returns: None
    '''

    msg = GmailAPI.create_message(botEmail,to,'Error generating report for %s' % team,err)
    GmailAPI.send_message(service,botEmail,msg)

def readInbox(service,botEmail,query=''):

    '''
    Reads the inbox with the query passed in (default to an empty string).  Uses the
    ListThreadsMatchingQuery method in the GmailAPI to retrieve a list of emails. If the
    list is not empty, then the first email from the list is returned.
    Args: service, str botEmail, str query
    Returns: An email object
    '''

    requests = GmailAPI.ListThreadsMatchingQuery(service,botEmail,query)
    if(requests):
        print requests
        return requests.pop()
    else:
        return False

def sendMail(service,botEmail,message,to, team):

    '''
    Reads the inbox with the query passed in (default to an empty string).  Uses the
    ListThreadsMatchingQuery method in the GmailAPI to retrieve a list of emails. If the
    list is not empty, then the first email from the list is returned.
    Args: service, str botEmail, str query
    Returns: An email object
    '''

    msg = GmailAPI.create_html_message(botEmail,to,'Scout Report for %s' % team,message)
    try:
        GmailAPI.send_message(service,botEmail,msg)
    except Exception as err:
        sendError(service,user_id,to,request,str(err))

def respondToRequest(service,user_id,RequestThread):
    '''
    Reads the inbox with the query passed in (default to an empty string).  Uses the
    ListThreadsMatchingQuery method in the GmailAPI to retrieve a list of emails. If the
    list is not empty, then the first email from the list is returned.
    Args: service, str user_id, email RequestThread
    Returns: Void
    '''

    thread_id = RequestThread['id']
    request = re.search(r'(?<=[sS]cout [Tt]eam )[A-Za-z ]+', str(RequestThread['snippet'])).group().strip()
    sender = str(GmailAPI.GetMessageSender(service, user_id, thread_id))
    to = re.search(r'(?<=<)[a-z0-9@\._-]+', sender).group()
    print to
    print request

    try:
        response = soFifa.Squad(request).report()
    except Exception as err:
        sendError(service,user_id,to,request,str(err))
        GmailAPI.mark_thread_as_read(service, user_id, thread_id)
        return

    message ='''

        <html><h3><u>''' + response['teamName'] + " (" + str(datetime.date.today()) +")" + '''
        </u></h3>

          <h4>U23 players are highlighted.</h4>
            <table>
            <tr>
                <td>Name</td><td>Position</td>Age<td>Nation</td><td>Rating</td><td>Potential</td><td>Loaned To</td>
            </tr>
            <tbody>'''

    for player in response['players']:
        line = "<tr>"

        try:
            if(int(player['Age']) <= 22):
                line += '<td bgcolor="#ffe066">' + str(unidecode(unicode(player['Name']))) + '</td>'
            else:
                line += '<td>' + str(player['Name']) + '</td>'

            line += '<td>' + str(player['Position']) + '</td>'
            line += '<td>' + str(player['Age']) + '</td>' + '<td>' + str(player['Nation']) + '</td>' + '<td>' + str(player['Rating']) + '</td>' + '<td>' + str(player['Potential']) + '</td>' + '<td>' + str(player['LoanedTo'])+ '</td>'
        except Exception as err:
            sendError(service,user_id,to,request,str(err))
            GmailAPI.mark_thread_as_read(service, user_id, thread_id)
            return
        line += '</tr>'
        message += line

    message += "<h4>A cheeky bot by <a href=\"vishymakthal.github.io\">Vishy Makthal</a></h4></tbody></table></html>"

    sendMail(service, user_id, message, to, response['teamName'])
    GmailAPI.mark_thread_as_read(service, user_id, thread_id)
    print 'Returning to read loop'



def main():

    '''
    Main thread. Sets relevant authentications variables, and enters the read loop.
    Continues to call readInbox() until the inbox is empty, and responds to each request
    from the inbox.

    Args: Void
    Returns: Void
    '''

    credentials = GmailAPI.get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = GmailAPI.discovery.build('gmail', 'v1', http=http)
    user_id = 'hipstersoccerbot@gmail.com'

    print 'Entering read loop'
    while(True):
        requestThread = readInbox(service,user_id,"is:unread")
        time.sleep(0.1)
        if(requestThread):
            'Request found, responding'
            respondToRequest(service,user_id,requestThread)
        else:
            break

main()
