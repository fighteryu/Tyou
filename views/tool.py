from flask import Blueprint, render_template, current_app
from models import gen_sidebar

tool = Blueprint('tool', __name__, template_folder="../templates")


@tool.route("/weather")
def weather():
    sidebar = gen_sidebar(current_app.config)
    return render_template('frozen/weather.html',
                           sidebar=sidebar)


@tool.route("/qrcode")
def qrcode():
    sidebar = gen_sidebar(current_app.config)
    return render_template("frozen/qrcode.html",
                           sidebar=sidebar)
