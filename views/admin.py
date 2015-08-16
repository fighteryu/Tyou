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
from models import Post, Comment, Link, Media, User
from helpers import gen_pager
from decorators import admin_required

adminor = Blueprint('admin', __name__, template_folder="../templates")


@adminor.route("/postlist")
@adminor.route('/postlist/<int:page>')
@admin_required
def adminpostlist(page=1):
    perpage = g.config["ADMIN_ITEM_COUNT"]
    args = request.args
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

    postlist = Post.get_page(
        offset=(page-1)*perpage,
        limit=perpage,
        **kargs)

    pager = gen_pager(Post.count(**kargs),
                      g.config["ADMIN_ITEM_COUNT"],
                      page)
    return render_template('admin/postlist.html',
                           postlist=postlist,
                           admin_url="pagelist",
                           pager=pager,
                           parameter=request.query_string)


@adminor.route("/post/inplace")
@admin_required
def pageinplace():
    """Check if a url is in place
    """
    url = request.args["url"]
    post_id = int(request.args["post_id"])
    post = Post.get_by_url(url=url)

    # same post or the post doesn't exist
    if (post and post.post_id == post_id) or (not post):
        return jsonify(success=True,
                       in_place=False)
    else:
        return jsonify(success=True,
                       in_place=True)


@adminor.route("/post", methods=["GET", "POST", "DELETE"])
@adminor.route("/post/<int:post_id>", methods=["GET", "POST", "DELETE"])
@admin_required
def editpost(post_id=None):
    """show the edit page, update the post
    """
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
@admin_required
def overview(post_id=-1):
    post = Post.get_by_id(post_id=post_id, public_only=False)
    if post:
        return render_template('page.html',
                               admin_url="overview",
                               post=post)
    else:
        abort(404)


@adminor.route("/linkmgnt")
@adminor.route("/linkmgnt/<int:page>")
@admin_required
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

        user = User.get_one()
        user.config = json.dumps(new_config)
        user.save()
        return redirect(url_for("admin.setting"))


@adminor.route('/mediamgnt', methods=['GET'])
@adminor.route('/mediamgnt/<int:page>', methods=["GET"])
@admin_required
def mediamgnt(page=1):
    per_page = g.config["ADMIN_ITEM_COUNT"]
    medialist = Media.get_page(per_page*(page-1), per_page)
    pager = gen_pager(
        Media.count(),
        per_page,
        page)
    return render_template('admin/mediamgnt.html',
                           admin_url="mediamgnt",
                           medialist=medialist,
                           pager=pager
                           )


@adminor.route('/commentmgnt', methods=["GET"])
@adminor.route('/commentmgnt/<int:page>')
@admin_required
def commentmgnt(page=1):
    if request.method == "GET":
        per_page = g.config["ADMIN_ITEM_COUNT"]
        if 'post_id' in request.args:
            post_id = request.args['post_id']
            commentlist = Comment.get_page(
                offset=per_page*(page-1),
                limit=per_page,
                post_id=post_id)
            pager = gen_pager(Comment.count(post_id), per_page, page)
        else:
            commentlist = Comment.get_page(
                offset=per_page*(page-1),
                limit=per_page)
            pager = gen_pager(Comment.count(), per_page, page)
        return render_template('admin/commentmgnt.html',
                               commentlist=commentlist,
                               admin_url="commentmgnt",
                               pager=pager)


@adminor.route("/export", methods=["GET"])
@admin_required
def export_blog():
    postlist = Post.query.all()
    linklist = Link.query.all()
    medialist = Media.query.all()

    ex_post = []
    for post in postlist:
        # Back up all comments
        ex_comment = []
        commentlist = Comment.get_by_post_id(post.post_id)
        for comment in commentlist:
            ex_comment.append({
                "comment_id": comment.comment_id,
                "post_id": comment.post_id,
                "url": comment.url,
                "email": comment.email,
                "nickname": comment.nickname,
                "content": comment.content,
                "to": comment.to,
                "refid": comment.refid,
                "create_time": int(comment.create_time.strftime("%s")),
                "ip": comment.ip,
                "website": comment.website
            })

        ex_post.append({
            "post_id": post.post_id,
            "url": post.url,
            "title": post.title,
            "content": post.content,
            "keywords": post.keywords,
            "metacontent": post.metacontent,
            "create_time": int(post.create_time.strftime("%s")),
            "update_time": int(post.update_time.strftime("%s")),
            "tags": post.tags,
            "allow_visit": post.allow_visit,
            "allow_comment": post.allow_comment,
            "need_key": post.need_key,
            "is_original": post.is_original,
            "num_lookup": post.num_lookup,
            "commentlist": ex_comment
        })

    # Backup all links
    ex_link = []
    for link in linklist:
        ex_link.append({
            "link_id": link.link_id,
            "name": link.name,
            "href": link.href,
            "description": link.description,
            "create_time": int(link.create_time.strftime("%s")),
            "display": link.display,
        })

    # Backup all media
    ex_media = []
    for media in medialist:
        ex_media.append({
            "fileid": media.fileid,
            "filename": media.filename,
            "version": media.version,
            "content_type": media.content_type,
            "size": media.size,
            "create_time": int(media.create_time.strftime("%s")),
            "display": media.display
        })

    data = json.dumps(
        {
            "site": request.url_root,
            "links": ex_link,
            "posts": ex_post,
            "medias": ex_media
        },
        sort_keys=True,
        indent=4,
        separators=(',', ': '))

    # compress data and send as zip
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
        data = json.load(f.stream)
        links = data.pop("links", [])
        medias = data.pop("medias", [])
        posts = data.pop("posts", [])

        for link in links:
            new_link = Link.get_by_href(link["href"])
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
            new_media = Media.get_by_fileid(media["fileid"])
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
            new_post = Post.get_by_url(post["url"], public_only=False)
            if new_post:
                continue
            else:
                new_post = Post()

            for item in post:
                new_post.__dict__[item] = post[item]
            new_post.post_id = None
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
                new_comment.post_id = new_post.post_id
                new_comment.comment_id = None
                new_comment.create_time = \
                    datetime.fromtimestamp(new_comment.create_time)
                new_comment.save()

    except Exception as e:
        return str(e)

    return "Done"
