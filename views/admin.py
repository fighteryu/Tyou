#!/usr/bin/env python
# coding: utf-8
"""
    admin.py
    ~~~~~~~~~~

"""
import re
import json
from datetime import datetime
from flask import Blueprint, render_template, g, request, abort, jsonify,\
    redirect, url_for, send_file
from models import Post, Comment, Link, Media, User, db
from helpers import gen_pager
from decorators import admin_required

adminor = Blueprint('admin', __name__, template_folder="../templates")


@adminor.route("/posts")
@admin_required
def posts():
    perpage = g.config["ADMIN_ITEM_COUNT"]
    args = request.args

    page = int(args.get("page", 1))

    kargs = {}
    if "is_original" in args and args["is_original"] == "true":
        kargs["is_original"] = True
    elif "is_original" in args and args["is_original"] == "false":
        kargs["is_original"] = False

    if "allow_visit" in args and args["allow_visit"] == "true":
        kargs["allow_visit"] = True
    elif "allow_visit" in args and args["allow_visit"] == "false":
        kargs["allow_visit"] = False

    if "allow_comment" in args and args["allow_comment"] == "true":
        kargs["allow_comment"] = True
    elif "allow_comment" in args and args["allow_comment"] == "false":
        kargs["allow_comment"] = False

    posts = Post.get_page(page, order_by=Post.id.desc(), perpage=perpage, **kargs)

    pager = gen_pager(page, Post.count(**kargs), perpage, request.url)
    return render_template('admin/posts.html',
                           posts=posts,
                           admin_url="posts",
                           pager=pager,
                           parameter=request.query_string)


@adminor.route("/post/inplace")
@admin_required
def pageinplace():
    """Check if a url is in place
    """
    url = request.args["url"]
    post_id = request.args.get("post_id", "")
    if post_id.isdigit():
        post_id = int(post_id)
    post = Post.get_post(url=url)

    # same post or the post doesn't exist
    if (post and post.id == post_id) or (not post):
        return jsonify(success=True, in_place=False)
    else:
        return jsonify(success=True, in_place=True)


@adminor.route("/post", methods=["GET", "POST", "DELETE"])
@adminor.route("/post/<int:id>", methods=["GET", "POST", "DELETE"])
@admin_required
def editpost(id=None):
    """show the edit page, update the post
    choice of editor:
        while editing an existing post, use post.editor as the editor
        editing a new post, use request.args["editor"] as the editor
    """
    if request.method == "GET":
        if id is not None:
            post = Post.get_post(id=id)
            editor = post.editor
            if not post:
                abort(404)
        else:
            post = Post()
            editor = request.args.get("editor", "markdown")

        return render_template('admin/editpost.html',
                               admin_url="post_" + editor,
                               post=post,
                               editor=editor)
    elif request.method == "POST":
        data = request.json
        now_time = datetime.now()
        if data['id'] is not None:
            post = Post.get_post(id=int(data["id"]))
        else:
            post = Post()
            post.create_time = now_time
        post.editor = data.get("editor", "markdown")
        post.update_time = now_time
        post.title = data.get("title", "")
        post.update_tags(data.get("tags", ""))
        post.url = data.get("url", "")
        post.keywords = data.get("keywords", "")
        post.metacontent = data.get("metacontent", "")
        post.content = data.get("content", "")
        post.raw_content = Post.gen_raw_content(post.content, post.editor)
        post.allow_comment = data.get("allow_comment", True)
        post.allow_visit = data.get("allow_visit", True)
        post.is_original = data.get("is_original", True)
        post.need_key = data.get("need_key", False)
        post.password = data.get("password", "")
        db.session.add(post)
        db.session.commit()
        return jsonify(success=True, id=post.id)

    elif request.method == "DELETE":
        # Delete post by id
        if id is not None:
            post = Post.get_post(id=int(id))
            if post:
                post.delete()
        # Batch Delete method
        else:
            removelist = request.json
            for post_id in removelist:
                post = Post.get_post(id=post_id)
                if post:
                    post.delete()
        return jsonify(success=True)


@adminor.route('/overview/<int:post_id>/')
@admin_required
def overview(post_id=-1):
    post = Post.get_post(id=post_id)
    if post:
        return render_template('page.html', admin_url="overview", post=post)
    else:
        abort(404)


@adminor.route("/links")
@admin_required
def links():
    perpage = g.config["ADMIN_ITEM_COUNT"]
    page = int(request.args.get("page", 1))
    linklist = Link.get_page(page, perpage=perpage)
    pager = gen_pager(page, Link.count(), perpage, request.url)
    return render_template('admin/links.html',
                           linklist=linklist,
                           admin_url="links",
                           pager=pager
                           )


