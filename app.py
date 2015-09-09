#!/usr/bin/env python
# coding: utf-8
# Author: fzlee
# Created Time : 2014/12/14 22:37

# File Name: app.py
import sys
for i in sys.path:
    print i
reload(sys)
# sys.setdefaultencoding("utf8")

import os
from flask import Flask, g, request, jsonify, render_template, session
import config
from models import db, gen_sidebar, User
from views import MODULES


def createapp():
    app = Flask('Tyou')
    app.config.from_object(config)
    configure_jinja_filter(app)
    configure_modules(app)
    configure_db(app)
    configure_before_handlers(app)
    configure_errorhandlers(app)
    return app


def configure_jinja_filter(app):
    import urllib

    @app.template_filter('urlencode')
    def urlencode(uri, **query):
        return urllib.quote(uri.encode('utf-8'))
    app.jinja_env.globals['urlencode'] = urlencode


def configure_modules(app):
    for item in MODULES:
        app.register_blueprint(item[0], url_prefix=item[1])


def configure_db(app):
    db.init_app(app)


def configure_before_handlers(app):
    @app.before_first_request
    def init_db():
        db.create_all()

    @app.before_first_request
    def create_upload_folder():
        if not os.path.exists(app.config["UPLOAD_FOLDER"]):
            os.makedirs(app.config["UPLOAD_FOLDER"])

    @app.before_request
    def init_setup():
        session.permanent = True
        g.config = User.get_config() or app.config
        g.sidebar = gen_sidebar(g.config)


def configure_errorhandlers(app):
    @app.errorhandler(404)
    def page_not_found(error):
        if request.is_xhr:
            return jsonify(error='Sorry, page not found')
        return render_template(
            "error/404.html",
            error=error), 404

    @app.errorhandler(500)
    def server_error(error):
        if request.is_xhr:
            return jsonify(error='Sorry, an error has occurred')
        return render_template("error/500.html", error=error), 500


def register_manage_command(app):
    """functions for commandline useage
    """
    def backup_blog():
        ctx = app.test_request_context()
        ctx.push()
        app.preprocess_request()

        # export and write to uploads folder
        from config import UPLOAD_FOLDER
        from models import export_all
        data = export_all()
        import zipfile
        import datetime
        z = zipfile.ZipFile(os.path.join(UPLOAD_FOLDER, "Blogbackup.zip"),
                            'w', zipfile.ZIP_DEFLATED)
        z.writestr(datetime.datetime.now().strftime("%Y%m%d%H%M.json"), data)
        z.close()

        ctx.pop()

    app.cli_backup_blog = backup_blog
    return app


app = createapp()


if __name__ == "__main__":
    app.run(host="0.0.0.0")
