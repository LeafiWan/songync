#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Clients for supported music site
"""

import logging
import re

import requests
from requests.exceptions import RequestException

from songync.exceptions import AuthException
from songync.utils import retry


class BaseClient(object):

    def __init__(self):
        self.session = requests.Session()

    def login(self, username, password):
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

    def login(self, username, password):
        login_token = None
        with retry(3, RequestException):
            self.session.get('http://yinyueyun.baidu.com')
            r = self.session.get(self._LOGIN_TOKEN_URL)
            if not r.status_code == 200:
                logging.error('status code: %d' % r.status_code)

            text = r.text
            logging.debug('Response from getting baidu token url:\n' + text)

            # extract login token
            m = re.search(r"bdPass\.api\.params\.login_token='(\w+)'", text)
            if not m:
                logging.error('Could not get login token.')
                logging.error(text)
                raise
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
            if not r.status_code == 200:
                logging.error('status code: %d' % r.status_code)
            if 'BDUSS' not in r.cookies:
                raise AuthException('Baidu music Auth failed. Reponse content:\n %s' % r.text)

            print 'Login successfully.'

    def get_fav_songs_info(self):
        raise NotImplementedError('This method has not been implemented.')


class DoubanFMClient(BaseClient):
    pass


class XiamiClient(BaseClient):
    pass
