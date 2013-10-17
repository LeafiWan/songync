#!/usr/bin/env python
# -*- coding: utf-8 -*-

from getpass import getpass

from songync.clients import BaiduMusicClient
from songync.clients import XiamiClient
from songync.exceptions import AuthException


def main():
    print u"""
This program will help you sync your favorite songs on baidu to Xiami.
"""
    bd_username = None
    bd_pwd = None

    baidu_client = BaiduMusicClient()
    while True:
        bd_username = raw_input('Baidu username: ')
        bd_pwd = getpass('Baidu password: ')
        try:
            baidu_client.login(bd_username, bd_pwd)
            break
        except AuthException:
            print 'Username and password are not match, please retry.'

    xiami_username = None
    xiami_pwd = None
    xiami_client = XiamiClient()
    while True:
        xiami_username = raw_input('Xiami account email: ')
        xiami_pwd = getpass('Xiami password: ')
        try:
            xiami_client.login(xiami_username, xiami_pwd)
            break
        except AuthException:
            print 'Email and password are not match, please retry.'

    baidu_songs_info = baidu_client.get_fav_songs_info()

    go_on = raw_input('Will sync %d songs, continue?[n] ' % len(baidu_songs_info))
    if not go_on or go_on == 'n':
        print 'Aborted.'
        return
    for info in baidu_songs_info:
        song_token = xiami_client.search_song(info)
        if not song_token:
            print u'Could not find %s - %s  on Xiami, skipped to next.' % (info.artist, info.name)
            continue
        if xiami_client.mark_song_as_fav(song_token):
            print u'Sync %s - %s successfully.' % (info.artist, info.name)
        else:
            print u'Sync %s - %s failed.' % (info.artist, info.name)

    print 'Done.'


if __name__ == '__main__':
    main()
