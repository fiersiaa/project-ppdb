from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

def create_admin():
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print('Admin user already exists!')
            return
        
        try:
            # Create admin user with sha256 hashing
            admin = User(
                username='admin',
                password=generate_password_hash('22', method='sha256'),
                is_admin=True
            )
            
            # Add to database
            db.session.add(admin)
            db.session.commit()
            
            print('Admin user created successfully!')
            print('Username: admin')
            print('Password: 22')
            
        except Exception as e:
            print(f'Error creating admin: {str(e)}')
            db.session.rollback()

if __name__ == '__main__':
    create_admin()