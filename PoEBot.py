# -*- coding: utf-8 -*-

import datetime
import json
import math
import pytz
import requests
import socket
import sys
import sys
import threading
import time

#SETTINGS
server = "SERVERADDRESS"       
channel = "#CHANNEL"
botnick = "BOTNAME"
port = 6667
#password = "oauth:asdasd234asd234ad234asds23" #Default is just an example password for twitch oauth format. Uncomment line 58 if you want this to work
MYTZ=pytz.timezone('US/Eastern') #CHANGE IF NOT EASTERN
administrators=[b'User1', b'User2'] #List any channel admins here. They will have access to all commands! NOTE THE b IS NECESSARY BEFORE EACH USER
rate_limit = 10.0 #seconds between messages. 0 means unlimited messages
defLeague = None #Non-race league for tracking. Change if you want to track a league when races aren't active, eg "Nemesis" or "Domination". Quotes important
trackAccount = None # Change this to 'account name' of the streamer to have it be the default tracked account. Single quotes important.
#END SETTINGS

ZULU = pytz.timezone('Zulu')  #DONTCHANGE
EVENT_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
ANNOUNCE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S UTC"


def parseEventDate(date):
   return datetime.datetime.strptime(date, EVENT_TIME_FORMAT).replace(tzinfo=ZULU)

def secondsUntil(then):
   now = datetime.datetime.now(MYTZ)
   return math.ceil((then - now).total_seconds())

def send(irc, to, msg):
   irc.send(bytes('PRIVMSG %s :%s\r\n' % (to, msg), "UTF-8"))


# Initilization
events = requests.get('http://api.pathofexile.com/leagues?type=event').json()
NextEvent = events[0]
start = parseEventDate(NextEvent['startAt'])
until = secondsUntil(start)
lg = 'none'
tracking = trackAccount
last_message = datetime.datetime.now(MYTZ)
#Done Initializing


#Connect to IRC
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #defines the socket
print("connecting to:"+ server)
irc.connect((server, port))   
#irc.send(bytes("PASS "+ password +"\n", 'UTF-8')) #Authentication, beta   
irc.send(bytes("NICK "+ botnick +"\n", 'UTF-8'))                                                      #connects to the server
irc.send(bytes("USER "+ botnick +" "+ botnick +" "+ botnick +" :Skyl3lazer's PoE bot\n", 'UTF-8')) #user authentication
time.sleep(15)
irc.send(bytes("JOIN "+ channel +"\n", 'UTF-8'))        #tries to join channel again

   

#Race Alerts
def hourAlert():
   print("HOURALERT")
   events = requests.get('http://api.pathofexile.com/leagues?type=event').json()
   
   NextEvent = events[0]
   start = parseEventDate(NextEvent['startAt'])
   until = secondsUntil(start)

   # First listed might have started already
   if until <= 0:
      NextEvent = events[1]
      start = parseEventDate(NextEvent['startAt'])
      until = secondsUntil(start)
   
   send(irc, channel, 'EVENT ALERT - 1 HOUR - %(id)s - Occurs at %(start)s - %(url)s' % {
         "id"    : NextEvent['id'],
         "start" : start.strftime(ANNOUNCE_TIME_FORMAT),
         "url"   : NextEvent['url']
         })
   print("Starting Timer to event - %d" % (until - 300))
   return [until - 300, 'e']


