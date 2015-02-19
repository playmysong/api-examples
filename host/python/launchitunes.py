#!/usr/bin/env python

### (c) 2015 Playmysong iTunes Script for OS X. 
### hello@playmysong.com / http://www.playmysong.com

import urllib2
import json
import time
import threading
import sys
from subprocess import call
from Foundation import *
from ScriptingBridge import *

iTunes = SBApplication.applicationWithBundleIdentifier_("com.apple.iTunes")

API_DOMAIN="https://app.playmysong.com/v1"

if len(sys.argv) < 2:
    sys.exit('Usage: %s API_TOKEN' % sys.argv[0])

accessToken = "%s" % str(sys.argv[1])
fetchingRequests=False
updatedRequest=False
location=False
nowPlaying=False
nextRequest=False
class ThreadClass(threading.Thread):    
    def run(self):
        global location
        global API_DOMAIN
        global accessToken
        global nextRequest
        global fetchingRequests
        print "Fetching next request..."
        start = time.time()
        response = urllib2.urlopen(API_DOMAIN+'/locations/'+location['location']['name']+'/requests/?status=0&access_token='+accessToken)
        data = json.load(response)   
        print "Done fetching next request, took: %s" % (time.time() - start)
        if data and data['requests'] and len(data['requests']) > 0:
            print data['requests'][0]
            nextRequest=data['requests'][0]
        else:
            print "No requests found."

class UpdateClass(threading.Thread):    
    def run(self):
        global updatedRequest
        global nowPlaying
        global location
        global API_DOMAIN
        global accessToken
        print "Updating request: "
        print nowPlaying
        start = time.time()
        req = urllib2.Request(API_DOMAIN+'/locations/'+location['location']['name']+'/requests?&access_token='+accessToken)
        req.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(req, json.dumps(nowPlaying))        

        data = json.load(response)   
        print "Done updating request, took: %s" % (time.time() - start)
        if data:
            print data
        else:
            print "No response found from update..."

playlists = {
    'udid': "iTunes Mac",
    'playlists': []
}

pls = iTunes.sources()[0].playlists()
for pl in pls:
    if "Playmysong" in pl.name():
        p = {
            'name':pl.name(),
            'extid':pl.id(),
            "active":"true",
            "source":"local",
            "tracks": []
        }
        tracks = pl.tracks()
        for tr in tracks:
            t = {
            "a": tr.artist(),
            "al": tr.album(),
            "d": tr.duration(),
            "i": tr.databaseID(),
            "t": tr.name()
            }
            p['tracks'].append(t)
        playlists['playlists'].append(p)

print playlists

req = urllib2.Request(API_DOMAIN+'/playlists?&access_token='+accessToken)
req.add_header('Content-Type', 'application/json')

response = urllib2.urlopen(req, json.dumps(playlists))        

location = json.load(response)
print location

if location and location['location']:
    print "Launching Playmysong location " + location['location']['name']

    while True:
            if iTunes.currentTrack().duration():
                print time.strftime("%c") + " - " + location['location']['name'] + " - Playing " + iTunes.currentTrack().name() + " by " + iTunes.currentTrack().artist() + ": " +  '%s'%(iTunes.currentTrack().duration()) + ' / ' + '%s'%(iTunes.playerPosition()) + ". Next song in %is" %round(iTunes.currentTrack().duration() - iTunes.playerPosition())
                nowPlaying = {
                    'track': {
                        'i': iTunes.currentTrack().databaseID(),
                        'a': iTunes.currentTrack().artist(),
                        't': iTunes.currentTrack().name(),
                        'd': '%s'%(iTunes.currentTrack().duration()),
                    },
                    'status': 300
                }
                if (iTunes.currentTrack().duration() - iTunes.playerPosition()) < 10 and fetchingRequests == False and nextRequest == False:
                        fetchingRequests=True
                        t = ThreadClass()
                        t.start()
                if (updatedRequest != nowPlaying):
                        fetchingRequests=False
                        updatedRequest = nowPlaying
                        u = UpdateClass()
                        u.start()
                if (iTunes.currentTrack().duration() - iTunes.playerPosition()) < 2 and nextRequest != False:
                        iTunes.pause()
                        cmd = 'tell application "iTunes" to play (a reference to (every track of playlist 1 whose database ID is '+nextRequest['track']['i']+'))'
                        call(['osascript','-e',cmd])
                        nextRequest=False
            time.sleep(1)

else:
    print "Coudln't launch location."