from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import Pendaftaran, User
from .. import db

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        flash('Anda tidak memiliki akses ke halaman admin.', 'danger')
        return redirect(url_for('main_bp.index'))
    
    # Ambil data pendaftaran berdasarkan status
    pending = Pendaftaran.query.filter_by(status='Pending').all()
    diterima = Pendaftaran.query.filter_by(status='Diterima').all()
    ditolak = Pendaftaran.query.filter_by(status='Ditolak').all()
    
    return render_template('admin/dashboard.html',
                         pending=pending,
                         diterima=diterima,
                         ditolak=ditolak,
                         title="Admin Dashboard")

@admin_bp.route('/update_status/<int:id>', methods=['POST'])
@login_required
def update_status(id):
    if not current_user.is_admin:
        flash('Anda tidak memiliki akses.', 'danger')
        return redirect(url_for('main_bp.index'))
    
    pendaftaran = Pendaftaran.query.get_or_404(id)
    status = request.form.get('status')
    
    if status in ['Diterima', 'Ditolak']:
        pendaftaran.status = status
        db.session.commit()
        flash(f'Status pendaftaran {pendaftaran.nama_lengkap} diubah menjadi {status}', 'success')
    
    return redirect(url_for('admin_bp.dashboard'))

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
    
    diterima = Pendaftaran.query.filter_by(status='Diterima').all()
    return render_template('admin/diterima.html',
                         diterima=diterima,
                         title="Daftar Siswa Diterima")

@admin_bp.route('/ditolak')
@login_required
def ditolak():
    if not current_user.is_admin:
        flash('Anda tidak memiliki akses.', 'danger')
        return redirect(url_for('main_bp.index'))
    
    ditolak = Pendaftaran.query.filter_by(status='Ditolak').all()
    return render_template('admin/ditolak.html',
                         ditolak=ditolak,
                         title="Daftar Siswa Ditolak")