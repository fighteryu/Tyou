#!/usr/bin/env python
# coding: utf-8
# Author: fzlee
# Created Time : 2014/12/14 22:37

# File Name: app.py
import os

import click
from flask import Flask, g, request, jsonify, render_template, session

import config
from models import db, gen_sidebar, User
from views import MODULES
from compat import quote


def createapp():
    app = Flask(__name__)
    app.config.from_object(config)
    configure_jinja_filter(app)
    configure_modules(app)
    configure_db(app)
    configure_before_handlers(app)
    configure_after_handlers(app)
    configure_errorhandlers(app)
    register_manage_command(app)
    return app


def configure_jinja_filter(app):

    @app.template_filter('urlencode')
    def urlencode(uri, **query):
        return quote(uri.encode('utf-8'))
    app.jinja_env.globals['urlencode'] = urlencode


def configure_modules(app):
    for item in MODULES:
        app.register_blueprint(item[0], url_prefix=item[1])


def configure_db(app):
    db.init_app(app)

    @app.teardown_appcontext
    def shutdown_sesion(exception=None):
        db.session.remove()


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
        g.version = version
        # 对于静态页面，不加载数据
        if request.endpoint in ("static", "media.medias"):
            return

        session.permanent = True
        g.config = User.get_config() or app.config

        # 避免非页面请求生成了sidebar
        if request.method != "GET":
            return

        g.sidebar = gen_sidebar(g.config)


def configure_after_handlers(app):

    @app.after_request
    def auto_commit(response):
        db.session.commit()
        return response


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
    @app.cli.command()
    def backup_blog():
        """
        backup blog
        """
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

    @app.cli.command()
    @click.option("--username", prompt=True)
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
    def create_user(*args, **kwargs):
        """
        create user
        """
        User.create_user(kwargs["username"], kwargs["password"])
        print("create user done")

    @app.cli.command()
    @click.option("--username", prompt=True, confirmation_prompt=True)
    def delete_user(*args, **kwargs):
        """delete current user, blog posts won't be deleted
        """
        User.delete_user(kwargs["username"])
        print("delete user done")

    return app


def get_project_version():
    """
    append version to g, so that we can link css like main.css?ver={{g.version}}
    """
    import subprocess
    return subprocess.check_output(["git", "rev-parse", "HEAD"])[:6].decode("utf-8")


app = createapp()
version = get_project_version()


if __name__ == "__main__":
    app.run(host="0.0.0.0")
