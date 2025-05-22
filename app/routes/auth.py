from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from ..models import User
from .. import db
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_bp.dashboard_admin'))
        return redirect(url_for('main_bp.home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Admin login check
        if username == "admin" and password == "22":
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                # Create admin user if not exists
                admin = User(
                    username='admin',
                    password=generate_password_hash('22'),
                    is_admin=True
                )
                db.session.add(admin)
                db.session.commit()
                
            login_user(admin)
            flash('Selamat datang, Admin!', 'success')
            return redirect(url_for('admin_bp.dashboard_admin'))
        
        # Regular user login
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main_bp.home'))
        
        flash('Username atau password salah', 'danger')
    
    return render_template('auth/login.html', title="Login")

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.home'))

    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            # Validation
            if not username or not password or not confirm_password:
                flash('Semua field harus diisi', 'danger')
                return redirect(url_for('auth_bp.register'))

            if User.query.filter_by(username=username).first():
                flash('Username sudah digunakan', 'danger')
                return redirect(url_for('auth_bp.register'))

            if password != confirm_password:
                flash('Password dan konfirmasi password tidak cocok', 'danger')
                return redirect(url_for('auth_bp.register'))

            # Create new user
            new_user = User(
                username=username,
                password=generate_password_hash(password, method='sha256')
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            logger.info(f"New user registered: {username}")
            flash('Registrasi berhasil! Silakan login dengan akun Anda.', 'success')
            return redirect(url_for('auth_bp.login'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            flash('Terjadi kesalahan saat mendaftar. Silakan coba lagi.', 'danger')
            return redirect(url_for('auth_bp.register'))

    return render_template('auth/register.html', title="Register")

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah logout.', 'success')
    return redirect(url_for('auth_bp.login'))

