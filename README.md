PoEBot
======

Path of Exile event IRC bot

This is a very simple IRC bot, meant to join a channel and assist with tracking PoE races.

!next will display the currently running race, if any, and the next upcoming event, with appropriate timers for time remaining and time until

!help will display the help (currently just !next and how it works)

The bot will also act as a timer: at one hour to an event, and five minutes before, it will say into the channel that an event is upcoming, along with details.

If for some reason you're looking to run this yourself, there's a few things it requires:

-Python 3.3
-pytz
-datetime

The two packages were not included by default on my install, so they may not be on yours either.

Within bot.py, you should also edit the server, channel, and botnick to appropriate values. I have not yet added an authentication feature yet.

If you are not in USE, you should also look for the 3 places that USE is specified and change them as appropriate. 

The second file, getevents.py, is simply there for testing functions without having to restart the bot. It probably won't be useful to you.
