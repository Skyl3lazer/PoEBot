import socket
import sys
import requests
import json
import datetime
import pytz
import time
import threading
import sys

#SETTINGS
server = "SERVERADDRESS"       
channel = "#CHANNEL"
botnick = "BOTNAME"
port = 6667
#password = "oauth:asdasd234asd234ad234asds23" #Default is just an example password for twitch oauth format. Uncomment line 40 if you want this to work
MYTZ=pytz.timezone('US/Eastern') #CHANGE IF NOT EASTERN
ZULU=pytz.timezone('Zulu')  #DONTCHANGE

#INITIALIZATION
NET = 0
r = requests.get('http://api.pathofexile.com/leagues?type=event')
events=r.json()
NextEvent=events[0];
now = datetime.datetime.now(MYTZ)
nextEventTime = events[0]['startAt']
eventTimeY=int(nextEventTime[:4])
eventTimeM=int(nextEventTime[5:-13])
eventTimeD=int(nextEventTime[8:-10])
eventTimeH=int(nextEventTime[11:-7])
eventTimeMin=int(nextEventTime[14:-4])
timeConverted=datetime.datetime(eventTimeY, eventTimeM, eventTimeD, eventTimeH, eventTimeMin, 0, 0).replace(tzinfo=ZULU)
until = timeConverted - now
NET = int(until.total_seconds())

#Connect to IRC
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #defines the socket
print("connecting to:"+ server)
irc.connect((server, port))      
#irc.send(bytes("PASS "+password+"\n", 'UTF-8')) #Authentication, beta
irc.send(bytes("NICK "+ botnick +"\n", 'UTF-8')) #Set the nickname
irc.send(bytes("USER "+ botnick +" "+ botnick +" "+ botnick +" :PoEBot, a simple Path of Exile IRC Bot\n", 'UTF-8')) #User authentication
irc.send(bytes("JOIN "+ channel +"\n", 'UTF-8'))        #tries to join channel, probably doesnt
time.sleep(15)
irc.send(bytes("JOIN "+ channel +"\n", 'UTF-8'))        #join the channel for sure this time

#Race Alerts
def hourAlert():
   print("HOURALERT")
   r = requests.get('http://api.pathofexile.com/leagues?type=event')
   events=r.json()
   NextEvent=events[0];
   now = datetime.datetime.now(MYTZ)
   print(now)
   nextEventTime = events[0]['startAt']
   eventTimeY=int(nextEventTime[:4])
   eventTimeM=int(nextEventTime[5:-13])
   eventTimeD=int(nextEventTime[8:-10])
   eventTimeH=int(nextEventTime[11:-7])
   eventTimeMin=int(nextEventTime[14:-4])
   timeConverted=datetime.datetime(eventTimeY, eventTimeM, eventTimeD, eventTimeH, eventTimeMin, 0, 0).replace(tzinfo=ZULU)   
   until = timeConverted - now
   NET = int(until.total_seconds())
   if until.total_seconds() > 0:
    irc.send(bytes('PRIVMSG '+channel+' '+"EVENT ALERT - 1 HOUR - "+NextEvent['id'] +' - Occurs at '+NextEvent['startAt']+' - '+NextEvent['url']+'\r\n', 'UTF-8')) #gives event info
    print("Starting Timer to event - "+str(NET-300))
    return [NET-300,'e']
   else:
    NextEvent=events[1];
    now = datetime.datetime.now(MYTZ)
    nextEventTime = events[1]['startAt']
    eventTimeY=int(nextEventTime[:4])
    eventTimeM=int(nextEventTime[5:-13])
    eventTimeD=int(nextEventTime[8:-10])
    eventTimeH=int(nextEventTime[11:-7])
    eventTimeMin=int(nextEventTime[14:-4])
    timeConverted=datetime.datetime(eventTimeY, eventTimeM, eventTimeD, eventTimeH, eventTimeMin, 0, 0).replace(tzinfo=ZULU)    
    until = timeConverted - now
    NET = int(until.total_seconds())
    irc.send(bytes('PRIVMSG '+channel+' '+"EVENT ALERT - 1 HOUR - "+NextEvent['id'] +' - Occurs at '+NextEvent['startAt']+' - '+NextEvent['url']+'\r\n', 'UTF-8')) #gives event info
    print("Starting Timer to next event - "+str(NET-300))
    return [NET-300,'e']
