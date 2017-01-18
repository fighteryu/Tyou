#!/usr/bin/env python
# coding:utf-8
"""
    views: link.py
    ~~~~~~~~~~~~~

"""
from flask import Blueprint, request, jsonify
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
    print(removelist)
    for link_id in removelist:
        link = Link.get_link(id=link_id)
        if link:
            link.delete()
    return jsonify(success=True, message="success")


@link.route("/reverse", methods=['POST'])
def reverse():
    reverselist = request.json
    for link_id in reverselist:
        link = Link.get_link(link_id=link_id)
        if link:
            link.display = not link.display
            link.save()
    return jsonify(success=True, message="success")
