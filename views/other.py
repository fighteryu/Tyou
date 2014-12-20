#!/usr/bin/env python
#coding:utf-8
"""
    other.py
    ~~~~~~~~~~~~~
    :license: BSD, see LICENSE for more details.
"""

import urllib
from urlparse import urljoin
from datetime import datetime,timedelta

from werkzeug.contrib.atom import AtomFeed
from flask import Blueprint, Response, request, flash, jsonify, g, current_app,\
    abort, redirect, url_for, session, send_file, send_from_directory, \
    render_template ,make_response

from application.models import USER, Post, Tag,Comment,Media,gen_sidebar
from application.decorators import cached

frontend=Blueprint('/',__name__,template_folder="../templates")
def make_external(url):
    return urljoin(request.url_root, url)

@frontend.route('/rss')
def recent_feed():
    feed = AtomFeed('文章订阅',
                    feed_url=request.url, url=request.url_root)
    postlist=Post.get_page(USER.page_set["rss_count"],1);
    for post in postlist:
        if not post.need_key:
            feed.add(post.title, unicode(post.content[0:300]+'......'),
                 content_type='html',
                 author="博主",
                 url=make_external('page/'+urllib.quote(post.url)),
                 updated=post.update_time,
                 published=post.create_time)
        else:
            feed.add(post.title, "文章被加密，输入密码查看",
                 content_type='html',
                 author="博主",
                 url=make_external('page/'+urllib.quote(post.url)),
                 updated=post.update_time,
                 published=post.create_time)

    return feed.get_response()

@frontend.route("/sitemap.xml")
def sitemap():
    """Generate sitemap.xml. Makes a list of urls and date modified."""
    # user model postlist
    postlist=[]
    alllist=Post.get_last_x_days(30)
    for post in alllist:
        url=make_external('page/'+post.url)
        modified_time=post.update_time.date().isoformat()
        postlist.append([url,modified_time]) 

    sitemap_xml = render_template('sitemap.xml', postlist=postlist)
    response= make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"    
    
    return response

@frontend.route("/test")
def test():
    param="name&def<>'"
    return render_template("test.html",
                            param=param)
