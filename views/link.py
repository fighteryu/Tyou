#!/usr/bin/env python
# coding:utf-8
"""
    views: link.py
    ~~~~~~~~~~~~~

"""
from flask import Blueprint, request, jsonify

from signals import signal_update_sidebar
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
    newlink.save()
    return jsonify(success=True, message="success")


@link.route("/delete", methods=['POST'])
def delete():
    removelist = request.json
    for link_id in removelist:
        link = Link.get_one(Link.id == link_id)
        if link:
            link.delete_instance()
    signal_update_sidebar.send()
    return jsonify(success=True, message="success")


@link.route("/reverse", methods=['POST'])
def reverse():
    reverselist = request.json
    for link_id in reverselist:
        link = Link.get_one(Link.id == link_id)
        if link:
            link.display = not link.display
            link.save()

    signal_update_sidebar.send()
    return jsonify(success=True, message="success")
