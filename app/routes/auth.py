from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from ..models import User
from .. import db

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            
            # Redirect ke halaman admin jika user adalah admin
            if user.is_admin:
                return redirect(url_for('main_bp.admin'))
            return redirect(url_for('main_bp.index'))
            
        flash('Username atau password salah', 'danger')
    return render_template('login.html', title="Login")

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Check if username exists
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username sudah digunakan. Silakan pilih username lain.', 'danger')
            return redirect(url_for('auth_bp.register'))

        # Validate password confirmation
        if password != confirm_password:
            flash('Password dan konfirmasi password tidak cocok.', 'danger')
            return redirect(url_for('auth_bp.register'))

        # Create new user
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Pendaftaran berhasil! Silakan login.', 'success')
            return redirect(url_for('auth_bp.login'))
        except:
            db.session.rollback()
            flash('Terjadi kesalahan. Silakan coba lagi.', 'danger')
            return redirect(url_for('auth_bp.register'))

    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah logout.', 'success')
    return redirect(url_for('auth_bp.login'))

