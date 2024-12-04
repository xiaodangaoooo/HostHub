from flask_login import UserMixin
from app.utils.db import get_db

class User(UserMixin):
    def __init__(self, id, username, first_name, last_name, email, role_type, password_hash=None):
        self.id = id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.role_type = role_type
        self.password_hash = password_hash

    @staticmethod
    def get_by_email(email):
        db = get_db()
        print(f"Checking for user with email: {email}")
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute('SELECT * FROM User WHERE email = %s', (email,))
            user_data = cursor.fetchone()
            
            if user_data:
                return User(
                    id=user_data['user_id'],
                    username=user_data['username'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    email=user_data['email'],
                    role_type=user_data['role_type'],
                    password_hash=user_data['password_hash']
                )
            return None
        finally:
            cursor.close()

    @staticmethod
    def get_by_id(user_id):
        db = get_db()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute('SELECT * FROM User WHERE user_id = %s', (user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                return User(
                    id=user_data['user_id'],
                    username=user_data['username'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    email=user_data['email'],
                    role_type=user_data['role_type'],
                    password_hash=user_data['password_hash']
                )
            return None
        finally:
            cursor.close()

    @staticmethod
    def create_user(username, first_name, last_name, email, password_hash, role_type):
        db = get_db()
        cursor = db.cursor()
        try:
            sql = '''
                INSERT INTO User 
                (username, first_name, last_name, email, password_hash, role_type) 
                VALUES (%s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(sql, (
                username,
                first_name,
                last_name,
                email,
                password_hash,
                role_type
            ))
            db.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error creating user: {e}")
            db.rollback()
            raise
        finally:
            cursor.close()

    def get_id(self):
        """Required method for Flask-Login"""
        return str(self.id)