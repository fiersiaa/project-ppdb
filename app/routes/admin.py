from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, send_from_directory, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from ..models import Pendaftaran, User
from .. import db
import logging
import pandas as pd
from io import BytesIO
import os

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

@admin_bp.route('/konfirmasi-pembayaran/<int:id>')
@login_required
@admin_required
def konfirmasi_pembayaran(id):
    try:
        pendaftaran = Pendaftaran.query.get_or_404(id)
        pendaftaran.konfirmasi_admin = True
        db.session.commit()
        
        flash(f'Pembayaran untuk {pendaftaran.nama_lengkap} telah dikonfirmasi', 'success')
        return redirect(url_for('admin_bp.daftar_diterima'))
    except Exception as e:
        logger.error(f"Payment confirmation error: {str(e)}")
        flash('Terjadi kesalahan saat konfirmasi pembayaran', 'danger')
        return redirect(url_for('admin_bp.daftar_diterima'))

@admin_bp.route('/laporan')
@login_required
@admin_required
def laporan():
    try:
        # Get basic statistics
        total_pendaftar = Pendaftaran.query.count()
        total_diterima = Pendaftaran.query.filter_by(status='Diterima').count()
        total_ditolak = Pendaftaran.query.filter_by(status='Ditolak').count()
        total_pending = Pendaftaran.query.filter_by(status='Pending').count()
        
        # Get payment statistics
        total_sudah_bayar = Pendaftaran.query.filter(
            Pendaftaran.status == 'Diterima',
            Pendaftaran.bukti_pembayaran.isnot(None)
        ).count()
        
        # Get age distribution
        now = datetime.utcnow()
        age_distribution = db.session.query(
            db.func.strftime('%Y', now) - db.func.strftime('%Y', Pendaftaran.tanggal_lahir),
            db.func.count(Pendaftaran.id)
        ).group_by(
            db.func.strftime('%Y', now) - db.func.strftime('%Y', Pendaftaran.tanggal_lahir)
        ).all()
        
        # Get gender distribution
        gender_distribution = db.session.query(
            Pendaftaran.jenis_kelamin,
            db.func.count(Pendaftaran.id)
        ).group_by(Pendaftaran.jenis_kelamin).all()
        
        # Get average UN score
        avg_nilai_un = db.session.query(
            db.func.avg(Pendaftaran.nilai_un)
        ).scalar()
        
        # Get registration trends
        registrations_per_day = db.session.query(
            db.func.date(Pendaftaran.tanggal_daftar),
            db.func.count(Pendaftaran.id)
        ).group_by(
            db.func.date(Pendaftaran.tanggal_daftar)
        ).order_by(
            db.func.date(Pendaftaran.tanggal_daftar)
        ).all()
        
        return render_template(
            'admin/laporan.html',
            title="Laporan PPDB",
            total_pendaftar=total_pendaftar,
            total_diterima=total_diterima,
            total_ditolak=total_ditolak,
            total_pending=total_pending,
            total_sudah_bayar=total_sudah_bayar,
            age_distribution=age_distribution,
            gender_distribution=gender_distribution,
            avg_nilai_un=avg_nilai_un,
            registrations_per_day=registrations_per_day
        )
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        flash('Terjadi kesalahan saat memuat laporan.', 'danger')
        return redirect(url_for('admin_bp.dashboard_admin'))

@admin_bp.route('/export-laporan')
@login_required
@admin_required
def export_laporan():
    try:
        # Get all registrations
        pendaftaran = Pendaftaran.query.all()
        
        # Create DataFrame
        data = []
        for p in pendaftaran:
            data.append({
                'Nama Lengkap': p.nama_lengkap,
                'Jenis Kelamin': p.jenis_kelamin,
                'Tanggal Lahir': p.tanggal_lahir.strftime('%d-%m-%Y'),
                'Asal Sekolah': p.asal_sekolah,
                'Nilai UN': p.nilai_un,
                'Status': p.status,
                'Tanggal Daftar': p.tanggal_daftar.strftime('%d-%m-%Y %H:%M'),
                'Status Pembayaran': 'Sudah Bayar' if p.bukti_pembayaran else 'Belum Bayar',
                'Tanggal Diproses': p.tanggal_diproses.strftime('%d-%m-%Y %H:%M') if p.tanggal_diproses else '-'
            })
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Write main data
            df.to_excel(writer, sheet_name='Data Pendaftar', index=False)
            
            # Write summary sheet
            summary_data = {
                'Metrik': [
                    'Total Pendaftar',
                    'Diterima',
                    'Ditolak',
                    'Pending',
                    'Sudah Bayar',
                    'Rata-rata Nilai UN'
                ],
                'Jumlah': [
                    len(pendaftaran),
                    sum(1 for p in pendaftaran if p.status == 'Diterima'),
                    sum(1 for p in pendaftaran if p.status == 'Ditolak'),
                    sum(1 for p in pendaftaran if p.status == 'Pending'),
                    sum(1 for p in pendaftaran if p.bukti_pembayaran),
                    sum(p.nilai_un for p in pendaftaran) / len(pendaftaran) if pendaftaran else 0
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Ringkasan', index=False)
            
            # Get workbook and worksheet objects
            workbook = writer.book
            
            # Add some formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#0d6efd',
                'font_color': 'white',
                'border': 1
            })
            
            # Format the header row of each sheet
            for worksheet in writer.sheets.values():
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(0, len(df.columns)-1, 15)  # Set column width
        
        # Prepare the file for download
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'Laporan_PPDB_{timestamp}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting report: {str(e)}")
        flash('Terjadi kesalahan saat mengexport laporan.', 'danger')
        return redirect(url_for('admin_bp.laporan'))

@admin_bp.route('/uploads/payments/<filename>')
@login_required
def payment_proof(filename):
    try:
        uploads_dir = os.path.join(current_app.root_path, 'static/uploads/payments')
        return send_from_directory(uploads_dir, filename)
    except Exception as e:
        logger.error(f"Error displaying payment proof: {str(e)}")
        flash('Terjadi kesalahan saat menampilkan bukti pembayaran.', 'danger')
        return redirect(url_for('admin_bp.daftar_diterima'))