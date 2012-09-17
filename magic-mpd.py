#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import mpd
import pylast
import os
import datetime, calendar

mpd_checkint = 10 
mpd_add_count = 2 #songs to add for every song
mpd_host = "10.1.20.5"
mpd_port = 6600

lastfm_apikey = os.environ.get('lastfm_apikey', "")
lastfm_apisecret = os.environ.get('lastfm_apisecret', "")
lastfm_user = os.environ.get('lastfm_user', "")
lastfm_passwd = pylast.md5(os.environ.get('lastfm_passwd', ""))
lastfm = pylast.LastFMNetwork(  api_key = lastfm_apikey, 
                                api_secret = lastfm_apisecret, 
                                username = lastfm_user, 
                                password_hash = lastfm_passwd)

mpd_client = mpd.MPDClient()
mpd_client.connect(mpd_host, mpd_port)


blacklist_max = 20 #only blacklist the last 50 songs
blacklist = []

def apiSong(song):
    i=song[0].decode('utf-8').encode('utf-8') if type(song[0]) != unicode else song[0]
    t=song[1].decode('utf-8').encode('utf-8') if type(song[1]) != unicode else song[1]
    return (i,t)

def printSong(song):
    i=song[0].decode('utf-8') if type(song[0]) != unicode else song[0]
    t=song[1].decode('utf-8') if type(song[1]) != unicode else song[1]
    return (i,t)

def isBlacklisted(song):
    return song in blacklist

def LastFmToSong(track):
    artist = str(track.get_artist())
    title  = track.get_name()
    return apiSong((artist, title))

def SongToLastFm(song):
    search = lastfm.search_for_track(song[0], song[1]).get_next_page()
    if len(search) == 0:
        print u"title %s - %s not found" % song
        return False
    return search[0]

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
    return apiSong(song)

def waitNextSong():
    print "waiting for next title"
    currentsong = getNp()
    while getNp() == currentsong:
        time.sleep(mpd_checkint)

def inPlaylist(song):
    #song=apiSong(song)
    lst = mpd_client.playlistsearch('artist', song[0], 'title', song[1])
    return len(lst)>0

def getSimilar(song):
    if (not song[0]) or (not song[1]):
        print "not enought song data"
        return []
    #song=apiSong(song)
    print song
    search = lastfm.search_for_track(song[0], song[1]).get_next_page()
    if len(search) == 0:
        print u"title %s - %s not found" % printSong(song)
        return []
    return search[0].get_similar() 

def getSimilarAdd(song, length=2):
    ret = []
    similars = getSimilar(song)
    if not similars:
        print u"no similar tracks for %s - %s found" % printSong(song)
    for si in similars:
        s = LastFmToSong(si.item)
        if isBlacklisted(s):
            print u"blacklisted: %s - %s" % printSong(s)
            continue
        if inPlaylist(s):
            print u"already in playlist: %s - %s" % printSong(s)
            continue
        files = mpd_client.search('artist', s[0], 'title', s[1])
        if files:
            ret.append((s[0], s[1], files[0]["file"]))
        else:
            print u"no matching files found to song %s - %s" % printSong(s)
        if len(ret) == length:
            return ret
    return ret

def newSong():
    song = getNp()
    print song
    addBlacklist(song)
    scrobbleSong(song)
    lst = getSimilarAdd(song, mpd_add_count)
    for item in lst:
        song=printSong(item)
        print "*"*10
        print song
        print u"add %s - %s to playlist" % printSong(song)
        mpd_client.add(item[2])
        addBlacklist(song)

def scrobbleSong(song):
    ts = calendar.timegm(datetime.datetime.now().utctimetuple())
    #song = apiSong(song)
    lastfm.scrobble(song[0], song[1], ts)
    print u"scrobbled %s - %s" % printSong(song)

def loop():
    while True:
        waitNextSong()
        newSong()


if __name__ == '__main__':
    loop()

