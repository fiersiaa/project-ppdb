from flask import Blueprint, redirect, url_for, render_template, flash, request
from datetime import datetime
from ..models import Pendaftaran
from .. import db
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

@main_bp.route("/daftar", methods=['GET', 'POST'])
@login_required
def daftar():
    if request.method == 'POST':
        try:
            pendaftaran = Pendaftaran(
                nama_lengkap=request.form.get('nama_lengkap'),
                tempat_lahir=request.form.get('tempat_lahir'),
                tanggal_lahir=datetime.strptime(request.form.get('tanggal_lahir'), '%Y-%m-%d'),
                jenis_kelamin=request.form.get('jenis_kelamin'),
                alamat=request.form.get('alamat'),
                nomor_hp=request.form.get('nomor_hp'),
                asal_sekolah=request.form.get('asal_sekolah'),
                nilai_un=float(request.form.get('nilai_un')),
                user_id=current_user.id
            )
            db.session.add(pendaftaran)
            db.session.commit()
            flash('Pendaftaran berhasil dikirim!', 'success')
            return redirect(url_for('main_bp.index'))
        except Exception as e:
            flash('Terjadi kesalahan. Silakan coba lagi.', 'danger')
            return redirect(url_for('main_bp.daftar'))
    
    return render_template('daftar.html', title="Formulir Pendaftaran PPDB")

@main_bp.route("/admin")
@login_required
def admin():
    if not current_user.is_admin:
        flash('Anda tidak memiliki akses ke halaman admin.', 'danger')
        return redirect(url_for('main_bp.index'))
    
    pendaftaran = Pendaftaran.query.all()
    return render_template("admin.html", title="Admin Dashboard", pendaftaran=pendaftaran)

@main_bp.route("/admin/update_status/<int:id>", methods=['POST'])
@login_required
def update_status(id):
    if not current_user.is_admin:
        return redirect(url_for('main_bp.index'))
    
    pendaftaran = Pendaftaran.query.get_or_404(id)
    status = request.form.get('status')
    if status in ['Diterima', 'Ditolak', 'Pending']:
        pendaftaran.status = status
        db.session.commit()
        flash('Status pendaftaran berhasil diperbarui.', 'success')
    return redirect(url_for('main_bp.admin'))