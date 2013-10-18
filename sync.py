#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from getpass import getpass

from songync.clients import BaiduMusicClient
from songync.clients import DoubanFMClient
from songync.clients import XiamiClient
from songync.exceptions import AuthException


_CLIENTS_MAP = {
    'baidu': BaiduMusicClient,
    'douban': DoubanFMClient,
    'xiami': XiamiClient,
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--from', dest='from_', type=str, choices=['baidu', 'douban'], required=True)
    parser.add_argument('-t', '--to', dest='to', type=str, choices=['xiami'], required=True)
    args = parser.parse_args()
    return args.from_, args.to


def main():
    from_, to = parse_args()
    print u"""Sync songs from %s to %s """ % (from_, to)

    username = None
    pwd = None

    from_client = _CLIENTS_MAP[from_]()
    while True:
        username = raw_input('%s username: ' % from_)
        pwd = getpass('%s password: ' % from_)
        try:
            from_client.login(username, pwd)
            break
        except AuthException:
            print 'username and password are not match, please retry.'

    to_client = _CLIENTS_MAP[to]()

    while True:
        username = raw_input('%s username: ' % to)
        pwd = getpass('%s password: ' % to)
        try:
            to_client.login(username, pwd)
            break
        except AuthException:
            print 'username and password are not match, please retry.'

    print 'Start to fetch your favorite songs from %s, this will take some time.' % from_
    from_songs_info = from_client.get_fav_songs_info()

    go_on = raw_input('Will sync %d songs, continue?[n] ' % len(from_songs_info))
    if not go_on or go_on == 'n':
        print 'Aborted.'
        return
    for info in from_songs_info:
        song_token = to_client.search_song(info)
        if not song_token:
            print u'Could not find %s - %s  on %s, skipped to next.' % (info.artist, info.name, to)
            continue
        if to_client.mark_song_as_fav(song_token):
            print u'Sync %s - %s to %s successfully.' % (info.artist, info.name, to)
        else:
            print u'Sync %s - %s to %s failed.' % (info.artist, info.name, to)

    print 'Done.'


if __name__ == '__main__':
    main()
