from flask import Blueprint, redirect, url_for, render_template
from flask_login import login_required, current_user

main_bp = Blueprint('main_bp', __name__)

@main_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.index'))
    return redirect(url_for('auth_bp.login'))

@main_bp.route("/dashboard")
@login_required
def index():
    return render_template("index.html", title="Halaman Utama PPDB")