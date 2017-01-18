#!/usr/bin/env python
# coding:utf-8
"""
    media.py
    ~~~~~~~~~~~~~

"""
import os
import json
from datetime import datetime
import hashlib
from flask import Blueprint, request, abort, jsonify,\
    send_from_directory, current_app

from models import Media

media = Blueprint('media', __name__, template_folder="../templates")


@media.route("", methods=["POST", "GET", "DELETE"])
@media.route("/<filename>", methods=["POST", "GET", "DELETE"])
def medias(filename=None):
    if request.method == "GET":
        media = Media.get_media(filename=filename)
        if not media:
            abort(404)
        return send_from_directory(
            current_app.config["UPLOAD_FOLDER"],
            media.filename
        )

    elif request.method == "POST":
        f = request.files["files[]"]
        if not f:
            return

        filename = f.filename
        filepath = os.path.join(
            current_app.config['UPLOAD_FOLDER'], filename)
        f.save(filepath)
        filesize = os.stat(filepath).st_size

        now = datetime.now()
        media = Media(
            fileid=hashlib.sha256(filename.encode("utf-8")).hexdigest(),
            filename=filename,
            version=0,
            content_type=f.content_type,
            size=filesize,
            create_time=now,
            display=True
        )

        media.save()
        return json.dumps(
            {"files": []})

    elif request.method == "DELETE":
        removelist = request.json
        for eachfile in removelist:
            fileid = eachfile["fileid"]
            filename = eachfile["filename"]
            onemedia = Media.get_media(fileid=fileid)
            if onemedia.filename != filename:
                continue
            onemedia.delete()
        return jsonify(
            success=True,
            message="success")


@media.route("/reverse", methods=['POST'])
def reverse():
    reverselist = request.json
    for item in reverselist:
        media = Media.get_media(fileid=item["fileid"])
        if media:
            media.display = not media.display
            media.save()
    return jsonify(success=True,
                   message="success")
