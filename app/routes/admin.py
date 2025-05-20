from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from ..models import Pendaftaran, User
from .. import db
import logging

# Setup logging
logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin_bp', __name__)

# Custom decorator untuk memastikan hanya admin yang bisa akses
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            logger.warning(f"Unauthorized access attempt by user: {current_user}")
            flash('Anda tidak memiliki akses ke halaman ini', 'danger')
            return redirect(url_for('main_bp.home'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard_admin():
    logger.info(f"Admin {current_user.username} accessing dashboard")
    
    try:
        # Ambil data pendaftaran berdasarkan status
        pending = Pendaftaran.query.filter_by(status='Pending')\
            .order_by(Pendaftaran.tanggal_daftar.desc()).all()
        diterima = Pendaftaran.query.filter_by(status='Diterima')\
            .order_by(Pendaftaran.tanggal_diproses.desc()).all()
        ditolak = Pendaftaran.query.filter_by(status='Ditolak')\
            .order_by(Pendaftaran.tanggal_diproses.desc()).all()
        
        logger.info(f"Found: {len(pending)} pending, {len(diterima)} accepted, {len(ditolak)} rejected")
        
        return render_template('admin/dashboard_admin.html',
                             pending=pending,
                             diterima=diterima,
                             ditolak=ditolak,
                             title="Admin Dashboard")
    except Exception as e:
        logger.error(f"Error in dashboard: {str(e)}")
        flash('Terjadi kesalahan saat memuat data.', 'danger')
        return redirect(url_for('main_bp.home'))

@admin_bp.route('/proses_pendaftaran/<int:id>', methods=['POST'])
@login_required
@admin_required
def proses_pendaftaran(id):
    logger.info(f"Processing application {id} by admin {current_user.username}")
    
    try:
        pendaftaran = Pendaftaran.query.get_or_404(id)
        aksi = request.form.get('aksi')
        catatan = request.form.get('catatan')
        
        if aksi not in ['terima', 'tolak']:
            flash('Aksi tidak valid', 'danger')
            return redirect(url_for('admin_bp.dashboard_admin'))
        
        # Update status pendaftaran
        pendaftaran.status = 'Diterima' if aksi == 'terima' else 'Ditolak'
        pendaftaran.diproses_oleh = current_user.id
        pendaftaran.tanggal_diproses = datetime.utcnow()
        pendaftaran.catatan_admin = catatan
        
        db.session.commit()
        logger.info(f"Application {id} processed successfully: {pendaftaran.status}")
        
        flash(f'Pendaftaran {pendaftaran.nama_lengkap} telah {aksi}', 'success')
        
    except Exception as e:
        logger.error(f"Error processing application {id}: {str(e)}")
        db.session.rollback()
        flash('Terjadi kesalahan saat memproses pendaftaran', 'danger')
    
    return redirect(url_for('admin_bp.dashboard_admin'))

@admin_bp.route('/detail/<int:id>')
@login_required
@admin_required
def detail_pendaftar(id):
    logger.info(f"Viewing details for application {id}")
    
    try:
        pendaftaran = Pendaftaran.query.get_or_404(id)
        return render_template('admin/detail.html',
                             pendaftaran=pendaftaran,
                             title="Detail Pendaftar")
    except Exception as e:
        logger.error(f"Error viewing application {id}: {str(e)}")
        flash('Data pendaftaran tidak ditemukan.', 'danger')
        return redirect(url_for('admin_bp.dashboard_admin'))

@admin_bp.route('/daftar-diterima')  # Changed URL pattern
@login_required
@admin_required
def daftar_diterima():
    logger.info(f"Admin {current_user.username} viewing accepted applications")
    
    try:
        diterima = Pendaftaran.query.filter_by(status='Diterima')\
            .order_by(Pendaftaran.tanggal_diproses.desc()).all()
        
        # Add now variable for template
        now = datetime.utcnow()
        
        return render_template('admin/diterima.html',
                             diterima=diterima,
                             title="Daftar Siswa Diterima",
                             now=now,
                             timedelta=timedelta)
    except Exception as e:
        logger.error(f"Error loading accepted applications: {str(e)}")
        flash('Terjadi kesalahan saat memuat data.', 'danger')
        return redirect(url_for('admin_bp.dashboard_admin'))

@admin_bp.route('/ditolak')
@login_required
@admin_required
def daftar_ditolak():
    logger.info(f"Admin {current_user.username} viewing rejected applications")
    
    try:
        ditolak = Pendaftaran.query.filter_by(status='Ditolak')\
            .order_by(Pendaftaran.tanggal_diproses.desc()).all()
        return render_template('admin/ditolak.html',
                             ditolak=ditolak,
                             title="Daftar Siswa Ditolak")
    except Exception as e:
        logger.error(f"Error loading rejected applications: {str(e)}")
        flash('Terjadi kesalahan saat memuat data.', 'danger')
        return redirect(url_for('admin_bp.dashboard_admin'))