#!/usr/bin/env python
# coding: utf-8
# Author: fzlee
# Created Time : 2014/12/14 22:37

# File Name: app.py

from flask import Flask, g, request, jsonify, render_template

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

    @app.before_request
    def get_config():
        g.config = User.get_config() or app.config


def configure_errorhandlers(app):
    @app.errorhandler(404)
    def page_not_found(error):
        if request.is_xhr:
            return jsonify(error='Sorry, page not found')
        sidebar = gen_sidebar(app.config)
        return render_template(
            "error/404.html",
            sidebar=sidebar,
            error=error), 404

    @app.errorhandler(500)
    def server_error(error):
        if request.is_xhr:
            return jsonify(error='Sorry, an error has occurred')
        return render_template("error/500.html", error=error), 500


app = createapp()


if __name__ == "__main__":
    app.run()
