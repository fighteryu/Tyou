#!/bin/env python
# coding:utf-8


def gen_pager(sumitem, perpage, currentpage=1):
    '''
    :param sumitem:total count of items
    :param perpage:: how many items displayed in each page
    return:dict to draw pagination
    '''
    pagenumber = sumitem/perpage
    if sumitem % perpage != 0:
        pagenumber += 1

    has_prv = False
    has_next = False
    if currentpage < pagenumber:
        has_next = True
    if currentpage > 1:
        has_prv = False
    return {"pagenumber": pagenumber,
            "currentpage": currentpage,
            "has_prv": has_prv,
            "has_next": has_next}
