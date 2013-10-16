#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Clients for supported music site
"""

import logging
import re
from collections import namedtuple

import requests
from requests.exceptions import RequestException

from songync.decorators import retry
from songync.exceptions import AuthException


SongInfo = namedtuple("SongInfo", ['name', 'artist', 'album'])


class BaseClient(object):

    def __init__(self):
        self.session = requests.Session()
        self._login_flag = False

    def login(self, username, password):
        if self.do_login(username, password):
            self._login_flag = True
        return self._login_flag

    def do_login(self, username, password):
        raise NotImplementedError('This method has not been implemented.')

    def get_fav_songs_info(self):
        raise NotImplementedError('This method has not been implemented.')

    def search_song(self, singer, name):
        raise NotImplementedError('This method has not been implemented.')

    def mark_song_as_fav(self, song_token):
        raise NotImplementedError('This method has not been implemented.')


class BaiduMusicClient(BaseClient):

    _LOGIN_TOKEN_URL = 'https://passport.baidu.com/v2/api/?getapi&class=login&tpl=music&tangram=true'
    _LOGIN_URL = 'https://passport.baidu.com/v2/api/?login'
    _SONG_IDS_URL = 'http://yinyueyun.baidu.com/data/cloud/collection?type=song'
    _SONG_INFO_URL = 'http://yinyueyun.baidu.com/data/cloud/songinfo'
    _CAPTCHA_URL = 'https://passport.baidu.com/cgi-bin/genimage'

    def do_login(self, username, password):
        login_token = None
        with retry(3, RequestException):
            self.session.get('http://yinyueyun.baidu.com')
            r = self.session.get(self._LOGIN_TOKEN_URL)
            if r.status_code != 200:
                logging.error('status code: %d' % r.status_code)

            text = r.text
            logging.debug('Response from getting baidu token url:\n' + text)

            # extract login token
            m = re.search(r"bdPass\.api\.params\.login_token='(\w+)'", text)
            if not m:
                logging.error('Could not get login token.')
                logging.error(text)
                return False
            login_token = m.group(1)

        login_data = {
            'ppui_logintime': 36473,
            'charset': 'UTF-8',
            'token': login_token,
            'isPhone': 'false',
            'index': 0,
            'safeflg': 0,
            'staticpage': 'http://yinyueyun.baidu.com/cloud/v2Jump.html',
            'loginType': 1,
            'tpl': 'music',
            'callback': 'parent.bdPass.api.login._postCallback',
            'username': username,
            'password': password,
            'mem_pass': 'off'
        }
        with retry(3, RequestException):
            r = self.session.post(self._LOGIN_URL, data=login_data)
            if r.status_code != 200:
                logging.error('status code: %d' % r.status_code)

            while True:
                m = re.search(r'&error=(\d+)', r.text)
                if not (m and int(m.group(1)) in [257, 6]):
                    break
                # need verify
                code_str_m = re.search(r'codestring=(\w+)', r.text)
                codestring = code_str_m.group(1) if code_str_m else ''
                if not codestring:
                    logging.error('Could not get the codestring for get captcha url.')
                    return False
                print 'Need verifying, please open the following url in your browser then input the catpcha you will see below before any refreshing:'
                print self._CAPTCHA_URL + '?' + codestring
                verifycode = raw_input('verify code: ')

                login_data['verifycode'] = verifycode
                login_data['codestring'] = codestring

                with retry(3, RequestException):
                    r = self.session.post(self._LOGIN_URL, data=login_data)
                    if r.status_code != 200:
                        logging.error('status code: %d' % r.status_code)

            if 'BDUSS' not in r.cookies:
                raise AuthException('Baidu music Auth failed. Reponse content:\n %s' % r.text)

            print 'Login Baidu Music successfully.'
            return True

    def get_fav_songs_info(self):
        batch_size = 200
        infos = []
        total = 500
        start = 0
        while start < total:
            tmp_start = start
            start += batch_size
            song_ids = []
            with retry(3, RequestException):
                r = self.session.get(self._SONG_IDS_URL, params={
                    'start': tmp_start,
                    'size': batch_size
                })
                if r.status_code != 200:
                    logging.error('status code: %d' % r.status_code)
                    continue
                res = r.json()
                if res['errorCode'] == 22000:
                    total = res['data']['total']
                    song_list = res['data']['songList']
                    song_ids = [str(s['id']) for s in song_list]
            if not song_ids:
                continue
            with retry(3, RequestException):
                r = self.session.post('http://yinyueyun.baidu.com/data/cloud/songinfo', data={
                    'songIds': ','.join(song_ids)
                })
                if not r.status_code == 200:
                    logging.error('status code: %d' % r.status_code)
                    continue
                res = r.json()
                if res['errorCode'] == 22000:
                    song_list = res['data']['songList']
                    song_infos = [SongInfo(s['songName'], s['artistName'], s['albumName']) for s in song_list]
                    infos.extend(song_infos)
        return infos


class DoubanFMClient(BaseClient):
    pass


class XiamiClient(BaseClient):
    pass
