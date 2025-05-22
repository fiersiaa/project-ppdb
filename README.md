# PPDB Online System

Sistem Penerimaan Peserta Didik Baru (PPDB) Online adalah aplikasi berbasis web untuk mengelola proses pendaftaran siswa baru.

## Features

- Multi-user system (Admin & Pendaftar)
- Form pendaftaran online
- Upload dokumen dan foto
- Manajemen pembayaran
- Laporan dan statistik
- Export data ke Excel

## Screenshots

### User Interface
| Description | Screenshot |
|-------------|------------|
| Login Page | ![Login](foto%20projek/login.png) |
| Register | ![Register](foto%20projek/register.png) |
| Informasi PPDB | ![Informasi PPDB](foto%20projek/informasi%20ppdb.png) |
| Langkah Pendaftaran | ![Langkah Pendaftaran](foto%20projek/langkah%20langkah%20pendaftaran.png) |

### Pendaftaran Process
| Description | Screenshot |
|-------------|------------|
| Form Pendaftaran | ![Pendaftaran](foto%20projek/pendaftaran.png) |
| Detail Pendaftaran | ![Detail Pendaftaran](foto%20projek/detail%20pendaftaran.png) |
| Upload Pembayaran | ![Pembayaran](foto%20projek/pembayaran.png) |
| Dashboard User | ![Dashboard User](foto%20projek/dashboard%20user.png) |

### Admin Panel
| Description | Screenshot |
|-------------|------------|
| Dashboard Admin | ![Dashboard Admin](foto%20projek/dashboard%20admin.png) |
| Daftar Siswa | ![Daftar Siswa](foto%20projek/daftar%20siswa.png) |
| Detail Siswa | ![Detail Siswa](foto%20projek/detail%20siswa.png) |
| Konfirmasi Siswa | ![Konfirmasi Siswa](foto%20projek/konfirmasi%20siswa.png) |
| Catatan Admin | ![Catatan Admin](foto%20projek/catatan%20admin.png) |
| Laporan PPDB | ![Laporan PPDB](foto%20projek/laporan%20ppdb.png) |

## Tech Stack

- Python 3.9+
- Flask
- SQLite
- Bootstrap 5
- Chart.js

## Installation

1. Clone repository:
```bash
git clone https://github.com/yourusername/ppdb-online.git
cd ppdb-online
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Setup database:
```bash
flask db upgrade
```

4. Create admin user:
```bash
python create_admin.py
```

5. Run application:
```bash
python run.py
```

## Project Structure

```
ppdb-online/
├── app/
│   ├── static/
│   │   └── uploads/
│   ├── templates/
│   ├── routes/
│   └── models.py
├── migrations/
├── config.py
├── requirements.txt
└── run.py
```

## Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

MIT License - see LICENSE file for details