@adminor.route("")
@adminor.route("/")
@adminor.route('/setting', methods=['GET', 'POST'])
@admin_required
def setting():
    if request.method == "GET":
        return render_template(
            "admin/setting.html",
            admin_url="setting",
            config=g.config)

    elif request.method == "POST":
        new_config = {}
        for item in request.form:
            if request.form[item].strip():
                try:
                    new_config[item] = int(request.form[item])
                except Exception:
                    new_config[item] = request.form[item]

        # blog url ends with slash
        new_config["BLOGURL"] = request.form.get("BLOGURL", "")
        if not new_config["BLOGURL"].endswith("/"):
            new_config["BLOGURL"] += "/"

        user = User.get_users().first()
        user.config = json.dumps(new_config)
        user.save()
        return redirect(url_for("admin.setting"))


@adminor.route('/medias', methods=['GET'])
@admin_required
def medias():
    page = int(request.args.get("page", 1))
    perpage = g.config["ADMIN_ITEM_COUNT"]
    medias = Media.get_page(page, order_by=Media.id.desc(), perpage=perpage)
    pager = gen_pager(page, Media.count(), perpage, request.url)
    return render_template('admin/medias.html',
                           admin_url="medias",
                           medias=medias,
                           pager=pager)


@adminor.route('/comments', methods=["GET"])
@admin_required
def comments():
    if request.method == "GET":
        page = int(request.args.get("page", 1))
        perpage = g.config["ADMIN_ITEM_COUNT"]
        if 'post_id' in request.args:
            post_id = request.args['post_id']
            comments = Comment.get_page(
                page, post_id=post_id, order_by=Comment.id.desc(), perpage=perpage
            )
            pager = gen_pager(page, Comment.count(post_id), perpage, request.url)
        else:
            comments = Comment.get_page(page, order_by=Comment.id.desc())
            pager = gen_pager(page, Comment.count(), perpage, request.url)
        return render_template('admin/comments.html',
                               comments=comments,
                               admin_url="comments",
                               pager=pager)


@adminor.route("/export", methods=["GET"])
@admin_required
def export_blog():
    # compress data and send as zip
    from models import export_all
    data = export_all()
    from io import BytesIO
    import zipfile
    filename = g.config["BLOGNAME"] + datetime.now().strftime("%Y%m%d%H%M")
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        zf.writestr(filename + ".json", data)
    memory_file.seek(0)
    return send_file(memory_file,
                     attachment_filename=filename + ".zip", as_attachment=True)


@adminor.route("/import", methods=["POST"])
def import_blog():
    f = request.files["file"]

    try:
        data = f.stream.read().decode("utf-8")
        data = json.loads(data)
        links = data.pop("links", [])
        medias = data.pop("medias", [])
        posts = data.pop("posts", [])

        for link in links:
            new_link = Link.get_link(href=link["href"])
            if new_link:
                continue
            else:
                new_link = Link()

            for item in link:
                new_link.__dict__[item] = link[item]
            new_link.link_id = None
            new_link.create_time = \
                datetime.fromtimestamp(new_link.create_time)
            new_link.save()

        for media in medias:
            new_media = Media.get_media(fileid=media["fileid"])
            if new_media:
                continue
            else:
                new_media = Media()

            for item in media:
                new_media.__dict__[item] = media[item]

            # Notice, media id should not be set to None
            new_media.media_id = None
            new_media.create_time = \
                datetime.fromtimestamp(new_media.create_time)
            new_media.save()

        for post in posts:
            # If posts exist, continue
            new_post = Post.get_post(url=post["url"])
            if new_post:
                continue
            else:
                new_post = Post()

            for item in post:
                new_post.__dict__[item] = post[item]
            new_post.id = None
            new_post.create_time = \
                datetime.fromtimestamp(new_post.create_time)
            new_post.update_time = \
                datetime.fromtimestamp(new_post.update_time)

            new_post.raw_content = re.sub('<[^<]+?>', "", new_post.content)
            newtags = new_post.tags
            new_post.tags = ""
            new_post.update_tags(newtags)
            new_post.save()

            # Restore all posts
            comments = post["commentlist"]
            for comment in comments:
                new_comment = Comment()
                for item in comment:
                    new_comment.__dict__[item] = comment[item]
                new_comment.post_id = new_post.id
                new_comment.comment_id = None
                new_comment.create_time = \
                    datetime.fromtimestamp(new_comment.create_time)
                new_comment.save()
    except Exception as e:
        return str(e)

    return "Done"
