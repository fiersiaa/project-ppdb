from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from ..models import Pendaftaran, User
from .. import db

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/dashboard_admin')
@login_required
def dashboard_admin():
    if not current_user.is_admin:
        flash('Anda tidak memiliki akses ke halaman admin.', 'danger')
        return redirect(url_for('main_bp.index'))
    
    # Ambil data pendaftaran berdasarkan status
    pending = Pendaftaran.query.filter_by(status='Pending').all()
    diterima = Pendaftaran.query.filter_by(status='Diterima').all()
    ditolak = Pendaftaran.query.filter_by(status='Ditolak').all()
    
    return render_template('admin/dashboard_admin.html',
                         pending=pending,
                         diterima=diterima,
                         ditolak=ditolak,
                         title="Admin Dashboard")

@admin_bp.route('/proses_pendaftaran/<int:id>', methods=['POST'])
@login_required
def proses_pendaftaran(id):
    if not current_user.is_admin:
        flash('Anda tidak memiliki akses.', 'danger')
        return redirect(url_for('main_bp.index'))
    
    pendaftaran = Pendaftaran.query.get_or_404(id)
    aksi = request.form.get('aksi')
    catatan = request.form.get('catatan')
    
    if aksi == 'terima':
        pendaftaran.status = 'Diterima'
        pesan = f'Pendaftaran {pendaftaran.nama_lengkap} telah DITERIMA'
    elif aksi == 'tolak':
        pendaftaran.status = 'Ditolak'
        pesan = f'Pendaftaran {pendaftaran.nama_lengkap} telah DITOLAK'
    else:
        flash('Aksi tidak valid', 'danger')
        return redirect(url_for('admin_bp.dashboard_admin'))
    
    # Update data pendaftaran
    pendaftaran.diproses_oleh = current_user.id
    pendaftaran.tanggal_diproses = datetime.utcnow()
    pendaftaran.catatan_admin = catatan
    
    try:
        db.session.commit()
        flash(f'{pesan}. Catatan: {catatan}', 'success')
    except:
        db.session.rollback()
        flash('Terjadi kesalahan saat memproses pendaftaran', 'danger')
    
    return redirect(url_for('admin_bp.dashboard_admin'))

@admin_bp.route('/detail/<int:id>')
@login_required
def detail(id):
    if not current_user.is_admin:
        flash('Anda tidak memiliki akses.', 'danger')
        return redirect(url_for('main_bp.index'))
    
    pendaftaran = Pendaftaran.query.get_or_404(id)
    return render_template('admin/detail.html', 
                         pendaftaran=pendaftaran,
                         title="Detail Pendaftar")

@admin_bp.route('/diterima')
@login_required
def diterima():
    if not current_user.is_admin:
        flash('Anda tidak memiliki akses.', 'danger')
        return redirect(url_for('main_bp.index'))
    
    diterima = Pendaftaran.query.filter_by(status='Diterima')\
        .order_by(Pendaftaran.tanggal_diproses.desc()).all()
    return render_template('admin/diterima.html',
                         diterima=diterima,
                         title="Daftar Siswa Diterima")

@admin_bp.route('/ditolak')
@login_required
def ditolak():
    if not current_user.is_admin:
        flash('Anda tidak memiliki akses.', 'danger')
        return redirect(url_for('main_bp.index'))
    
    ditolak = Pendaftaran.query.filter_by(status='Ditolak')\
        .order_by(Pendaftaran.tanggal_diproses.desc()).all()
    return render_template('admin/ditolak.html',
                         ditolak=ditolak,
                         title="Daftar Siswa Ditolak")

@admin_bp.route('/batalkan_status/<int:id>', methods=['POST'])
@login_required
def batalkan_status(id):
    if not current_user.is_admin:
        flash('Anda tidak memiliki akses.', 'danger')
        return redirect(url_for('main_bp.index'))
    
    pendaftaran = Pendaftaran.query.get_or_404(id)
    pendaftaran.status = 'Pending'
    pendaftaran.diproses_oleh = None
    pendaftaran.tanggal_diproses = None
    pendaftaran.catatan_admin = None
    
    try:
        db.session.commit()
        flash(f'Status pendaftaran {pendaftaran.nama_lengkap} telah dibatalkan', 'success')
    except:
        db.session.rollback()
        flash('Terjadi kesalahan saat membatalkan status', 'danger')
    
    return redirect(url_for('admin_bp.dashboard_admin'))