#!/usr/bin/env python
# coding:utf-8
"""
    search.py
    ~~~~~~~~~~~~~

"""
from flask import Blueprint, render_template, request, g
from models import Post
from helpers import gen_pager

makesearch = Blueprint('search', __name__, template_folder="../templates")


@makesearch.route('')
@makesearch.route('/')
def dosearch(page=1):
    page = int(request.args.get("page", 1))
    # Tag search
    if "tagname" in request.args:
        tagname = request.args.get("tagname").strip()
        count, posts = Post.tag_search(
            keyword=tagname,
            offset=g.config["PER_PAGE"] * (page-1),
            limit=g.config["PER_PAGE"]
        )

        pager = gen_pager(page, count, g.config["PER_PAGE"], request.url)
        return render_template(
            "search.html",
            searchtype="tagsearch",
            searchcontent=tagname,
            pager=pager,
            posts=posts,
            parameter=request.query_string)

    # Text search
    if 'keyword' in request.args:
        words = request.args["keyword"].split()
        # In case a query with too much keywords
        words = [word for word in words if len(word) >= 2]
        if len(words) == 0:
            posts = []
            count = 0
        else:
            count, posts = Post.text_search(
                words=words,
                offset=g.config["PER_PAGE"]*(page-1),
                limit=g.config["PER_PAGE"]
            )

        pager = gen_pager(page, count, g.config["PER_PAGE"], request.url)
        return render_template(
            'search.html',
            searchtype="textsearch",
            searchcontent=" ".join(words),
            posts=posts,
            pager=pager,
            parameter=request.query_string)
