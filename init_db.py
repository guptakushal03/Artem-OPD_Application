from app import app, db
from models import Patient, Appointment, Consultation

def init_database():
    with app.app_context():
        print("Testing database connection...")
        
        try:
            db.session.execute(db.text('SELECT 1'))
            print("Database connection successful!\n")
            
            print("Dropping existing tables...")
            db.drop_all()
            
            print("Creating tables...")
            db.create_all()
            
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tables created: {', '.join(tables)}\n")
            
            print("Adding sample data...")
            patient1 = Patient(
                name="John Doe",
                gender="Male",
                age=35,
                phone="1234567890",
                status="Active"
            )
            patient2 = Patient(
                name="Jane Smith",
                gender="Female",
                age=28,
                phone="0987654321",
                status="Active"
            )
            
            db.session.add_all([patient1, patient2])
            db.session.commit()
            
            print(f"Added {Patient.query.count()} sample patients\n")
            print("="*50)
            print("Database initialized successfully!")
            print("="*50)
            
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("\nPlease check:")
            print("1. MySQL is running")
            print("2. Database 'opd_db' exists")
            print("3. Credentials in config.py are correct")
            return False
        
        return True

if __name__ == '__main__':
    init_database()