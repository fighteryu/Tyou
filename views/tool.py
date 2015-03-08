from flask import Blueprint, render_template

tool = Blueprint('tool', __name__, template_folder="../templates")


@tool.route("/weather")
def weather():
    return render_template('frozen/weather.html')


@tool.route("/qrcode")
def qrcode():
    return render_template("frozen/qrcode.html")


@tool.route("/markdown")
def markdown():
    return render_template("frozen/markdown.html")
