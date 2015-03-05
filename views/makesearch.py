#!/usr/bin/env python
# coding:utf-8
"""
    search.py
    ~~~~~~~~~~~~~

"""
from flask import Blueprint, render_template, request, g
from models import Post, gen_sidebar
from helpers import gen_pager

makesearch = Blueprint('search', __name__, template_folder="../templates")


@makesearch.route('')
@makesearch.route('/')
@makesearch.route('/<int:page>')
def dosearch(page=1):
    sidebar = gen_sidebar(g.config)
    # Tag search
    if "tagname" in request.args:
        tagname = request.args.get("tagname").strip()
        # Defence of SQL injection
        if " " in tagname or tagname == "":
            postlist = []
            count = 0
        else:
            postlist = Post.tag_search(
                keyword=tagname,
                offset=g.config["PER_PAGE"] * (page-1),
                limit=g.config["PER_PAGE"]
            )
            count = Post.tag_search_count(tagname)

        pager = gen_pager(count, g.config["PER_PAGE"], page)
        return render_template(
            "search.html",
            searchtype="tagsearch",
            searchcontent=tagname,
            sidebar=sidebar,
            pager=pager,
            postlist=postlist,
            parameter=request.query_string)

    # Text search
    if 'keyword' in request.args:
        words = request.args["keyword"].split()
        # In case a query with too much keywords
        words = [word for word in words if len(word) >= 2]
        if len(words) > 5 or len(words) == 0:
            postlist = []
            count = 0
        else:
            postlist = Post.text_search(
                words=words,
                offset=g.config["PER_PAGE"]*(page-1),
                limit=g.config["PER_PAGE"]
            )
            count = Post.text_search_count(words=words)

        pager = gen_pager(count, g.config["PER_PAGE"], page)
        return render_template(
            'search.html',
            searchtype="textsearch",
            searchcontent=" ".join(words),
            postlist=postlist,
            sidebar=sidebar,
            pager=pager,
            parameter=request.query_string)
