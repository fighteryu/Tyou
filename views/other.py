#!/usr/bin/env python
# coding:utf-8
"""
    other.py
    ~~~~~~~~~~~~~

"""

from datetime import datetime
from werkzeug.contrib.atom import AtomFeed
from flask import Blueprint, request, render_template, make_response, g

from models import Post

from compat import urljoin, quote

frontend = Blueprint('/', __name__, template_folder="../templates")


def make_external(url):
    return urljoin(request.url_root, url)


@frontend.route('/rss')
def recent_feed():
    feed = AtomFeed(g.config["BLOGNAME"],
                    feed_url=request.url, url=request.url_root)
    posts = Post.get_list(Post.allow_visit == True).order_by(-Post.id).limit(20)
    for post in posts:
        if not post.need_key:
            feed.add(post.title, post.html_content,
                     content_type='html',
                     author=u"博主",
                     url=make_external('page/' + quote(post.url)),
                     updated=post.update_time,
                     published=post.create_time)
        else:
            feed.add(post.title, u"文章被加密，输入密码查看",
                     content_type='html',
                     author=u"博主",
                     url=make_external('page/' + quote(post.url)),
                     updated=post.update_time,
                     published=post.create_time)

    return feed.get_response()


@frontend.route("/sitemap.xml")
def sitemap():
    """Generate sitemap.xml. Makes a list of urls and date modified."""
    # user model postlist
    postlist = []
    posts = Post.get_list(Post.allow_visit == True).order_by(Post.id.desc())

    url = make_external("/")
    if posts:
        modified_time = posts[0].update_time.date().isoformat()
    else:
        modified_time = datetime.now().date().isoformat()
    postlist.append([url, modified_time, 1.0])

    for post in posts:
        url = make_external('page/'+post.url)
        modified_time = post.update_time.date().isoformat()
        postlist.append([url, modified_time, 0.7])

    sitemap_xml = render_template('sitemap.xml', postlist=postlist)
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"

    return response
