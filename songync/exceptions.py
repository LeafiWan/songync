#!/usr/bin/env python
# -*- coding: utf-8 -*-


class AuthException(Exception):

    def __init__(self, msg):
        self.msg = msg
