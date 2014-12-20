#!/usr/bin/env python
# coding: utf-8
"""
    admin.py
    ~~~~~~~~~~

"""
import re
from datetime import datetime
from flask import Blueprint, render_template, g, request, abort, jsonify

from models import Post, Comment, Link, Media
from helpers import gen_pager

adminor = Blueprint('admin', __name__, template_folder="../templates")


@adminor.route("/postlist")
@adminor.route('/postlist/<int:page>')
def adminpostlist(page=1):
    perpage = g.config["PER_PAGE"]
    postlist = Post.get_page(
        offset=(page-1)*perpage,
        limit=perpage,
        public_only=False)
    pager = gen_pager(Post.count(public_only=False),
                      g.config["PER_PAGE"],
                      page)
    return render_template('admin/postlist.html',
                           postlist=postlist,
                           admin_url="pagelist",
                           pager=pager)


@adminor.route("/post/<url>/inplace")
def pageinplace(url=None):
    """Check if a url is in place
    """
    post = Post.get_by_url(url=url, public_only=False)
    if post:
        return jsonify(success=True,
                       in_place=True)
    else:
        return jsonify(success=True,
                       in_plcae=False)


@adminor.route("/post", methods=["GET", "POST", "DELETE"])
@adminor.route("/post/<int:post_id>", methods=["GET", "POST", "DELETE"])
def editpost(post_id=None):
    '''show the edit page, update the post
    '''
    if request.method == "GET":
        post = Post()
        if post_id is not None:
            post = Post.get_by_id(post_id=post_id, public_only=False)
            if not post:
                abort(404)
        return render_template(
            'admin/editpost.html',
            admin_url="post",
            post=post)
    elif request.method == "POST":
        data = request.json
        now_time = datetime.now()
        post = None
        if data['post_id'] is not None:
            post = Post.get_by_id(
                post_id=int(data["post_id"]),
                public_only=False)
        else:
            post = Post()
            post.create_time = now_time
        post.update_time = now_time
        post.title = data.get("title", "")
        post.update_tags(data.get("tags", ""))
        post.url = data.get("url", "")
        post.keywords = data.get("keywords", "")
        post.metacontent = data.get("metacontent", "")
        post.content = data.get("content", "")
        post.raw_content = re.sub('<[^<]+?>', "", post.content)
        post.allow_comment = data.get("allow_comment", True)
        post.allow_visit = data.get("allow_visit", True)
        post.is_original = data.get("is_original", True)
        post.need_key = data.get("need_key", False)
        post.save()
        return jsonify(success=True,
                       post_id=post.post_id)

    elif request.method == "DELETE":
        # Delete post by id
        if post_id is not None:
            post = Post.get_by_id(int(post_id), public_only=False)
            if post:
                post.delete()
        # Batch Delete method
        else:
            removelist = request.json
            for post_id in removelist:
                post = Post.get_by_id(post_id=int(post_id), public_only=False)
                if post:
                    post.delete()
        return jsonify(success=True)


@adminor.route('/overview/<int:post_id>/')
def overview(post_id=-1):
    post = Post.get_by_id(post_id=post_id, public_only=False)
    if post:
        sidebar = None
        return render_template('page.html',
                               admin_url="overview",
                               post=post,
                               sidebar=sidebar)
    else:
        abort(404)


@adminor.route("/linkmgnt")
@adminor.route("/linkmgnt/<int:page>")
def linkmgnt(page=1):
    per_page = g.config["ADMIN_ITEM_COUNT"]
    linklist = Link.get_page(offset=per_page*(page-1), limit=per_page)
    return render_template('admin/linkmgnt.html',
                           linklist=linklist,
                           admin_url="linkmgnt",
                           )


@adminor.route("")
@adminor.route("/")
@adminor.route('/setting', methods=['GET', 'POST'])
def setting():
    if request.method == "GET":
        return render_template(
            "admin/setting.html",
            admin_url="setting",
            config=g.config)


@adminor.route('/mediamgnt', methods=['GET'])
@adminor.route('/mediamgnt/<int:page>', methods=["GET"])
def mediamgnt(page=1):
    per_page = g.config["ADMIN_ITEM_COUNT"]
    medialist = Media.get_page(per_page*(page-1), per_page)
    pager = gen_pager(
        Media.count(),
        per_page)
    return render_template('admin/mediamgnt.html',
                           admin_url="mediamgnt",
                           medialist=medialist,
                           pager=pager
                           )


@adminor.route('/commentmgnt', methods=["GET"])
@adminor.route('/commentmgnt/<int:page>')
def commentmgnt(page=1):
    if request.method == "GET":
        per_page = g.config["ADMIN_ITEM_COUNT"]
        if 'post_id' in request.args:
            post_id = request.args['post_id']
            commentlist = Comment.get_page(post_id=post_id, pagenumber=page)
            pager = gen_pager(Comment.count(), per_page, page)
        else:
            commentlist = Comment.get_page(
                offset=per_page*(page-1),
                limit=per_page)
            pager = gen_pager(Comment.count(), per_page, page)
        return render_template('admin/commentmgnt.html',
                               commentlist=commentlist,
                               admin_url="commentmgnt",
                               pager=pager)

if __name__ == "__main__":
    pass
