from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

def create_admin():
    app = create_app()
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            try:
                db.session.delete(admin)
                db.session.commit()
                print('Admin lama berhasil dihapus')
            except Exception as e:
                print(f'Error saat menghapus admin: {str(e)}')
                db.session.rollback()
                return
        
        try:
            # Create new admin user
            admin = User(
                username='admin',
                password=generate_password_hash('admin123', method='scrypt'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print('Admin baru berhasil dibuat!')
            print('Username: admin')
            print('Password: admin123')
        except Exception as e:
            print(f'Error: {str(e)}')
            db.session.rollback()

if __name__ == '__main__':
    create_admin()