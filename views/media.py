#!/usr/bin/env python
# coding:utf-8
"""
    media.py
    ~~~~~~~~~~~~~

"""
import os
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
        # save file to local folder, if file exists, delete it
        filepath = os.path.join(
            current_app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        f.save(filepath)
        filesize = os.stat(filepath).st_size

        now = datetime.now()
        # if file with same name exists, replace it
        media = Media.get_one(Media.filename == filename)
        if not media:
            media = Media(
                filename=filename
            )
        media.fileid = hashlib.sha256(filename.encode("utf-8")).hexdigest()
        media.size = filesize
        media.content_type = f.content_type
        media.size = filesize
        media.create_time = now
        media.save()
        return jsonify(
            {"files": []})

    elif request.method == "DELETE":
        removelist = request.json
        for eachfile in removelist:
            fileid = eachfile["fileid"]
            filename = eachfile["filename"]
            onemedia = Media.get_one(Media.fileid == fileid)
            if onemedia.filename != filename:
                continue

            # remove file from folder
            try:
                os.remove(onemedia.filepath(current_app.config["UPLOAD_FOLDER"]))
            except Exception:
                pass
            # remove file from database
            onemedia.delete_instance()
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