def startAlert():
   print("STARTALERT")
   events = requests.get('http://api.pathofexile.com/leagues?type=event').json()

   NextEvent = events[0]
   start = parseEventDate(events[1]['startAt'])
   until = secondsUntil(start)

   if until > 3600:
      send(irc, channel, 'EVENT ALERT - STARTING IN 5 MINUTES - %(id)s - %(url)s' % {
            "id"    : NextEvent['id'],
            "start" : start.strftime(ANNOUNCE_TIME_FORMAT),
            "url"   : NextEvent['url']
            })
      print("Starting Timer to 1hr - " + str(until - 3600))
      return [until - 3600, 'h']
   elif until > 300:
      send(irc, channel, 'EVENT ALERT - STARTING IN 5 MINUTES - %(id)s - %(url)s' % {
            "id"    : NextEvent['id'],
            "start" : start.strftime(ANNOUNCE_TIME_FORMAT),
            "url"   : NextEvent['url']
            })
      #TODO - Info about the race coming up in under an hour
      print("Starting Timer to event - " + str(until - 300))
      return [until - 300, 'e']
   else:
      print("Event Collision - SUB 5 MINUTE EVENT CHAIN")
      NextEvent = events[1]
      start = parseEventDate(events[2]['startAt'])
      until = secondsUntil(start)
      
      send(irc, channel, 'EVENT COLLISION ALERT - THERE MAY BE ERRORS HERE OR WITH THE NEXT ALERT - %(id) - %(url)s' % {
            "id"    : NextEvent['id'],
            "start" : start.strftime(ANNOUNCE_TIME_FORMAT),
            "url"   : NextEvent['url']
            })
      
      print("Starting Timer to next event - "  + str(until))
      return [until, 'e']
	
def alertLoop(n, t):
   while 1:
      time.sleep(n)
      r = t()
      n = r[0]
      t = r[1]
      if t == 'e':
         t = startAlert
      elif t == 'h':
         t = hourAlert
      else:
         print("Error occured")
   
if until > 3600: #Handle First event after bot start
   print("Starting Timer to 1hr - " + str(until - 3600))
   thread = threading.Thread(target=alertLoop, args=(until - 3600, hourAlert))
   thread.start()
elif until > 300:
   print("Starting Timer to event - " + str(until - 300))
   thread = threading.Thread(target=alertLoop, args=(until - 300, startAlert))
   thread.start()
else:
   NextEvent = events[1]
   start = parseEventDate(NextEvent['startAt'])
   until = secondsUntil(start)
   print("Starting Timer to next event 1h - " + str(until - 3600))
   thread = threading.Thread(target=alertLoop, args=(until - 3600, hourAlert))
   thread.start()
#End Alerts
  


def announceRank(irc, channel, account, league):
   ladder = requests.get("http://api.pathofexile.com/ladders/%s?limit=200" % (league,)).json()
   
   byClass = { "Duelist"  : 0,
               "Marauder" : 0,
               "Ranger"   : 0,
               "Scion"    : 0,
               "Shadow"   : 0,
               "Templar"  : 0,
               "Witch"    : 0 }
   charClass = None
   rank = None
   rankInClass = None

   for entry in ladder['entries']:
      byClass[entry['character']['class']] += 1
      if entry['account']['name'].lower() == account.lower():
         charClass = entry['character']['class']
         rank = entry['rank']
         rankInClass = byClass[entry['character']['class']]
         break
           
   if rank is None:
      send(irc, channel, "Account %(account)s in league %(league)s is not in the top 200 on the ladder" % {
            "account" : account,
            "league"  : league
            })
   else:
      send(irc, channel, "Account %(account)s in league %(league)s is Rank %(rank)s overall and Rank %(crak)s %(class)s" % {
            "account" : account,
            "league"  : league,
            "rank"    : rank,
            "class"   : charClass,
            "crank"   : rankInClass
            })