def startAlert():
   print("STARTALERT")
   r = requests.get('http://api.pathofexile.com/leagues?type=event')
   events=r.json()
   NextEvent=events[0];
   now = datetime.datetime.now(MYTZ)
   print(now)
   nextEventTime = events[1]['startAt']
   eventTimeY=int(nextEventTime[:4])
   eventTimeM=int(nextEventTime[5:-13])
   eventTimeD=int(nextEventTime[8:-10])
   eventTimeH=int(nextEventTime[11:-7])
   eventTimeMin=int(nextEventTime[14:-4])
   timeConverted=datetime.datetime(eventTimeY, eventTimeM, eventTimeD, eventTimeH, eventTimeMin, 0, 0).replace(tzinfo=ZULU)
   until = timeConverted - now
   NET = int(until.total_seconds())
   if until.total_seconds() > 3600:
    irc.send(bytes('PRIVMSG '+channel+' '+"EVENT ALERT - STARTING IN 5 MINUTES - "+NextEvent['id'] +' - '+NextEvent['url']+'\r\n', 'UTF-8')) #gives event info
    print("Starting Timer to 1hr - " + str(NET-3600))
    return [NET-3600,'h']
   elif until.total_seconds() > 300:
    irc.send(bytes('PRIVMSG '+channel+' '+"EVENT ALERT - STARTING IN 5 MINUTES - "+NextEvent['id'] +' - '+NextEvent['url']+'\r\n', 'UTF-8')) #gives event info
	#TODO - Info about the race coming up in under an hour?
    print("Starting Timer to event - " + str(NET-300))
    return [NET-300,'e']
   else:
    print("Event Collision - SUB 5 MINUTE EVENT CHAIN")
    NextEvent=events[1];
    irc.send(bytes('PRIVMSG '+channel+' '+"EVENT COLLISION ALERT - THERE MAY BE ERRORS HERE OR WITH THE NEXT ALERT - "+NextEvent['id'] +' - '+NextEvent['url']+'\r\n', 'UTF-8')) #gives event info
    now = datetime.datetime.now(MYTZ)
    nextEventTime = events[2]['startAt']
    eventTimeY=int(nextEventTime[:4])
    eventTimeM=int(nextEventTime[5:-13])
    eventTimeD=int(nextEventTime[8:-10])
    eventTimeH=int(nextEventTime[11:-7])
    eventTimeMin=int(nextEventTime[14:-4])
    timeConverted=datetime.datetime(eventTimeY, eventTimeM, eventTimeD, eventTimeH, eventTimeMin, 0, 0).replace(tzinfo=ZULU)
    until = timeConverted - now
    NET = int(until.total_seconds())
    print("Starting Timer to next event - " +str(NET-300))
    return [NET-300,'e']
	
def alertLoop(n, t):
  while 1:
    time.sleep(n)
    r=t()
    n=r[0]
    t=r[1]
    if t == 'e':
     t = startAlert
    elif t == 'h':
     t = hourAlert
    else:
     print("Error occured")
   
if until.total_seconds() > 3600: #Handle First event after bot start
  print("Starting Timer to 1hr - " + str(NET-3600))
  thread = threading.Thread(target=alertLoop, args=(NET-3600, hourAlert))
  thread.start()
elif until.total_seconds() > 300:
  print("Starting Timer to event - " + str(NET-300))
  thread = threading.Thread(target=alertLoop, args=(NET-300, startAlert))
  thread.start()
else:
  NextEvent=events[1];
  now = datetime.datetime.now(MYTZ)
  nextEventTime = events[1]['startAt']
  eventTimeY=int(nextEventTime[:4])
  eventTimeM=int(nextEventTime[5:-13])
  eventTimeD=int(nextEventTime[8:-10])
  eventTimeH=int(nextEventTime[11:-7])
  eventTimeMin=int(nextEventTime[14:-4])
  timeConverted=datetime.datetime(eventTimeY, eventTimeM, eventTimeD, eventTimeH, eventTimeMin, 0, 0).replace(tzinfo=ZULU)
  until = timeConverted - now
  NET = int(until.total_seconds())
  print("Starting Timer to next event 1h - "+str(NET-3600))
  thread = threading.Thread(target=alertLoop, args=(NET-3600, hourAlert))
  thread.start()
