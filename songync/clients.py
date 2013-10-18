#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Clients for supported music site
"""

import logging
import re
from collections import namedtuple

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

from songync.decorators import retry
from songync.exceptions import AuthException


SongInfo = namedtuple("SongInfo", ['name', 'artist', 'album'])


class BaseClient(object):

    def __init__(self):
        self.session = requests.Session()
        self._login_flag = False
        self.init()

    def init(self):
        pass

    def login(self, username, password):
        if self.do_login(username, password):
            self._login_flag = True
        return self._login_flag

    def do_login(self, username, password):
        raise NotImplementedError('This method has not been implemented.')

    def get_fav_songs_info(self):
        raise NotImplementedError('This method has not been implemented.')

    def search_song(self, song_info):
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
                print 'It needs verifying, please open the following URL in your browser then input the catpcha you will see:'
                print self._CAPTCHA_URL + '?' + codestring
                verifycode = raw_input('verify code: ')

                login_data['verifycode'] = verifycode
                login_data['codestring'] = codestring

                with retry(3, RequestException):
                    r = self.session.post(self._LOGIN_URL, data=login_data)
                    if r.status_code != 200:
                        logging.error('status code: %d' % r.status_code)

            if 'BDUSS' not in r.cookies:
                raise AuthException('Baidu music authentication failed. Reponse content:\n %s' % r.text)

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

    _LOGIN_URL = 'http://douban.fm/j/login'
    _NEW_CAPTCHA_URL = 'http://douban.fm/j/new_captcha'
    _FAV_SONG_URL = 'http://douban.fm/j/play_record'

    def init(self):
        self._ck = None
        self._bid = None

    def do_login(self, email, password):
        res = None
        with retry(3, RequestException):
            login_data = {
                'source': 'radio',
                'alias': email,
                'form_password': password,
                'task': 'sync_channel_list'
            }
            r = self.session.post(self._LOGIN_URL, data=login_data)
            if not r.status_code == 200:
                logging.error('status code: %d' % r.status_code)
                return False

        res = r.json()
        while res and res.get('err_no', None) == 1011:
            # catpcha
            captcha_id = self._get_captcha_id()
            if not captcha_id:
                return False
            print 'It needs verifying, please open the following URL in your browser then input the catpcha you will see:'
            print 'http://douban.fm/misc/captcha?size=m&id=' + captcha_id
            verifycode = raw_input('verify code: ')
            login_data['captcha_solution'] = verifycode
            login_data['captcha_id'] = captcha_id
            with retry(3, RequestException):
                r = self.session.post(self._LOGIN_URL, data=login_data)
                if not r.status_code == 200:
                    logging.error('status code: %d' % r.status_code)
                    return False
                res = r.json()

        if 'user_info' not in res:
            raise AuthException('Xiami Music authentication failed.')

        self._ck = res['user_info']['ck']
        self._bid = self.session.cookies.get_dict()['bid'].replace('"', '')
        if not self._ck or not self._bid:
            logging.error('ck or bid could not be fetched.')
            print False
        return True

    def _get_captcha_id(self):
        captcha_id = None
        with retry(3, RequestException):
            r = self.session.get(self._NEW_CAPTCHA_URL)
            if not r.status_code == 200:
                logging.error('status code: %d' % r.status_code)
                return None
            captcha_id = r.json()

        if not captcha_id:
                logging.error('Get captcha id failed.')
                return None
        return captcha_id

    def get_fav_songs_info(self):
        infos = []
        start = 0
        total = 100
        page_size = 100
        user_id_sign = self._get_user_id_sign()
        while start < total - 1:
            song_infos = []
            with retry(3, RequestException):
                r = self.session.get(self._FAV_SONG_URL, params=dict(
                    ck=self._ck,
                    spbid=user_id_sign + self._bid,
                    type='liked',
                    start=start
                ), headers={
                    'Host': 'douban.fm',
                    'X-Requested-With': 'XMLHttpRequest',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.65 Safari/537.36',
                    'Referer': 'http://douban.fm/mine?type=liked '
                })
                print r.request.url
                if not r.status_code == 200:
                    logging.error('status code: %d' % r.status_code)
                    continue
                res = r.json()
                print res
                page_size = res['per_page']
                total = res['total']
                start += page_size
                song_infos = [SongInfo(s['title'], s['artist'], s['subject_title']) for s in res['songs']]

            infos.extend(song_infos)
        infos.reverse()
        return infos

    def _get_user_id_sign(self):
        html_content = None
        with retry(3, RequestException):
            r = self.session.get('http://douban.fm/mine#!type=liked')
            if not r.status_code == 200:
                logging.error('status code: %d' % r.status_code)
                return None
            html_content = r.text
        if not html_content:
            return None

        matches = re.findall(r'<script>([\s\S]+?)<\/script>', html_content)
        magic_script = matches[-2] + ";setTimeout(function(){console.log(window.user_id_sign)}, 1000);"
        print "Plase run the following piece of code in your browser's console:\n"
        print "/*=======================*/"
        print magic_script
        print "/*=======================*/"
        user_id_sign = raw_input('\nEnter the return code: ')
        return user_id_sign


class XiamiClient(BaseClient):

    _LOGIN_URL = 'https://login.xiami.com/member/login'
    _SEARCH_URL = 'http://www.xiami.com/ajax/search-index'
    _ADD_FAV_URL = 'http://www.xiami.com/ajax/addtag'

    def init(self):
        self._xiamitoken = None
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.65 Safari/537.36',
        })

    def do_login(self, email, password):
        with retry(3, RequestException):
            r = self.session.get('http://www.xiami.com')
            if r.status_code != 200:
                logging.error('status code: %d' % r.status_code)
            self._xiamitoken = r.cookies.get('_xiamitoken', None)

        if self._xiamitoken is None:
            logging.error('Get _xiamitoken failed.')
            return False

        self.session.params = {
            '_xiamitoken': self._xiamitoken
        }

        with retry(3, RequestException):
            r = self.session.post(self._LOGIN_URL, data={
                'email': email,
                'password': password,
                'done': '/',
                '_xiamitoken': self._xiamitoken,
                'submit': u'登 录',
            }, allow_redirects=False)
            if 'member_auth' not in r.cookies:
                raise AuthException('Xiami Music authentication failed.')

        print 'Login Xiami successfully.'
        return True

    def search_song(self, song_info):
        html_content = ''
        with retry(3, RequestException):
            r = self.session.get(self._SEARCH_URL, params={
                'key': ' '.join([song_info.name, song_info.artist])
            })
            if r.status_code != 200:
                logging.error('status code: %d' % r.status_code)
                return None
            html_content = r.text

        soup = BeautifulSoup(html_content)

        first_result = None
        try:
            first_result = soup.ul.li.a
        except AttributeError:
            return None

        if not first_result or 'song_result' not in first_result.get('class', None):
            return None

        href = first_result.get('href', None)
        m = re.search(r'\/song\/(\d+)', href)
        if not m:
            return None
        return m.group(1)

    def mark_song_as_fav(self, song_token):
        with retry(3, RequestException):
            r = self.session.post(self._ADD_FAV_URL, data={
                'type': 3,
                'id': song_token,
                'share': 0,
                'shareTo': 'all',
                '_xiamitoken': self._xiamitoken,
            }, headers={
                'Referer': 'http://www.xiami.com/song/%s' % song_token,
            })
            if r.status_code != 200:
                logging.error('status code: %d' % r.status_code)
                return False
            res = r.json()
            if res.get('status', None) != 'ok':
                return False
        return True
