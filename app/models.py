from flask_login import UserMixin
from datetime import datetime
from . import db

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    # One-to-many relationship with Pendaftaran
    pendaftaran = db.relationship('Pendaftaran', backref='pendaftar', lazy=True,
                                foreign_keys='Pendaftaran.user_id')

class Pendaftaran(db.Model):
    __tablename__ = 'pendaftaran'
    id = db.Column(db.Integer, primary_key=True)
    nama_lengkap = db.Column(db.String(150), nullable=False)
    tempat_lahir = db.Column(db.String(100), nullable=False)
    tanggal_lahir = db.Column(db.Date, nullable=False)
    jenis_kelamin = db.Column(db.String(20), nullable=False)
    alamat = db.Column(db.Text, nullable=False)
    nomor_hp = db.Column(db.String(15), nullable=False)
    asal_sekolah = db.Column(db.String(150), nullable=False)
    nilai_un = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    tanggal_daftar = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key to User (pendaftar)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Foreign key to User (admin)
    diproses_oleh = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    tanggal_diproses = db.Column(db.DateTime, nullable=True)
    catatan_admin = db.Column(db.Text, nullable=True)