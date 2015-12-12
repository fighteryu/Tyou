#!/usr/bin/env python
# coding: utf-8
"""
    frontend.py
    ~~~~~~~~~~~~~

"""
import json
from datetime import datetime

from flask import request, jsonify, g, abort, render_template,\
    flash, redirect, url_for, session

from models import Post, Comment, User
from helpers import gen_pager
from .other import frontend
from compat import unquote


@frontend.route('/')
@frontend.route("/index")
def index():
    page = int(request.args.get("page", 1))
    offset = g.config["PER_PAGE"]*(page - 1)
    postlist = Post.get_page(offset, g.config["PER_PAGE"], allow_visit=True)
    pager = gen_pager(page, Post.count(allow_visit=True), g.config["PER_PAGE"],
                      request.url)
    if postlist or page == 1:
        return render_template(
            "index.html",
            blogname=g.config["BLOGNAME"],
            postlist=postlist,
            pager=pager)
    else:
        return render_template("error/404.html")


@frontend.route('/page/<url>')
def page(url=None):
    """display post"""
    post = Post.get_by_url(url=url, public_only=False)
    if post and post.allow_visit:
        commentlist = Comment.get_by_post_id(post.post_id)
        return render_template(
            'page.html',
            blogname=g.config["BLOGNAME"],
            post=post,
            commentlist=commentlist,
            is_admin=True)
    else:
        abort(404)


@frontend.route("/key", methods=["POST"])
@frontend.route("/key/", methods=["POST"])
def key():
    data = request.json
    if g.config.get("POST_PASSWORD", "") != data.get("post_password", None):
        return jsonify(
            validate=False,
            error=True,
            message=u"Password error!")

    post = Post.get_by_url(url=data.get("posturl", ""), public_only=False)
    if not post:
        return jsonify(
            validate=True,
            error=True,
            message="Post doesn't exists"
        )
    else:
        return jsonify(
            validate=True,
            error=False,
            message=post.content
        )


@frontend.route("/comment", methods=["DELETE", "POST"])
def comment():
    if request.method == "DELETE":
        if not session.get("is_admin", False):
            abort(401)
        removelist = request.json
        for item in removelist:
            comment = Comment.get_by_id(int(item))
            if comment:
                comment.delete()
        return jsonify(success=True,
                       message="success")
    elif request.method == "POST":
        usercomment = request.json
        nickname = usercomment["nickname"]
        email = usercomment["email"]
        content = usercomment["content"]
        website = usercomment["website"]
        post_id = usercomment["post_id"]
        refid = None
        to = None
        if usercomment["refid"]:
            refid = int(usercomment["refid"])
            refcomment = Comment.get_by_id(refid)
            if refcomment:
                to = refcomment.nickname
        post = Post.query.filter_by(post_id=int(post_id)).first()
        if not post or post.allow_visit is False:
            return json.dumps({'has_error': True, "message": "文章不存在"})
        elif post.allow_comment is False:
            return json.dumps({"has_error": True, "message": "不允许评论"})
        comment = Comment(
            post_id=post.post_id,
            url=post.url,
            email=email,
            nickname=nickname,
            content=unquote(content),
            to=to,
            refid=refid,
            create_time=datetime.now(),
            ip=request.remote_addr,
            website=website)
        comment.save()

        # keep username, website, email to session
        session.expire = False
        session["nickname"] = nickname
        session["website"] = website
        session["email"] = email

        return jsonify(success=True, message="success")


@frontend.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "username" in session:
            return redirect(url_for("admin.setting"))
        return render_template("login.html")

    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if not username.strip() or not password:
            flash("用户名密码错误")
            return redirect(url_for('.login'))

        user = User.get_by_name(username.split()[0])
        if not user or not user.validate(password):
            flash("用户名密码错误")
            return redirect(url_for('.login'))

        session["is_admin"] = True
        session["username"] = username
        return redirect(url_for("admin.setting"))


@frontend.route("/logout", methods=["GET"])
def logout():
    session.pop("username", None)
    session.pop("is_admin", None)

    return redirect(url_for(".index"))
