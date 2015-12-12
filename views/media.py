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
def mediamgnt(filename=None):
    if request.method == "GET":
        if "fileid" not in request.args:
            abort(400)
        else:
            media = Media.get_by_id(request.args["fileid"])
            if not media or media.filename != filename:
                abort(404)
            return send_from_directory(
                current_app.config["UPLOAD_FOLDER"],
                media.local_filename
            )

    elif request.method == "POST":
        f = request.files["files[]"]
        if f:
            filename = f.filename
            version = Media.get_version(filename)
            local_filename = Media.new_local_filename(filename, version)
            filepath = os.path.join(
                current_app.config['UPLOAD_FOLDER'], local_filename)
            f.save(filepath)
            filesize = os.stat(filepath).st_size

            now = datetime.now()
            hashstr = local_filename + now.strftime("%Y-%m-%d %H:%M:%S")
            hashstr = hashstr.encode("utf8")
            media = Media(
                fileid=hashlib.sha256(hashstr).hexdigest(),
                filename=filename,
                version=Media.get_version(filename),
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
            onemedia = Media.get_by_id(fileid)
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
        media = Media.get_by_id(item["fileid"])
        if media:
            media.display = not media.display
            media.save()
    return jsonify(success=True,
                   message="success")
