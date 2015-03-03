#!/usr/bin/env python
# coding:utf-8
"""
	views: link.py
	~~~~~~~~~~~~~

"""

import json
import time
import datetime
from flask import Blueprint, request, jsonify, g, current_app,abort
from models import Link
link = Blueprint('link', __name__, template_folder="../templates")


@link.route("/", methods=["POST", "DELETE", "PUT"])
def index():
    link = request.json
    newlink = Link()
    newlink.name = link["name"]
    newlink.href = link["href"]
    newlink.display = link["display"]
    newlink.description = link["description"]
    newlink.create_time = datetime.datetime.now()
    newlink.save()
    return jsonify(success=True,
                   message="success")


@link.route("/delete", methods=['POST'])
def mydelete():
    removelist = request.json
    for item in removelist:
        link = Link.get_by_id(item)
        if link:
            link.delete()
    return jsonify(success=True,
                   message="success")


@link.route("/reverse", methods=['POST'])
def reverse():
    reverselist = request.json
    for item in reverselist:
        link = Link.get_by_id(item)
        if link:
            link.display = not link.display
            link.save()
    return jsonify(success=True,
                   message="success")
