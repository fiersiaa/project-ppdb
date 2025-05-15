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
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.index'))
    return redirect(url_for('auth_bp.login'))

@main_bp.route("/dashboard")
@login_required
def index():
    return render_template("index.html", title="Halaman Utama PPDB")

@main_bp.route("/daftar", methods=['GET', 'POST'])
@login_required
def daftar():
    try:
        # Check if user already registered
        existing_pendaftaran = Pendaftaran.query.filter_by(user_id=current_user.id).first()
        if existing_pendaftaran:
            flash('Anda sudah melakukan pendaftaran.', 'warning')
            return redirect(url_for('main_bp.index'))

        if request.method == 'POST':
            try:
                logger.debug(f"Processing registration for user: {current_user.username}")
                logger.debug(f"Form data: {request.form}")

                # Create new registration
                pendaftaran = Pendaftaran(
                    nama_lengkap=request.form.get('nama_lengkap'),
                    tempat_lahir=request.form.get('tempat_lahir'),
                    tanggal_lahir=datetime.strptime(request.form.get('tanggal_lahir'), '%Y-%m-%d'),
                    jenis_kelamin=request.form.get('jenis_kelamin'),
                    alamat=request.form.get('alamat'),
                    nomor_hp=request.form.get('nomor_hp'),
                    asal_sekolah=request.form.get('asal_sekolah'),
                    nilai_un=float(request.form.get('nilai_un')),
                    user_id=current_user.id,
                    status='Pending'
                )

                db.session.add(pendaftaran)
                db.session.commit()
                logger.info(f"Registration successful for user: {current_user.username}")
                
                flash('Pendaftaran berhasil dikirim!', 'success')
                return redirect(url_for('main_bp.index'))

            except ValueError as e:
                logger.error(f"Value Error: {str(e)}")
                db.session.rollback()
                flash('Format data tidak valid. Silakan periksa kembali isian Anda.', 'danger')
            
            except Exception as e:
                logger.error(f"Error saving registration: {str(e)}")
                db.session.rollback()
                flash('Terjadi kesalahan saat menyimpan data. Silakan coba lagi.', 'danger')

    except Exception as e:
        logger.error(f"General error: {str(e)}")
        flash('Terjadi kesalahan sistem. Silakan coba lagi nanti.', 'danger')

    # For GET request or if there were errors
    return render_template('daftar.html', 
                         title="Formulir Pendaftaran PPDB",
                         now=datetime.now())  # Pass current date for date input max value