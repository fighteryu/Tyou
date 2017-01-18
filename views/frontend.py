#!/usr/bin/env python
# coding: utf-8
"""
    frontend.py
    ~~~~~~~~~~~~~

"""
import random

from flask import request, jsonify, g, abort, render_template,\
    flash, redirect, url_for, session

from models import Post, Comment, User, Fail
from helpers import gen_pager
from .other import frontend
from compat import unquote


@frontend.route('/')
@frontend.route("/index")
def index():
    page = int(request.args.get("page", 1))
    postlist = Post.get_page(page, allow_visit=True)
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
    post = Post.get_post(url=url)
    if post and post.allow_visit:
        comments = Comment.get_comments(post_id=post.id).order_by(Comment.id.desc())
        return render_template(
            'page.html',
            blogname=g.config["BLOGNAME"],
            post=post,
            comments=comments)
    else:
        abort(404)


@frontend.route("/key", methods=["POST"])
@frontend.route("/key/", methods=["POST"])
def key():
    data = request.json
    post = Post.get_post(url=data.get("posturl", ""))
    if not post:
        return jsonify(
            validate=False,
            error=True,
            message="Post doesn't exists"
        )

    validate_result = Fail.validate_client(request.remote_addr)
    if validate_result is False:
        return jsonify(
            validate=False,
            error=True,
            message="Please wait for a few seconds and try later"
        )

    post_password = post.password or g.config.get("POST_PASSWORD", "")
    if post_password != data.get("post_password", None):
        record = Fail.add_record(request.remote_addr, post.post_id)
        # There is a chance in which users in put wrong password for quite a
        # few times, and we direct them to a random page
        if record.is_above_threshold() and random.randint(1, 5) % 5 == 0:
            return jsonify(validate=True,
                           error=False,
                           message=Post.random_post().content
                           )

        return jsonify(
            validate=False,
            error=True,
            message=u"Password error!")

    else:
        Fail.clear_record(request.remote_addr, post.post_id)
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
        for comment_id in removelist:
            comment = Comment.get_comment(id=comment_id)
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
        if usercomment.get("refid", None):
            refid = int(usercomment["refid"])
            refcomment = Comment.get_comment(refid=refid)
            if refcomment:
                to = refcomment.nickname
        post = Post.query.filter_by(id=post_id).first()
        if not post or post.allow_visit is False:
            return jsonify(has_error=True, message="文章不存在")
        elif post.allow_comment is False:
            return jsonify(has_error=True, message="不允许评论")
        comment = Comment(
            post_id=post.id,
            email=email,
            nickname=nickname,
            content=unquote(content),
            to=to,
            refid=refid,
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

        user = User.get_user(username=username.split()[0])
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