while 1:    #puts it in a loop
   text = irc.recv(2040)  #receive the text
   now = datetime.datetime.now(MYTZ)
   time_passed = datetime.datetime.now(MYTZ) - last_message
   last_message = now

   print(text)   #print text to console
   if text.find(b'PING') != -1:                          #check if 'PING' is found
      print("Return Ping Sent")
      print(bytes('PONG ' + text.split() [1].decode('utf-8') + '\r\n', 'UTF-8'))
      irc.send(bytes('PONG ' + text.split() [1].decode('utf-8') + '\r\n', 'UTF-8')) #returns 'PONG' back to the server (prevents pinging out!)
   
   if any([text.find(adm) != -1 for adm in administrators]):
      if text.find(b':!track') != -1:
         print("Admin Command Found - Track")
         if len(text.split(maxsplit = 5)) > 4:
            tracking = text.split(maxsplit = 5)[4]
            tracking = str(tracking)[2:-1]
            send(irc, channel, "Now tracking account %s" % (tracking,))
         else:
            senc(irc, channel, "Use: !track <accountName>")

   # Throttling?
   if time_passed.total_seconds() <= rate_limit:
      continue

   if text.find(b':!place') != -1 or text.find(b':!rank' ) != -1: #!Place\!Rank Command - Check current rank of tracked account
      print("Command found - Place\Rank")
      if tracking is None:
         send(irc, channel, "No Character being Tracked at this time")
      else:
         currentEvent = requests.get('http://api.pathofexile.com/leagues?type=event').json()[0]
         start = parseEventDate(currentEvent['startAt'])
         if start < now: # Event Running
            announceRank(irc, channel, tracking, currentEvent['id'])
         elif defLeague is not None:
            announceRank(irc, channel, tracking, defLeague)
         else:
            send(irc, channel, "No races are currently running!")
   
   if text.find(b':!next') != -1:                          #!next
      print("Command found - Next Event")
      events = requests.get('http://api.pathofexile.com/leagues?type=event').json()
      start = parseEventDate(events[0]['startAt'])

      # Announce running event and next one
      if start < now:
         end = parseEventDate(events[0]['endAt'])
         remain = end - now
         send(irc, channel, "EVENT IN PROGRESS - %(id)s - Started at %(start)s, ends at %(end)s - %(remd)s%(remt)s remaining - %(url)s" % {
               "id"    : events[0]['id'],
               "url"   : events[0]['url'],
               "start" : start.strftime(ANNOUNCE_TIME_FORMAT),
               "end"   : end.strftime(ANNOUNCE_TIME_FORMAT),
               "remd"  : "%d days " if remain.days != 0 else "",
               "remt"  : (datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(seconds=remain.seconds)).strftime("%H:%M:%S")
               })

         time.sleep(1) #prevent Twitch throttling the second message
         
         start = parseEventDate(events[1]['startAt'])
         until = start - now
         send(irc, channel, "%(id)s - Occurs at %(start)s, in \u0002%(untild)s%(untilt)s\u000F - %(url)s" % {
               "id"     : events[1]['id'],
               "url"    : events[1]['url'],
               "start"  : parseEventDate(events[1]['startAt']).strftime(ANNOUNCE_TIME_FORMAT),
               "untild" : "%d days " if until.days != 0 else "",
               "untilt" : (datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(seconds=until.seconds)).strftime("%H:%M:%S")
               })
      # Just announce next
      else:
         start = parseEventDate(events[0]['startAt'])
         until = start - now
         send(irc, channel, "%(id)s - Occurs at %(start)s, in \u0002%(untild)s%(untilt)s\u000F - %(url)s" % {
               "id"     : events[0]['id'],
               "url"    : events[0]['url'],
               "start"  : parseEventDate(events[1]['startAt']).strftime(ANNOUNCE_TIME_FORMAT),
               "untild" : "%d days " if until.days != 0 else "",
               "untilt" : (datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(seconds=until.seconds)).strftime("%H:%M:%S")
               })

   if text.find(b':!help') != -1:
      print("Command found - Help")
      send(irc, channel, "!next - Displays next upcoming event, and any currently running event")
      send(irc, channel, "!place/!rank - Displays the place of the !track ed account in the current race")

   if text.find(b':!about') != -1:  #you don't have to keep this obviously, but credit is nice :)
      send(irc, channel, "PoEBot - A PoE race IRC/Twitch bot by Skyl3lazer! https://github.com/Skyl3lazer/PoEBot")