#End Alerts
  


#IRC Loop
while 1: 
   text=irc.recv(2040)  #Recieve text
   print(text) 
   if text.find(b'PING') != -1:                          #check if 'PING' is found
      print("Return Ping Sent")
      print(bytes('PONG ' + text.split() [1].decode('utf-8') + '\r\n', 'UTF-8'))
      irc.send(bytes('PONG ' + text.split() [1].decode('utf-8') + '\r\n', 'UTF-8')) #returns 'PONG' back to the server (prevents pinging out!)
   if text.find(b':!next') != -1:                          #check if '!next' is found
      print("Command found - Next Event")
      r = requests.get('http://api.pathofexile.com/leagues?type=event')
      events=r.json()
      now = datetime.datetime.now(MYTZ)
      nextEventTime = events[0]['startAt']
      eventTimeY=int(nextEventTime[:4])
      eventTimeM=int(nextEventTime[5:-13])
      eventTimeD=int(nextEventTime[8:-10])
      eventTimeH=int(nextEventTime[11:-7])
      eventTimeMin=int(nextEventTime[14:-4])
      timeConverted=datetime.datetime(eventTimeY, eventTimeM, eventTimeD, eventTimeH, eventTimeMin, 0, 0).replace(tzinfo=ZULU)
      until = timeConverted - now
      NET = until.seconds
      until=str(until)
      until = until[:-7]
      if timeConverted < now:
        nextEventTime = events[0]['endAt']
        eventTimeY=int(nextEventTime[:4])
        eventTimeM=int(nextEventTime[5:-13])
        eventTimeD=int(nextEventTime[8:-10])
        eventTimeH=int(nextEventTime[11:-7])
        eventTimeMin=int(nextEventTime[14:-4])
        timeConverted=datetime.datetime(eventTimeY, eventTimeM, eventTimeD, eventTimeH, eventTimeMin, 0, 0).replace(tzinfo=ZULU)
        until = timeConverted - now
        NET = until.seconds
        until=str(until)
        until = until[:-7]
        irc.send(bytes('PRIVMSG '+channel+' EVENT IN PROGRESS - '+events[0]['id'] +' - Started at '+events[0]['startAt']+', ends at '+events[0]['endAt']+' - '+until+' remaining - '+events[0]['url']+'\r\n', 'UTF-8'))
        nextEventTime = events[1]['startAt']
        eventTimeY=int(nextEventTime[:4])
        eventTimeM=int(nextEventTime[5:-13])
        eventTimeD=int(nextEventTime[8:-10])
        eventTimeH=int(nextEventTime[11:-7])
        eventTimeMin=int(nextEventTime[14:-4])
        timeConverted=datetime.datetime(eventTimeY, eventTimeM, eventTimeD, eventTimeH, eventTimeMin, 0, 0).replace(tzinfo=ZULU)
        until = timeConverted - now
        NET = until.seconds
        until=str(until)
        until = until[:-7]
        irc.send(bytes('PRIVMSG '+channel+' '+events[1]['id'] +' - Occurs at '+events[1]['startAt']+', in \u0002'+until+'\u000F - '+events[1]['url']+'\r\n', 'UTF-8')) #gives event info
      else:
        irc.send(bytes('PRIVMSG '+channel+' '+events[0]['id'] +' - Occurs at '+events[0]['startAt']+', in \u0002'+until+'\u000F - '+events[0]['url']+'\r\n', 'UTF-8')) #gives event info
   if text.find(b':!help') != -1:   #Check for '!help' command
     print("Command found - Help")
     irc.send(bytes('PRIVMSG '+channel+' '+"!next - Displays next upcoming event, and any currently running event"+'\r\n', 'UTF-8'))
   #Add any other commands you wish!