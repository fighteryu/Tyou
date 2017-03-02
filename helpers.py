#!/bin/env python
# coding:utf-8
import functools
from peewee import DoesNotExist
from compat import urlparse, parse_qs


def gen_pager(current, count, pagesize, baseurl, seperator="page"):
    """
    current: current page index, shoule always bigger than 0
    return {
        "current": xxx,
        "previous": xxx,
        "next": xxx
        "total_page": xxx
    }
    """
    if current <= 0:
        raise Exception("current page should always bigger than 0!")

    total_page = count // pagesize + 1
    if count % pagesize == 0:
        total_page -= 1
    if total_page == 0:
        total_page = 1

    pager = {}
    pager["current"] = current
    pager["previous"] = current - 1 if current - 1 > 0 else None
    pager["next"] = current + 1 if current + 1 <= total_page else None
    pager["total_page"] = total_page
    pager["seperator"] = seperator

    # this is to make sure baseurl + "page=<int: page>" always make a valid url
    frag = urlparse(baseurl)
    args = parse_qs(frag.query)
    # rebuild the query string, but ignore "page"
    query = "&".join(["=".join((k, args[k][0])) for k in args if k != seperator])
    baseurl = frag.path
    if query:
        baseurl += "?" + query + "&"
    else:
        baseurl += "?"
    pager["baseurl"] = baseurl
    return pager


def get_or_none(old_func):
    """
        get one from datebase and return None instead of raising an exception
    """
    @functools.wraps(old_func)
    def new_func(*args, **kwargs):
        try:
            return old_func(*args, **kwargs)
        except DoesNotExist:
            return None
    return new_func
