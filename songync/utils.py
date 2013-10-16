#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from contextlib import contextmanager


@contextmanager
def retry(times, *exceptions):
    if not exceptions:
        exceptions = (Exception, )
    failed_times = 0
    while True:
        try:
            yield
            break
        except tuple(exceptions) as ex:
            failed_times += 1
            logging.warning(ex)
            if failed_times >= times:
                raise ex
