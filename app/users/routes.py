from flask import Blueprint, render_template

users_bp = Blueprint("users", __name__, url_prefix="/users")

@users_bp.route("/")
def users_page():
    return render_template("users.html")
