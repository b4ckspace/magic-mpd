#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import mpd
import pylast
import os

mpd_checkint = 10 
mpd_add_after = 30 # only add new songs after the current song has reached 30%
mpd_host = "10.1.20.5"
mpd_port = 6600

lastfm_apikey = os.environ.get('lastfm_apikey', "")
lastfm = pylast.LastFMNetwork(api_key = lastfm_apikey)

mpd_client = mpd.MPDClient()
mpd_client.connect(mpd_host, mpd_port)


blacklist_max = 20 #only blacklist the last 50 songs
blacklist = []

def isBlacklisted(song):
    return song in blacklist

def LastFmToSong(track):
    artist = str(track.get_artist())
    title  = track.get_name()
    return (artist, title)

def addBlacklist(song):
    global blacklist
    if song in blacklist:
        blacklist.remove(song) #move song to the end of the blacklist
    blacklist.append(song)
    if len(blacklist) > blacklist_max:
        blacklist = blacklist[(-1*blacklist_max):]

def getNp():
    np      = mpd_client.currentsong()
    artist  = np.get("artist")
    title   = np.get("title")
    song    = (artist, title)
    return song

def waitNextSong():
    print "waiting for next title"
    currentsong = getNp()
    while getNp() == currentsong:
        time.sleep(mpd_checkint)

def getSimilar(song):
    if (not song[0]) or (not song[1]):
        print "not enought song data"
        return []
    search = lastfm.search_for_track(song[0], song[1]).get_next_page()
    if len(search) == 0:
        print "title %s - %s not found" % song
        return []
    return search[0].get_similar() 

def getSimilarAdd(song, length=2):
    ret = []
    similars = getSimilar(song)
    if not similars:
        print "no similar tracks for %s - %s found" % song
    for si in similars:
        s = LastFmToSong(si.item)
        if isBlacklisted(s):
            print "blacklisted: %s - %s" % s
            continue
        files = mpd_client.search('artist', s[0], 'title', s[1])
        if files:
            ret.append((s[0], s[1], files[0]["file"]))
        else:
            print "no matching files found to song %s - %s" % s
        if len(ret) == length:
            return ret
    return ret

def loop():
    while True:
        waitNextSong()
        print getNp()
        addBlacklist(getNp())
        lst = getSimilarAdd(getNp())
        for item in lst:
            print "add %s - %s to playlist" % item[:2]
            mpd_client.add(item[2])
            addBlacklist(item[:2])

if __name__ == '__main__':
    loop()

