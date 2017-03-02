#!/usr/bin/env python
# coding: utf-8
"""
    frontend.py
    ~~~~~~~~~~~~~

"""
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
    count, posts = Post.get_page(page, Post.allow_visit == True, order_by=-Post.id)
    pager = gen_pager(page, count, g.config["PER_PAGE"], request.url)
    if posts or page == 1:
        return render_template(
            "index.html",
            blogname=g.config["BLOGNAME"],
            posts=posts,
            pager=pager)
    else:
        return render_template("error/404.html")


@frontend.route('/page/<url>')
def page(url=None):
    """display post"""
    post = Post.get_one(Post.url == url)
    if not post or not post.allow_visit:
        abort(404)

    comments = Comment.get_list(Comment.post_id == post.id).order_by(-Comment.id)
    return render_template(
        'page.html',
        blogname=g.config["BLOGNAME"],
        post=post,
        comments=comments)


@frontend.route("/key", methods=["POST"])
@frontend.route("/key/", methods=["POST"])
def key():
    data = request.json
    post = Post.get_one(Post.url == data.get("posturl", ""))
    if not post:
        return jsonify(
            validate=False,
            error=True,
            message="Post doesn't exists"
        )

    post_password = post.password or g.config.get("POST_PASSWORD", "")
    if post_password != data.get("post_password", None):
        return jsonify(validate=False, error=True, message=u"Password error!")

    else:
        return jsonify(validate=True, error=False, message=post.content)


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
        parent_comment_id = None
        to = None
        if usercomment.get("parent_comment_id", None):
            parent_comment_id = int(usercomment["parent_comment_id"])
            parent_comment = Comment.get_one(Comment.id == parent_comment_id)
            if parent_comment:
                to = parent_comment.nickname
        post = Post.get_one(Post.id == post_id)
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
            parent_comment_id=parent_comment_id,
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

        user = User.get_one(User.username == username.split()[0])
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
