from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from ..models import Pendaftaran, User
from .. import db
import logging
import pandas as pd
import io
from openpyxl.styles import PatternFill

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

@admin_bp.route('/statistik')
@login_required
@admin_required
def statistik():
    try:
        # Get all registrations
        pendaftaran = Pendaftaran.query.all()
        
        # Basic statistics
        total_pendaftar = len(pendaftaran)
        total_diterima = sum(1 for p in pendaftaran if p.status == 'Diterima')
        total_ditolak = sum(1 for p in pendaftaran if p.status == 'Ditolak')
        total_pending = sum(1 for p in pendaftaran if p.status == 'Pending')
        
        # Gender statistics
        laki_laki = sum(1 for p in pendaftaran if p.jenis_kelamin == 'Laki-laki')
        perempuan = sum(1 for p in pendaftaran if p.jenis_kelamin == 'Perempuan')
        
        # Payment statistics for accepted students
        diterima_list = [p for p in pendaftaran if p.status == 'Diterima']
        sudah_bayar = sum(1 for p in diterima_list if p.status_pembayaran == 'Sudah Bayar')
        belum_bayar = sum(1 for p in diterima_list if p.status_pembayaran == 'Belum Bayar')
        
        # Calculate average UN score
        nilai_list = [p.nilai_un for p in pendaftaran]
        avg_nilai = sum(nilai_list) / len(nilai_list) if nilai_list else 0
        
        # Get school distribution
        sekolah_count = {}
        for p in pendaftaran:
            sekolah_count[p.asal_sekolah] = sekolah_count.get(p.asal_sekolah, 0) + 1
        
        # Sort schools by count
        sekolah_data = sorted(sekolah_count.items(), key=lambda x: x[1], reverse=True)
        
        return render_template('admin/statistik.html',
                             total_pendaftar=total_pendaftar,
                             total_diterima=total_diterima,
                             total_ditolak=total_ditolak,
                             total_pending=total_pending,
                             laki_laki=laki_laki,
                             perempuan=perempuan,
                             sudah_bayar=sudah_bayar,
                             belum_bayar=belum_bayar,
                             avg_nilai=round(avg_nilai, 2),
                             sekolah_data=sekolah_data[:5],  # Top 5 schools
                             now=datetime.now())
                             
    except Exception as e:
        logger.error(f"Error generating statistics: {str(e)}")
        flash('Terjadi kesalahan saat memuat statistik', 'danger')
        return redirect(url_for('admin_bp.dashboard_admin'))

@admin_bp.route('/export-excel/<report_type>')
@login_required
@admin_required
def export_excel(report_type):
    try:
        if report_type == 'semua':
            data = Pendaftaran.query.all()
            filename = 'data_semua_pendaftar.xlsx'
        elif report_type == 'diterima':
            data = Pendaftaran.query.filter_by(status='Diterima').all()
            filename = 'data_pendaftar_diterima.xlsx'
        elif report_type == 'ditolak':
            data = Pendaftaran.query.filter_by(status='Ditolak').all()
            filename = 'data_pendaftar_ditolak.xlsx'
        else:
            flash('Tipe laporan tidak valid', 'danger')
            return redirect(url_for('admin_bp.statistik'))

        # Convert to DataFrame
        df_data = []
        for p in data:
            df_data.append({
                'ID': p.id,
                'Nama Lengkap': p.nama_lengkap,
                'Jenis Kelamin': p.jenis_kelamin,
                'Tempat Lahir': p.tempat_lahir,
                'Tanggal Lahir': p.tanggal_lahir.strftime('%d-%m-%Y'),
                'Alamat': p.alamat,
                'No. HP': p.nomor_hp,
                'Asal Sekolah': p.asal_sekolah,
                'Nilai UN': p.nilai_un,
                'Status': p.status,
                'Tanggal Daftar': p.tanggal_daftar.strftime('%d-%m-%Y %H:%M'),
                'Status Pembayaran': p.status_pembayaran,
                'Tanggal Upload Pembayaran': p.tanggal_upload_pembayaran.strftime('%d-%m-%Y %H:%M') if p.tanggal_upload_pembayaran else '-',
                'Catatan Admin': p.catatan_admin or '-'
            })

        df = pd.DataFrame(df_data)

        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Data Pendaftar', index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Data Pendaftar']
            
            # Add formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#0D6EFD',
                'font_color': 'white',
                'border': 1
            })
            
            # Format headers
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 15)  # Set column width
            
            # Adjust specific column widths
            worksheet.set_column('B:B', 25)  # Nama Lengkap
            worksheet.set_column('E:E', 20)  # Alamat
            worksheet.set_column('H:H', 25)  # Asal Sekolah
            worksheet.set_column('K:K', 20)  # Tanggal Daftar
            worksheet.set_column('M:M', 25)  # Tanggal Upload Pembayaran
            worksheet.set_column('N:N', 30)  # Catatan Admin

        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")
        flash('Terjadi kesalahan saat mengekspor data', 'danger')
        return redirect(url_for('admin_bp.statistik'))