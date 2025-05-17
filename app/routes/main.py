from flask import Blueprint, redirect, url_for, render_template, flash, request
from datetime import datetime
from ..models import Pendaftaran
from .. import db
from flask_login import login_required, current_user
import logging

logger = logging.getLogger(__name__)

main_bp = Blueprint('main_bp', __name__)

@main_bp.route("/")
def home():
    return render_template("index.html", title="Halaman Utama PPDB")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_bp.dashboard_admin'))
        return render_template("index.html", title="Dashboard PPDB")
    return redirect(url_for('auth_bp.login'))

@main_bp.route("/daftar", methods=['GET', 'POST'])
@login_required
def daftar():
    try:
        # Check if user already registered
        existing = Pendaftaran.query.filter_by(user_id=current_user.id).first()
        if existing:
            flash('Anda sudah melakukan pendaftaran', 'warning')
            return redirect(url_for('main_bp.home'))

        if request.method == 'POST':
            try:
                # Create new registration
                pendaftaran = Pendaftaran(
                    nama_lengkap=request.form['nama_lengkap'],
                    tempat_lahir=request.form['tempat_lahir'],
                    tanggal_lahir=datetime.strptime(request.form['tanggal_lahir'], '%Y-%m-%d'),
                    jenis_kelamin=request.form['jenis_kelamin'],
                    alamat=request.form['alamat'],
                    nomor_hp=request.form['nomor_hp'],
                    asal_sekolah=request.form['asal_sekolah'],
                    nilai_un=float(request.form['nilai_un']),
                    user_id=current_user.id,
                    status='Pending'
                )

                # Save to database
                db.session.add(pendaftaran)
                db.session.commit()
                logger.info(f"Registration successful for user: {current_user.username}")

                flash('Pendaftaran berhasil dikirim!', 'success')
                return redirect(url_for('main_bp.home'))

            except Exception as e:
                db.session.rollback()
                logger.error(f"Registration error: {str(e)}")
                flash('Terjadi kesalahan saat mendaftar. Silakan coba lagi.', 'danger')
                
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        flash('Terjadi kesalahan sistem. Silakan coba lagi nanti.', 'danger')

    return render_template('daftar.html', 
                         title="Formulir Pendaftaran PPDB",
                         now=datetime.now())

@main_bp.route("/detail-pendaftaran")
@login_required
def detail_pendaftaran():
    pendaftaran = Pendaftaran.query.filter_by(user_id=current_user.id).first()
    if not pendaftaran:
        flash('Anda belum melakukan pendaftaran', 'warning')
        return redirect(url_for('main_bp.daftar'))
    
    return render_template('detail_pendaftaran.html', 
                         title="Detail Pendaftaran",
                         pendaftaran=pendaftaran)