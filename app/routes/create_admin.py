import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

def create_admin():
    app = create_app()
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print('Admin user already exists')
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
            print('Admin created successfully!')
            print('Username: admin')
            print('Password: admin123')
        except Exception as e:
            print(f'Error creating admin: {str(e)}')
            db.session.rollback()

if __name__ == '__main__':
    create_admin()