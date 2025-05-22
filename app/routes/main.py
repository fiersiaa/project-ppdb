from flask import Blueprint, redirect, url_for, render_template, flash, request, current_app
from datetime import datetime, timedelta
from ..models import Pendaftaran
from .. import db
from flask_login import login_required, current_user
import logging
import os
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

main_bp = Blueprint('main_bp', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
UPLOAD_FOLDER = 'app/static/uploads/documents'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route("/")
def home():
    try:
        # If user is admin, redirect to admin dashboard
        if current_user.is_authenticated and current_user.is_admin:
            return redirect(url_for('admin_bp.dashboard_admin'))

        # For regular authenticated users
        pendaftaran = None
        if current_user.is_authenticated:
            pendaftaran = Pendaftaran.query.filter_by(user_id=current_user.id).first()
            if pendaftaran:
                if pendaftaran.status == 'Diterima':
                    flash(f'Selamat! Pendaftaran Anda telah DITERIMA! {pendaftaran.catatan_admin if pendaftaran.catatan_admin else ""}', 'success')
                elif pendaftaran.status == 'Ditolak':
                    flash(f'Mohon maaf, pendaftaran Anda belum dapat kami terima. {pendaftaran.catatan_admin if pendaftaran.catatan_admin else ""}', 'danger')
                elif pendaftaran.status == 'Pending':
                    flash('Pendaftaran Anda sedang dalam proses review.', 'info')
    
        return render_template("index.html", 
                            title="Halaman Utama PPDB",
                            pendaftaran=pendaftaran)

    except Exception as e:
        logger.error(f"Error in home route: {str(e)}")
        flash('Terjadi kesalahan sistem', 'danger')
        return render_template("index.html", 
                            title="Halaman Utama PPDB",
                            pendaftaran=None)

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
                # Create upload directory if doesn't exist
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)

                # Handle pas foto upload
                pas_foto = request.files['pas_foto']
                if pas_foto and allowed_file(pas_foto.filename):
                    pas_foto_filename = secure_filename(f"foto_{current_user.id}_{pas_foto.filename}")
                    pas_foto.save(os.path.join(UPLOAD_FOLDER, pas_foto_filename))
                else:
                    flash('Pas foto harus diupload dengan format PNG atau JPG', 'danger')
                    return redirect(request.url)

                # Handle ijazah upload
                ijazah = request.files['ijazah']
                if ijazah and allowed_file(ijazah.filename):
                    ijazah_filename = secure_filename(f"ijazah_{current_user.id}_{ijazah.filename}")
                    ijazah.save(os.path.join(UPLOAD_FOLDER, ijazah_filename))
                else:
                    flash('Ijazah harus diupload dengan format PNG atau JPG', 'danger')
                    return redirect(request.url)

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
                    status='Pending',
                    pas_foto=pas_foto_filename,
                    ijazah=ijazah_filename,
                    tanggal_upload_dokumen=datetime.utcnow()
                )

                db.session.add(pendaftaran)
                db.session.commit()
                
                logger.info(f"Registration successful for user: {current_user.username}")
                flash('Pendaftaran berhasil dikirim!', 'success')
                return redirect(url_for('main_bp.home'))

            except Exception as e:
                db.session.rollback()
                logger.error(f"Registration error: {str(e)}")
                flash('Terjadi kesalahan saat mendaftar. Silakan coba lagi.', 'danger')
                return redirect(request.url)

    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        flash('Terjadi kesalahan sistem. Silakan coba lagi nanti.', 'danger')

    return render_template('daftar.html', 
                         title="Formulir Pendaftaran PPDB",
                         now=datetime.now())

@main_bp.route("/detail_pendaftaran")
@login_required
def detail_pendaftaran():
    pendaftaran = Pendaftaran.query.filter_by(user_id=current_user.id).first()
    if not pendaftaran:
        flash('Anda belum melakukan pendaftaran', 'warning')
        return redirect(url_for('main_bp.daftar'))
    
    # Calculate payment deadline for accepted students
    if pendaftaran.status == 'Diterima':
        payment_deadline = pendaftaran.tanggal_diproses + timedelta(days=3)
        if datetime.now() > payment_deadline:
            flash('Batas waktu pembayaran telah berakhir!', 'danger')
        else:
            remaining = payment_deadline - datetime.now()
            flash(f'Sisa waktu pembayaran: {remaining.days} hari {remaining.seconds//3600} jam', 'warning')
    
    return render_template('detail_pendaftaran.html', 
                         title="Detail Pendaftaran",
                         pendaftaran=pendaftaran,
                         timedelta=timedelta)  # Pass timedelta to template

@main_bp.route("/upload-pembayaran", methods=['GET', 'POST'])
@login_required
def upload_pembayaran():
    pendaftaran = Pendaftaran.query.filter_by(user_id=current_user.id).first()
    
    if not pendaftaran or pendaftaran.status != 'Diterima':
        flash('Anda tidak memiliki akses ke halaman ini', 'danger')
        return redirect(url_for('main_bp.home'))
    
    if request.method == 'POST':
        if 'bukti_pembayaran' not in request.files:
            flash('Tidak ada file yang dipilih', 'danger')
            return redirect(request.url)
            
        file = request.files['bukti_pembayaran']
        
        if file.filename == '':
            flash('Tidak ada file yang dipilih', 'danger')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            try:
                # Create upload directory if it doesn't exist
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                
                # Generate unique filename
                filename = secure_filename(f"{pendaftaran.id}_{file.filename}")
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                
                # Save file
                file.save(filepath)
                
                # Update database with payment info
                pendaftaran.bukti_pembayaran = filename
                pendaftaran.tanggal_upload_pembayaran = datetime.now()
                pendaftaran.status_pembayaran = 'Sudah Bayar'
                db.session.commit()
                
                flash('Bukti pembayaran berhasil diupload!', 'success')
                return redirect(url_for('main_bp.detail_pendaftaran'))
                
            except Exception as e:
                logger.error(f"Upload error: {str(e)}")
                flash('Terjadi kesalahan saat upload file', 'danger')
                return redirect(request.url)
        else:
            flash('Format file tidak diizinkan. Gunakan PNG, JPG, JPEG, atau PDF', 'danger')
            return redirect(request.url)
            
    return render_template('upload_pembayaran.html', 
                         title="Upload Bukti Pembayaran",
                         pendaftaran=pendaftaran)