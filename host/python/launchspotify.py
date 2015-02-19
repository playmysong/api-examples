#!/usr/bin/env python

### (c) 2015 Playmysong Spotify Script for OS X.
### hello@playmysong.com / http://www.playmysong.com

import urllib2
import json
import time
import threading
import sys
from subprocess import call
from Foundation import *
from ScriptingBridge import *

Spotify = SBApplication.applicationWithBundleIdentifier_("com.spotify.client");

API_DOMAIN="https://app.playmysong.com/v1"

if len(sys.argv) < 2:
    sys.exit('Usage: %s API_TOKEN' % sys.argv[0])

playlistUri = ""
if len(sys.argv) > 2:
    playlistUri = "%s" % str(sys.argv[2])
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

playlists = {}
if playlistUri != "":
    playlists = {
            'udid': "Spotify Mac",
            'en_spotify': "true",
            'playlists': [
                {
                    "extid": playlistUri,
                    "name": "spotify",
                    "active": "true",
                    "source": "spotify"
                }
            ]   
    }
else:
    playlists = {
            'udid': "Spotify Mac",
            'en_spotify': "true",
            'playlists': [
                {
                    "extid": "-",
                    "name": "Spotify Example",
                    "active": "true",
                    "source": "spotify",
                    "tracks": []
                }
            ]   
    }

req = urllib2.Request(API_DOMAIN+'/playlists?&access_token='+accessToken)
req.add_header('Content-Type', 'application/json')

response = urllib2.urlopen(req, json.dumps(playlists))        

location = json.load(response)
print location

if location and location['location']:
    print "Launching Playmysong location " + location['location']['name']

    while True:
            if Spotify.currentTrack().duration():
                print time.strftime("%c") + " - " + location['location']['name'] + " - Playing " + Spotify.currentTrack().name() + " by " + Spotify.currentTrack().artist() + ": " +  '%s'%(Spotify.currentTrack().duration()) + ' / ' + '%s'%(Spotify.playerPosition()) + ". Next song in %is" %round(Spotify.currentTrack().duration() - Spotify.playerPosition())
                nowPlaying = {
                    'track': {
                        'i': Spotify.currentTrack().id(),
                    },
                    'status': 300
                }
                if (Spotify.currentTrack().duration() - Spotify.playerPosition()) < 10 and fetchingRequests == False and nextRequest == False:
                        fetchingRequests=True
                        t = ThreadClass()
                        t.start()
                if (updatedRequest != nowPlaying):
                        fetchingRequests=False
                        updatedRequest = nowPlaying
                        u = UpdateClass()
                        u.start()
                if (Spotify.currentTrack().duration() - Spotify.playerPosition()) < 2 and nextRequest != False:
                        Spotify.pause()
                        cmd = 'tell application "Spotify" to play track "'+nextRequest['track']['i']+'"'
                        call(['osascript','-e',cmd])
                        nextRequest=False
            time.sleep(1)
else:
    print "Coudln't launch location."