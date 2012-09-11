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

def encSong(song):
    i=unicode(song[0], errors='replace')
    t=unicode(song[1], errors='replace')

    return (i,t)

def isBlacklisted(song):
    return song in blacklist

def LastFmToSong(track):
    artist = str(track.get_artist())
    title  = track.get_name()
    return (artist, title)

def SongToLastFm(song):
    search = lastfm.search_for_track(song[0], song[1]).get_next_page()
    if len(search) == 0:
        print "title %s - %s not found" % song
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
    return song

def waitNextSong():
    print "waiting for next title"
    currentsong = getNp()
    while getNp() == currentsong:
        time.sleep(mpd_checkint)

def inPlaylist(song):
    lst = mpd_client.playlistsearch('artist', song[0], 'title', song[1])
    return len(lst)>0

def getSimilar(song):
    if (not song[0]) or (not song[1]):
        print "not enought song data"
        return []
    song=encSong(song)
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
        if inPlaylist(s):
            print "already in playlist: %s - %s" % s
            continue
        files = mpd_client.search('artist', s[0], 'title', s[1])
        if files:
            ret.append((s[0], s[1], files[0]["file"]))
        else:
            print "no matching files found to song %s - %s" % s
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
        print u"add %s - %s to playlist" % item[:2]
        mpd_client.add(item[2])
        addBlacklist(item[:2])

def scrobbleSong(song):
    ts = calendar.timegm(datetime.datetime.now().timetuple())
    song=encSong(song)
    lastfm.scrobble(song[0], song[1], ts)
    print u"scrobbled %s - %s" % song

def loop():
    while True:
        waitNextSong()
        newSong()


if __name__ == '__main__':
    loop()

